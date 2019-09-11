import copy
import os
import re
import uuid  # pylint: disable=unused-import # noqa: F401
from typing import (
    Any,
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from six import iteritems, string_types, text_type
from six.moves import StringIO, urllib
from typing_extensions import Text  # pylint: disable=unused-import

from ruamel import yaml
from ruamel.yaml.comments import CommentedMap
from schema_salad.ref_resolver import Fetcher
from schema_salad.sourceline import SourceLine, add_lc_filename, bullets, indent
from schema_salad.exceptions import SchemaSaladException, ValidationException

# move to a regular typing import when Python 3.3-3.6 is no longer supported

_vocab = {}  # type: Dict[Text, Text]
_rvocab = {}  # type: Dict[Text, Text]


class Savable(object):
    @classmethod
    def fromDoc(cls, _doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Savable
        pass

    def save(self, top=False, base_url="", relative_uris=True):
        # type: (bool, Text, bool) -> Dict[Text, Text]
        pass


class LoadingOptions(object):
    def __init__(
        self,
        fetcher=None,  # type: Optional[Fetcher]
        namespaces=None,  # type: Optional[Dict[Text, Text]]
        fileuri=None,  # type: Optional[Text]
        copyfrom=None,  # type: Optional[LoadingOptions]
        schemas=None,  # type: Optional[List[Text]]
        original_doc=None,  # type: Optional[Any]
    ):  # type: (...) -> None
        self.idx = {}  # type: Dict[Text, Text]
        self.fileuri = fileuri  # type: Optional[Text]
        self.namespaces = namespaces
        self.schemas = schemas
        self.original_doc = original_doc
        if copyfrom is not None:
            self.idx = copyfrom.idx
            if fetcher is None:
                fetcher = copyfrom.fetcher
            if fileuri is None:
                self.fileuri = copyfrom.fileuri
            if namespaces is None:
                self.namespaces = copyfrom.namespaces
            if namespaces is None:
                schemas = copyfrom.schemas

        if fetcher is None:
            import requests
            from cachecontrol.wrapper import CacheControl
            from cachecontrol.caches import FileCache
            from schema_salad.ref_resolver import DefaultFetcher

            if "HOME" in os.environ:
                session = CacheControl(
                    requests.Session(),
                    cache=FileCache(
                        os.path.join(os.environ["HOME"], ".cache", "salad")
                    ),
                )
            elif "TMPDIR" in os.environ:
                session = CacheControl(
                    requests.Session(),
                    cache=FileCache(
                        os.path.join(os.environ["TMPDIR"], ".cache", "salad")
                    ),
                )
            else:
                session = CacheControl(
                    requests.Session(), cache=FileCache("/tmp", ".cache", "salad")
                )
            self.fetcher = DefaultFetcher({}, session)  # type: Fetcher
        else:
            self.fetcher = fetcher

        self.vocab = _vocab
        self.rvocab = _rvocab

        if namespaces is not None:
            self.vocab = self.vocab.copy()
            self.rvocab = self.rvocab.copy()
            for k, v in iteritems(namespaces):
                self.vocab[k] = v
                self.rvocab[v] = k


def load_field(val, fieldtype, baseuri, loadingOptions):
    # type: (Union[Text, Dict[Text, Text]], _Loader, Text, LoadingOptions) -> Any
    if isinstance(val, MutableMapping):
        if "$import" in val:
            if loadingOptions.fileuri is None:
                raise SchemaSaladException("Cannot load $import without fileuri")
            return _document_load_by_url(
                fieldtype,
                loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$import"]),
                loadingOptions,
            )
        elif "$include" in val:
            if loadingOptions.fileuri is None:
                raise SchemaSaladException("Cannot load $import without fileuri")
            val = loadingOptions.fetcher.fetch_text(
                loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$include"])
            )
    return fieldtype.load(val, baseuri, loadingOptions)


save_type = Union[
    Dict[Text, Text], List[Union[Dict[Text, Text], List[Any], None]], None
]


def save(
    val,  # type: Optional[Union[Savable, MutableSequence[Savable]]]
    top=True,  # type: bool
    base_url="",  # type: Text
    relative_uris=True,  # type: bool
):  # type: (...) -> save_type

    if isinstance(val, Savable):
        return val.save(top=top, base_url=base_url, relative_uris=relative_uris)
    if isinstance(val, MutableSequence):
        return [
            save(v, top=False, base_url=base_url, relative_uris=relative_uris)
            for v in val
        ]
    if isinstance(val, MutableMapping):
        newdict = {}
        for key in val:
            newdict[key] = save(
                val[key], top=False, base_url=base_url, relative_uris=relative_uris
            )
        return newdict
    return val


def expand_url(
    url,  # type: Union[str, Text]
    base_url,  # type: Union[str, Text]
    loadingOptions,  # type: LoadingOptions
    scoped_id=False,  # type: bool
    vocab_term=False,  # type: bool
    scoped_ref=None,  # type: Optional[int]
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
            url = loadingOptions.vocab[prefix] + url[len(prefix) + 1 :]

    split = urllib.parse.urlsplit(url)

    if (
        (bool(split.scheme) and split.scheme in [u"http", u"https", u"file"])
        or url.startswith(u"$(")
        or url.startswith(u"${")
    ):
        pass
    elif scoped_id and not bool(split.fragment):
        splitbase = urllib.parse.urlsplit(base_url)
        frg = u""
        if bool(splitbase.fragment):
            frg = splitbase.fragment + u"/" + split.path
        else:
            frg = split.path
        pt = splitbase.path if splitbase.path != "" else "/"
        url = urllib.parse.urlunsplit(
            (splitbase.scheme, splitbase.netloc, pt, splitbase.query, frg)
        )
    elif scoped_ref is not None and not bool(split.fragment):
        splitbase = urllib.parse.urlsplit(base_url)
        sp = splitbase.fragment.split(u"/")
        n = scoped_ref
        while n > 0 and len(sp) > 0:
            sp.pop()
            n -= 1
        sp.append(url)
        url = urllib.parse.urlunsplit(
            (
                splitbase.scheme,
                splitbase.netloc,
                splitbase.path,
                splitbase.query,
                u"/".join(sp),
            )
        )
    else:
        url = loadingOptions.fetcher.urljoin(base_url, url)

    if vocab_term:
        split = urllib.parse.urlsplit(url)
        if bool(split.scheme):
            if url in loadingOptions.rvocab:
                return loadingOptions.rvocab[url]
        else:
            raise ValidationException("Term '{}' not in vocabulary".format(url))

    return url


class _Loader(object):
    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        pass


class _AnyLoader(_Loader):
    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if doc is not None:
            return doc
        raise ValidationException("Expected non-null")


class _PrimitiveLoader(_Loader):
    def __init__(self, tp):
        # type: (Union[type, Tuple[Type[Text], Type[Text]]]) -> None
        self.tp = tp

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if not isinstance(doc, self.tp):
            raise ValidationException(
                "Expected a {} but got {}".format(
                    self.tp.__class__.__name__, doc.__class__.__name__
                )
            )
        return doc

    def __repr__(self):  # type: () -> str
        return str(self.tp)


class _ArrayLoader(_Loader):
    def __init__(self, items):
        # type: (_Loader) -> None
        self.items = items

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if not isinstance(doc, MutableSequence):
            raise ValidationException("Expected a list")
        r = []  # type: List[Any]
        errors = []
        for i in range(0, len(doc)):
            try:
                lf = load_field(
                    doc[i], _UnionLoader((self, self.items)), baseuri, loadingOptions
                )
                if isinstance(lf, MutableSequence):
                    r.extend(lf)
                else:
                    r.append(lf)
            except ValidationException as e:
                errors.append(SourceLine(doc, i, str).makeError(text_type(e)))
        if errors:
            raise ValidationException("\n".join(errors))
        return r

    def __repr__(self):  # type: () -> str
        return "array<{}>".format(self.items)


class _EnumLoader(_Loader):
    def __init__(self, symbols):
        # type: (Sequence[Text]) -> None
        self.symbols = symbols

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if doc in self.symbols:
            return doc
        else:
            raise ValidationException("Expected one of {}".format(self.symbols))


class _RecordLoader(_Loader):
    def __init__(self, classtype):
        # type: (Type[Savable]) -> None
        self.classtype = classtype

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if not isinstance(doc, MutableMapping):
            raise ValidationException("Expected a dict")
        return self.classtype.fromDoc(doc, baseuri, loadingOptions, docRoot=docRoot)

    def __repr__(self):  # type: () -> str
        return str(self.classtype)


class _UnionLoader(_Loader):
    def __init__(self, alternates):
        # type: (Sequence[_Loader]) -> None
        self.alternates = alternates

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        errors = []
        for t in self.alternates:
            try:
                return t.load(doc, baseuri, loadingOptions, docRoot=docRoot)
            except ValidationException as e:
                errors.append(
                    u"tried {} but\n{}".format(t.__class__.__name__, indent(str(e)))
                )
        raise ValidationException(bullets(errors, u"- "))

    def __repr__(self):  # type: () -> str
        return " | ".join(str(a) for a in self.alternates)


class _URILoader(_Loader):
    def __init__(self, inner, scoped_id, vocab_term, scoped_ref):
        # type: (_Loader, bool, bool, Union[int, None]) -> None
        self.inner = inner
        self.scoped_id = scoped_id
        self.vocab_term = vocab_term
        self.scoped_ref = scoped_ref

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if isinstance(doc, MutableSequence):
            doc = [
                expand_url(
                    i,
                    baseuri,
                    loadingOptions,
                    self.scoped_id,
                    self.vocab_term,
                    self.scoped_ref,
                )
                for i in doc
            ]
        if isinstance(doc, string_types):
            doc = expand_url(
                doc,
                baseuri,
                loadingOptions,
                self.scoped_id,
                self.vocab_term,
                self.scoped_ref,
            )
        return self.inner.load(doc, baseuri, loadingOptions)


class _TypeDSLLoader(_Loader):
    typeDSLregex = re.compile(r"^([^[?]+)(\[\])?(\?)?$")

    def __init__(self, inner, refScope):
        # type: (_Loader, Union[int, None]) -> None
        self.inner = inner
        self.refScope = refScope

    def resolve(self, doc, baseuri, loadingOptions):
        # type: (Any, Text, LoadingOptions) -> Any
        m = self.typeDSLregex.match(doc)
        if m:
            first = expand_url(
                m.group(1), baseuri, loadingOptions, False, True, self.refScope
            )
            second = third = None
            if bool(m.group(2)):
                second = {"type": "array", "items": first}
                # second = CommentedMap((("type", "array"),
                #                       ("items", first)))
                # second.lc.add_kv_line_col("type", lc)
                # second.lc.add_kv_line_col("items", lc)
                # second.lc.filename = filename
            if bool(m.group(3)):
                third = [u"null", second or first]
                # third = CommentedSeq([u"null", second or first])
                # third.lc.add_kv_line_col(0, lc)
                # third.lc.add_kv_line_col(1, lc)
                # third.lc.filename = filename
            doc = third or second or first
        return doc

    def load(self, doc, baseuri, loadingOptions, docRoot=None):
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if isinstance(doc, MutableSequence):
            r = []  # type: List[Any]
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
        # type: (Any, Text, LoadingOptions, Optional[Text]) -> Any
        if isinstance(doc, MutableMapping):
            r = []  # type: List[Any]
            for k in sorted(doc.keys()):
                val = doc[k]
                if isinstance(val, CommentedMap):
                    v = copy.copy(val)
                    v.lc.data = val.lc.data
                    v.lc.filename = val.lc.filename
                    v[self.mapSubject] = k
                    r.append(v)
                elif isinstance(val, MutableMapping):
                    v2 = copy.copy(val)
                    v2[self.mapSubject] = k
                    r.append(v2)
                else:
                    if self.mapPredicate:
                        v3 = {self.mapPredicate: val}
                        v3[self.mapSubject] = k
                        r.append(v3)
                    else:
                        raise ValidationException("No mapPredicate")
            doc = r
        return self.inner.load(doc, baseuri, loadingOptions)


def _document_load(loader, doc, baseuri, loadingOptions):
    # type: (_Loader, Any, Text, LoadingOptions) -> Any
    if isinstance(doc, string_types):
        return _document_load_by_url(
            loader, loadingOptions.fetcher.urljoin(baseuri, doc), loadingOptions
        )

    if isinstance(doc, MutableMapping):
        if "$namespaces" in doc:
            loadingOptions = LoadingOptions(
                copyfrom=loadingOptions, namespaces=doc["$namespaces"]
            )
            doc = {k: v for k, v in doc.items() if k != "$namespaces"}

        if "$schemas" in doc:
            loadingOptions = LoadingOptions(
                copyfrom=loadingOptions, schemas=doc["$schemas"]
            )
            doc = {k: v for k, v in doc.items() if k != "$schemas"}

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
    # type: (_Loader, Text, LoadingOptions) -> Any
    if url in loadingOptions.idx:
        return _document_load(loader, loadingOptions.idx[url], url, loadingOptions)

    text = loadingOptions.fetcher.fetch_text(url)
    if isinstance(text, bytes):
        textIO = StringIO(text.decode("utf-8"))
    else:
        textIO = StringIO(text)
    textIO.name = str(url)
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
        return "file:{}{}".format(urlpath, frag)
    else:
        return "file://{}{}".format(urlpath, frag)


def prefix_url(url, namespaces):  # type: (Text, Dict[Text, Text]) -> Text
    for k, v in namespaces.items():
        if url.startswith(v):
            return k + ":" + url[len(v) :]
    return url


def save_relative_uri(uri, base_url, scoped_id, ref_scope, relative_uris):
    # type: (Text, Text, bool, Optional[int], bool) -> Union[Text, List[Text]]
    if not relative_uris:
        return uri
    if isinstance(uri, MutableSequence):
        return [
            save_relative_uri(u, base_url, scoped_id, ref_scope, relative_uris)
            for u in uri
        ]
    elif isinstance(uri, text_type):
        urisplit = urllib.parse.urlsplit(uri)
        basesplit = urllib.parse.urlsplit(base_url)
        if urisplit.scheme == basesplit.scheme and urisplit.netloc == basesplit.netloc:
            if urisplit.path != basesplit.path:
                p = os.path.relpath(urisplit.path, os.path.dirname(basesplit.path))
                if urisplit.fragment:
                    p = p + "#" + urisplit.fragment
                return p

            basefrag = basesplit.fragment + "/"
            if ref_scope:
                sp = basefrag.split("/")
                i = 0
                while i < ref_scope:
                    sp.pop()
                    i += 1
                basefrag = "/".join(sp)

            if urisplit.fragment.startswith(basefrag):
                return urisplit.fragment[len(basefrag) :]
            else:
                return urisplit.fragment
        return uri
    else:
        return save(uri, top=False, base_url=base_url)
