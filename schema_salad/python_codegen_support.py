import copy
import re
import uuid  # pylint: disable=unused-import
from typing import (Any, Dict, List, MutableMapping, MutableSequence, Sequence,
                    Union)

from ruamel import yaml
from six import iteritems, string_types, text_type
from six.moves import StringIO, urllib
from typing_extensions import Text  # pylint: disable=unused-import
# move to a regular typing import when Python 3.3-3.6 is no longer supported



class ValidationException(Exception):
    pass

class Savable(object):
    pass

class LoadingOptions(object):
    def __init__(self, fetcher=None, namespaces=None, fileuri=None, copyfrom=None, schemas=None):
        if copyfrom is not None:
            self.idx = copyfrom.idx
            if fetcher is None:
                fetcher = copyfrom.fetcher
            if fileuri is None:
                fileuri = copyfrom.fileuri
            if namespaces is None:
                namespaces = copyfrom.namespaces
            if namespaces is None:
                schemas = copyfrom.schemas
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
            elif "TMPDIR" in os.environ:
                session = CacheControl(
                    requests.Session(),
                    cache=FileCache(os.path.join(os.environ["TMPDIR"], ".cache", "salad")))
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
        self.namespaces = namespaces
        self.schemas = schemas

        if namespaces is not None:
            self.vocab = self.vocab.copy()
            self.rvocab = self.rvocab.copy()
            for k,v in iteritems(namespaces):
                self.vocab[k] = v
                self.rvocab[v] = k



