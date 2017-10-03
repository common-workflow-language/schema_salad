from types import NoneType
from six.moves import urllib
import ruamel.yaml as yaml
from StringIO import StringIO
import copy

class ValidationException(Exception):
    pass

class Savable(object):
    pass

class LoadingOptions(object):
    def __init__(self, fetcher=None, namespaces=None, fileuri=None, copyfrom=None):
        if copyfrom is not None:
            self.idx = copyfrom.idx
            if fetcher is None:
                fetcher = copyfrom.fetcher
            if fileuri is None:
                fileuri = copyfrom.fileuri
        else:
            self.idx = {}

        if fetcher is None:
            import os
            import requests
            from cachecontrol.wrapper import CacheControl
            from cachecontrol.caches import FileCache
            from schema_salad.ref_resolver import DefaultFetcher
            if "HOME" in os.environ:
                session = CacheControl(
                    requests.Session(),
                    cache=FileCache(os.path.join(os.environ["HOME"], ".cache", "salad")))
            elif "TMP" in os.environ:
                session = CacheControl(
                    requests.Session(),
                    cache=FileCache(os.path.join(os.environ["TMP"], ".cache", "salad")))
            else:
                session = CacheControl(
                    requests.Session(),
                    cache=FileCache("/tmp", ".cache", "salad"))
            self.fetcher = DefaultFetcher({}, session)
        else:
            self.fetcher = fetcher

        self.fileuri = fileuri

        self.vocab = _vocab
        self.rvocab = _rvocab

        if namespaces is not None:
            self.vocab = self.vocab.copy()
            self.rvocab = self.rvocab.copy()
            for k,v in namespaces.iteritems():
                self.vocab[k] = v
                self.rvocab[v] = k