def load_field(val, fieldtype, baseuri, loadingOptions):
    if isinstance(val, MutableMapping):
        if "$import" in val:
            return _document_load_by_url(fieldtype, loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$import"]), loadingOptions)
        elif "$include" in val:
            val = loadingOptions.fetcher.fetch_text(loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$include"]))
    return fieldtype.load(val, baseuri, loadingOptions)


def save(val, top=True, base_url="", relative_uris=True):
    if isinstance(val, Savable):
        return val.save(top=top, base_url=base_url, relative_uris=relative_uris)
    if isinstance(val, MutableSequence):
        return [save(v, top=False, base_url=base_url, relative_uris=relative_uris) for v in val]
    return val

def expand_url(url,                 # type: Union[str, Text]
               base_url,            # type: Union[str, Text]
               loadingOptions,      # type: LoadingOptions
               scoped_id=False,     # type: bool
               vocab_term=False,    # type: bool
               scoped_ref=None      # type: int
               ):
    # type: (...) -> Text

    if not isinstance(url, string_types):
        return url

    url = Text(url)

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
    elif scoped_ref is not None and not bool(split.fragment):
        splitbase = urllib.parse.urlsplit(base_url)
        sp = splitbase.fragment.split(u"/")
        n = scoped_ref
        while n > 0 and len(sp) > 0:
            sp.pop()
            n -= 1
        sp.append(url)
        url = urllib.parse.urlunsplit((
            splitbase.scheme, splitbase.netloc, splitbase.path, splitbase.query,
            u"/".join(sp)))
    else:
        url = loadingOptions.fetcher.urljoin(base_url, url)

    if vocab_term:
        split = urllib.parse.urlsplit(url)
        if bool(split.scheme):
            if url in loadingOptions.rvocab:
                return loadingOptions.rvocab[url]
        else:
            raise ValidationException("Term '%s' not in vocabulary" % url)

    return url


class _Loader(object):
    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Union[Text, None]) -> Any
        pass

class _AnyLoader(_Loader):
    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if doc is not None:
            return doc
        raise ValidationException("Expected non-null")

class _PrimitiveLoader(_Loader):
    def __init__(self, tp):
        # type: (Union[type, Sequence[type]]) -> None
        self.tp = tp

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if not isinstance(doc, self.tp):
            raise ValidationException("Expected a %s but got %s" % (self.tp, type(doc)))
        return doc

    def __repr__(self):
        return str(self.tp)

class _ArrayLoader(_Loader):
    def __init__(self, items):
        # type: (_Loader) -> None
        self.items = items

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if not isinstance(doc, MutableSequence):
            raise ValidationException("Expected a list")
        r = []
        errors = []
        for i in range(0, len(doc)):
            try:
                lf = load_field(doc[i], _UnionLoader((self, self.items)), baseuri, loadingOptions)
                if isinstance(lf, MutableSequence):
                    r.extend(lf)
                else:
                    r.append(lf)
            except ValidationException as e:
                errors.append(SourceLine(doc, i, str).makeError(text_type(e)))
        if errors:
            raise ValidationException("\n".join(errors))
        return r

    def __repr__(self):
        return "array<%s>" % self.items

class _EnumLoader(_Loader):
    def __init__(self, symbols):
        # type: (Sequence[Text]) -> None
        self.symbols = symbols

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if doc in self.symbols:
            return doc
        else:
            raise ValidationException("Expected one of %s" % (self.symbols,))


class _RecordLoader(_Loader):
    def __init__(self, classtype):
        # type: (type) -> None
        self.classtype = classtype

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if not isinstance(doc, MutableMapping):
            raise ValidationException("Expected a dict")
        return self.classtype(doc, baseuri, loadingOptions, docRoot=docRoot)

    def __repr__(self):
        return str(self.classtype)


class _UnionLoader(_Loader):
    def __init__(self, alternates):
        # type: (Sequence[_Loader]) -> None
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
        # type: (_Loader, bool, bool, Union[int, None]) -> None
        self.inner = inner
        self.scoped_id = scoped_id
        self.vocab_term = vocab_term
        self.scoped_ref = scoped_ref

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if isinstance(doc, MutableSequence):
            doc = [expand_url(i, baseuri, loadingOptions,
                            self.scoped_id, self.vocab_term, self.scoped_ref) for i in doc]
        if isinstance(doc, string_types):
            doc = expand_url(doc, baseuri, loadingOptions,
                             self.scoped_id, self.vocab_term, self.scoped_ref)
        return self.inner.load(doc, baseuri, loadingOptions)

class _TypeDSLLoader(_Loader):
    typeDSLregex = re.compile(r"^([^[?]+)(\[\])?(\?)?$")

    def __init__(self, inner, refScope):
        # type: (_Loader, Union[int, None]) -> None
        self.inner = inner
        self.refScope = refScope

    def resolve(self, doc, baseuri, loadingOptions):
        m = self.typeDSLregex.match(doc)
        if m:
            first = expand_url(m.group(1), baseuri, loadingOptions, False, True, self.refScope)
            second = third = None
            if bool(m.group(2)):
                second = {"type": "array", "items": first}
                #second = CommentedMap((("type", "array"),
                #                       ("items", first)))
                #second.lc.add_kv_line_col("type", lc)
                #second.lc.add_kv_line_col("items", lc)
                #second.lc.filename = filename
            if bool(m.group(3)):
                third = [u"null", second or first]
                #third = CommentedSeq([u"null", second or first])
                #third.lc.add_kv_line_col(0, lc)
                #third.lc.add_kv_line_col(1, lc)
                #third.lc.filename = filename
            doc = third or second or first
        return doc

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if isinstance(doc, MutableSequence):
            r = []
            for d in doc:
                if isinstance(d, string_types):
                    resolved = self.resolve(d, baseuri, loadingOptions)
                    if isinstance(resolved, MutableSequence):
                        for i in resolved:
                            if i not in r:
                                r.append(i)
                    else:
                        if resolved not in r:
                            r.append(resolved)
                else:
                    r.append(d)
            doc = r
        elif isinstance(doc, string_types):
            doc = self.resolve(doc, baseuri, loadingOptions)

        return self.inner.load(doc, baseuri, loadingOptions)


class _IdMapLoader(_Loader):
    def __init__(self, inner, mapSubject, mapPredicate):
        # type: (_Loader, Text, Union[Text, None]) -> None
        self.inner = inner
        self.mapSubject = mapSubject
        self.mapPredicate = mapPredicate

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        if isinstance(doc, MutableMapping):
            r = []
            for k in sorted(doc.keys()):
                val = doc[k]
                if isinstance(val, MutableMapping):
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
    if isinstance(doc, string_types):
        return _document_load_by_url(loader, loadingOptions.fetcher.urljoin(baseuri, doc), loadingOptions)

    if isinstance(doc, MutableMapping):
        if "$namespaces" in doc:
            loadingOptions = LoadingOptions(copyfrom=loadingOptions, namespaces=doc["$namespaces"])
            doc = {k: v for k,v in doc.items() if k != "$namespaces"}

        if "$schemas" in doc:
            loadingOptions = LoadingOptions(copyfrom=loadingOptions, schemas=doc["$schemas"])
            doc = {k: v for k,v in doc.items() if k != "$schemas"}

        if "$base" in doc:
            baseuri = doc["$base"]

        if "$graph" in doc:
            return loader.load(doc["$graph"], baseuri, loadingOptions)
        else:
            return loader.load(doc, baseuri, loadingOptions, docRoot=baseuri)

    if isinstance(doc, MutableSequence):
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
    result = yaml.round_trip_load(textIO, preserve_quotes=True)
    add_lc_filename(result, url)

    loadingOptions.idx[url] = result

    loadingOptions = LoadingOptions(copyfrom=loadingOptions, fileuri=url)

    return _document_load(loader, result, url, loadingOptions)

def file_uri(path, split_frag=False):  # type: (str, bool) -> str
    if path.startswith("file://"):
        return path
    if split_frag:
        pathsp = path.split("#", 2)
        frag = "#" + urllib.parse.quote(str(pathsp[1])) if len(pathsp) == 2 else ""
        urlpath = urllib.request.pathname2url(str(pathsp[0]))
    else:
        urlpath = urllib.request.pathname2url(path)
        frag = ""
    if urlpath.startswith("//"):
        return "file:%s%s" % (urlpath, frag)
    else:
        return "file://%s%s" % (urlpath, frag)

def prefix_url(url, namespaces):
    for k,v in namespaces.items():
        if url.startswith(v):
            return k+":"+url[len(v):]
    return url

def save_relative_uri(uri, base_url, scoped_id, ref_scope, relative_uris):
    if not relative_uris:
        return uri
    if isinstance(uri, MutableSequence):
        return [save_relative_uri(u, base_url, scoped_id, ref_scope, relative_uris) for u in uri]
    elif isinstance(uri, text_type):
        urisplit = urllib.parse.urlsplit(uri)
        basesplit = urllib.parse.urlsplit(base_url)
        if urisplit.scheme == basesplit.scheme and urisplit.netloc == basesplit.netloc:
            if urisplit.path != basesplit.path:
                p = os.path.relpath(urisplit.path, os.path.dirname(basesplit.path))
                if urisplit.fragment:
                    p = p + "#" + urisplit.fragment
                return p

            basefrag = basesplit.fragment+"/"
            if ref_scope:
                sp = basefrag.split("/")
                i = 0
                while i < ref_scope:
                    sp.pop()
                    i += 1
                basefrag = "/".join(sp)

            if urisplit.fragment.startswith(basefrag):
                return urisplit.fragment[len(basefrag):]
            else:
                return urisplit.fragment
        return uri
    else:
        return save(uri, top=False, base_url=base_url)