def load_field(val, fieldtype, baseuri, loadingOptions):
    if isinstance(val, dict):
        if "$import" in val:
            return _document_load_by_url(fieldtype, loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$import"]), loadingOptions)
        elif "$include" in val:
            val = loadingOptions.fetcher.fetch_text(loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$include"]))
    return fieldtype.load(val, baseuri, loadingOptions)


def save(val):
   if isinstance(val, Savable):
       return val.save()
   if isinstance(val, list):
       return [save(v) for v in val]
   return val

def expand_url(url,                 # type: Text
               base_url,            # type: Text
               loadingOptions,
               scoped_id=False,     # type: bool
               vocab_term=False,    # type: bool
               scoped_ref=None      # type: int
               ):
    # type: (...) -> Text
    if url in (u"@id", u"@type"):
        return url

    if vocab_term and url in loadingOptions.vocab:
        return url

    if bool(loadingOptions.vocab) and u":" in url:
        prefix = url.split(u":")[0]
        if prefix in loadingOptions.vocab:
            url = loadingOptions.vocab[prefix] + url[len(prefix) + 1:]

    split = urllib.parse.urlsplit(url)

    if ((bool(split.scheme) and split.scheme in [u'http', u'https', u'file']) or url.startswith(u"$(")
        or url.startswith(u"${")):
        pass
    elif scoped_id and not bool(split.fragment):
        splitbase = urllib.parse.urlsplit(base_url)
        frg = u""
        if bool(splitbase.fragment):
            frg = splitbase.fragment + u"/" + split.path
        else:
            frg = split.path
        pt = splitbase.path if splitbase.path != '' else "/"
        url = urllib.parse.urlunsplit(
            (splitbase.scheme, splitbase.netloc, pt, splitbase.query, frg))
    elif scoped_ref is not None and not split.fragment:
        pass
    else:
        url = loadingOptions.fetcher.urljoin(base_url, url)

    if vocab_term:
        if bool(split.scheme):
            if url in loadingOptions.rvocab:
                return loadingOptions.rvocab[url]
        else:
            raise ValidationException("Term '%s' not in vocabulary" % url)
    return url


class _Loader(object):
    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        pass

class _PrimitiveLoader(_Loader):
    def __init__(self, tp):
        self.tp = tp

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if not isinstance(doc, self.tp):
            raise ValidationException("Expected a %s but got %s" % (self.tp, type(doc)))
        return doc

    def __repr__(self):
        return str(self.tp)

class _ArrayLoader(_Loader):
    def __init__(self, items):
        self.items = items

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if not isinstance(doc, list):
            raise ValidationException("Expected a list")
        r = []
        errors = []
        for i in xrange(0, len(doc)):
            try:
                lf = load_field(doc[i], _UnionLoader((self, self.items)), baseuri, loadingOptions)
                if isinstance(lf, list):
                    r.extend(lf)
                else:
                    r.append(lf)
            except ValidationException as e:
                errors.append(SourceLine(doc, i, str).makeError(six.text_type(e)))
        if errors:
            raise ValidationException("\n".join(errors))
        return r

    def __repr__(self):
        return "array<%s>" % self.items

class _EnumLoader(_Loader):
    def __init__(self, symbols):
        self.symbols = symbols

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if doc in self.symbols:
            return doc
        else:
            raise ValidationException("Expected one of %s" % (self.symbols,))


class _RecordLoader(_Loader):
    def __init__(self, classtype):
        self.classtype = classtype

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if not isinstance(doc, dict):
            raise ValidationException("Expected a dict")
        return self.classtype(doc, baseuri, loadingOptions, docRoot=docRoot)

    def __repr__(self):
        return str(self.classtype)


class _UnionLoader(_Loader):
    def __init__(self, alternates):
        self.alternates = alternates

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        errors = []
        for t in self.alternates:
            try:
                return t.load(doc, baseuri, loadingOptions, docRoot=docRoot)
            except ValidationException as e:
                errors.append("tried %s but\n%s" % (t, indent(str(e))))
        raise ValidationException(bullets(errors, "- "))

    def __repr__(self):
        return " | ".join(str(a) for a in self.alternates)

class _URILoader(_Loader):
    def __init__(self, inner, scoped_id, vocab_term, scoped_ref):
        self.inner = inner
        self.scoped_id = scoped_id
        self.vocab_term = vocab_term
        self.scoped_ref = scoped_ref

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if isinstance(doc, list):
            doc = [expand_url(i, baseuri, loadingOptions,
                            self.scoped_id, self.vocab_term, self.scoped_ref) for i in doc]
        if isinstance(doc, basestring):
            doc = expand_url(doc, baseuri, loadingOptions,
                             self.scoped_id, self.vocab_term, self.scoped_ref)
        return self.inner.load(doc, baseuri, loadingOptions)


class _TypeDSLLoader(_Loader):
    def __init__(self, inner):
        self.inner = inner

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        return self.inner.load(doc, baseuri, loadingOptions)


class _IdMapLoader(_Loader):
    def __init__(self, inner, mapSubject, mapPredicate):
        self.inner = inner
        self.mapSubject = mapSubject
        self.mapPredicate = mapPredicate

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if isinstance(doc, dict):
            r = []
            for k in sorted(doc.keys()):
                val = doc[k]
                if isinstance(val, dict):
                    v = copy.copy(val)
                    if hasattr(val, 'lc'):
                        v.lc.data = val.lc.data
                        v.lc.filename = val.lc.filename
                else:
                    if self.mapPredicate:
                        v = {self.mapPredicate: val}
                    else:
                        raise ValidationException("No mapPredicate")
                v[self.mapSubject] = k
                r.append(v)
            doc = r
        return self.inner.load(doc, baseuri, loadingOptions)


def _document_load(loader, doc, baseuri, loadingOptions):
    if isinstance(doc, basestring):
        return _document_load_by_url(loader, doc, loadingOptions)

    if isinstance(doc, dict):
        if "$namespaces" in doc:
            loadingOptions = LoadingOptions(copyfrom=loadingOptions, namespaces=doc["$namespaces"])

        if "$base" in doc:
            baseuri = doc["$base"]

        if "$graph" in doc:
            return loader.load(doc["$graph"], baseuri, loadingOptions)
        else:
            return loader.load(doc, baseuri, loadingOptions, docRoot=baseuri)

    if isinstance(doc, list):
        return loader.load(doc, baseuri, loadingOptions)

    raise ValidationException()


def _document_load_by_url(loader, url, loadingOptions):
    if url in loadingOptions.idx:
        return _document_load(loader, loadingOptions.idx[url], url, loadingOptions)

    text = loadingOptions.fetcher.fetch_text(url)
    if isinstance(text, bytes):
        textIO = StringIO(text.decode('utf-8'))
    else:
        textIO = StringIO(text)
    textIO.name = url    # type: ignore
    result = yaml.round_trip_load(textIO)
    add_lc_filename(result, url)

    loadingOptions.idx[url] = result

    loadingOptions = LoadingOptions(copyfrom=loadingOptions, fileuri=url)

    return _document_load(loader, result, url, loadingOptions)
