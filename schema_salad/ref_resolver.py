from __future__ import absolute_import

import copy
import logging
import os
import re
import sys
import xml.sax
from io import open
from typing import Callable  # pylint: disable=unused-import
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import requests
from cachecontrol.caches import FileCache
from cachecontrol.wrapper import CacheControl
from future.utils import raise_from
from rdflib.graph import Graph
from rdflib.namespace import OWL, RDF, RDFS
from rdflib.plugins.parsers.notation3 import BadSyntax
from six import StringIO, iteritems, string_types
from six.moves import range, urllib
from typing_extensions import Text  # pylint: disable=unused-import

from ruamel import yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq, LineCol

from .exceptions import ValidationException, SchemaSaladException
from .sourceline import SourceLine, add_lc_filename, relname
from .utils import aslist, onWindows

# move to a regular typing import when Python 3.3-3.6 is no longer supported


_logger = logging.getLogger("salad")
ContextType = Dict[Text, Union[Dict[Text, Any], Text, Iterable[Text]]]
DocumentType = TypeVar("DocumentType", CommentedSeq, CommentedMap)
DocumentOrStrType = TypeVar("DocumentOrStrType", CommentedSeq, CommentedMap, Text)

_re_drive = re.compile(r"/([a-zA-Z]):")


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
    return "file://{}{}".format(urlpath, frag)


def uri_file_path(url):  # type: (str) -> str
    split = urllib.parse.urlsplit(url)
    if split.scheme == "file":
        return urllib.request.url2pathname(str(split.path)) + (
            "#" + urllib.parse.unquote(str(split.fragment))
            if bool(split.fragment)
            else ""
        )
    raise ValidationException("Not a file URI: {}".format(url))


def to_validation_exception(
    e,
):  # type: (yaml.error.MarkedYAMLError) -> ValidationException
    fname_regex = re.compile(r"^file://" + re.escape(os.getcwd()) + "/")

    exc = ValidationException(e.problem)
    mark = e.problem_mark
    exc.file = re.sub(fname_regex, "", mark.name)
    exc.start = (mark.line + 1, mark.column + 1)
    exc.end = None

    if e.context:
        parent = ValidationException(e.context)
        mark = e.context_mark
        parent.file = re.sub(fname_regex, "", mark.name)
        parent.start = (mark.line + 1, mark.column + 1)
        parent.end = None
        parent.children = [exc]
        return parent
    else:
        return exc


class NormDict(CommentedMap):
    """A Dict where all keys are normalized using the provided function."""

    def __init__(self, normalize=Text):  # type: (Callable[[Text], Text]) -> None
        super(NormDict, self).__init__()
        self.normalize = normalize

    def __getitem__(self, key):  # type: (Any) -> Any
        return super(NormDict, self).__getitem__(self.normalize(key))

    def __setitem__(self, key, value):  # type: (Any, Any) -> Any
        return super(NormDict, self).__setitem__(self.normalize(key), value)

    def __delitem__(self, key):  # type: (Any) -> Any
        return super(NormDict, self).__delitem__(self.normalize(key))

    def __contains__(self, key):  # type: (Any) -> Any
        return super(NormDict, self).__contains__(self.normalize(key))


def merge_properties(a, b):  # type: (List[Any], List[Any]) -> Dict[Any, Any]
    c = {}
    for i in a:
        if i not in b:
            c[i] = a[i]
    for i in b:
        if i not in a:
            c[i] = b[i]
    for i in a:
        if i in b:
            c[i] = aslist(a[i]) + aslist(b[i])  # type: ignore

    return c


def SubLoader(loader):  # type: (Loader) -> Loader
    return Loader(
        loader.ctx,
        schemagraph=loader.graph,
        foreign_properties=loader.foreign_properties,
        idx=loader.idx,
        cache=loader.cache,
        fetcher_constructor=loader.fetcher_constructor,
        skip_schemas=loader.skip_schemas,
        url_fields=loader.url_fields,
        allow_attachments=loader.allow_attachments,
    )


class Fetcher(object):
    def fetch_text(self, url):  # type: (Text) -> Text
        raise NotImplementedError()

    def check_exists(self, url):  # type: (Text) -> bool
        raise NotImplementedError()

    def urljoin(self, base_url, url):  # type: (Text, Text) -> Text
        raise NotImplementedError()

    schemes = [u"file", u"http", u"https", u"mailto"]

    def supported_schemes(self):  # type: () -> List[Text]
        return self.schemes


class DefaultFetcher(Fetcher):
    def __init__(
        self,
        cache,  # type: Dict[Text, Union[Text, bool]]
        session,  # type: Optional[requests.sessions.Session]
    ):  # type: (...) -> None
        self.cache = cache
        self.session = session

    def fetch_text(self, url):
        # type: (Text) -> Text
        if url in self.cache and self.cache[url] is not True:
            # treat "True" as a placeholder that indicates something exists but
            # not necessarily what its contents is.
            return cast(Text, self.cache[url])

        split = urllib.parse.urlsplit(url)
        scheme, path = split.scheme, split.path

        if scheme in [u"http", u"https"] and self.session is not None:
            try:
                resp = self.session.get(url)
                resp.raise_for_status()
            except Exception as e:
                raise_from(
                    ValidationException("Error fetching {}: {}".format(url, e)), e
                )
            return resp.text
        if scheme == "file":
            try:
                # On Windows, url.path will be /drive:/path ; on Unix systems,
                # /path. As we want drive:/path instead of /drive:/path on Windows,
                # remove the leading /.
                if os.path.isabs(
                    path[1:]
                ):  # checking if pathis valid after removing front / or not
                    path = path[1:]
                with open(
                    urllib.request.url2pathname(str(path)), encoding="utf-8"
                ) as fp:
                    return Text(fp.read())

            except (OSError, IOError) as err:
                if err.filename == path:
                    raise_from(ValidationException(Text(err)), err)
                else:
                    raise_from(
                        ValidationException("Error reading {}: {}".format(url, err)),
                        err,
                    )
        raise ValidationException("Unsupported scheme in url: {}".format(url))

    def check_exists(self, url):  # type: (Text) -> bool
        if url in self.cache:
            return True

        split = urllib.parse.urlsplit(url)
        scheme, path = split.scheme, split.path

        if scheme in [u"http", u"https"] and self.session is not None:
            try:
                resp = self.session.head(url)
                resp.raise_for_status()
            except Exception:
                return False
            self.cache[url] = True
            return True
        if scheme == "file":
            return os.path.exists(urllib.request.url2pathname(str(path)))
        if scheme == "mailto":
            return True
        raise ValidationException("Unsupported scheme in url: {}".format(url))

    def urljoin(self, base_url, url):  # type: (Text, Text) -> Text
        if url.startswith("_:"):
            return url

        basesplit = urllib.parse.urlsplit(base_url)
        split = urllib.parse.urlsplit(url)
        if basesplit.scheme and basesplit.scheme != "file" and split.scheme == "file":
            raise ValidationException(
                "Not resolving potential remote exploit {} from base {}".format(
                    url, base_url
                )
            )

        if sys.platform == "win32":
            if base_url == url:
                return url
            basesplit = urllib.parse.urlsplit(base_url)
            # note that below might split
            # "C:" with "C" as URI scheme
            split = urllib.parse.urlsplit(url)

            has_drive = split.scheme and len(split.scheme) == 1

            if basesplit.scheme == "file":
                # Special handling of relative file references on Windows
                # as urllib seems to not be quite up to the job

                # netloc MIGHT appear in equivalents of UNC Strings
                # \\server1.example.com\path as
                # file:///server1.example.com/path
                # https://tools.ietf.org/html/rfc8089#appendix-E.3.2
                # (TODO: test this)
                netloc = split.netloc or basesplit.netloc

                # Check if url is a local path like "C:/Users/fred"
                # or actually an absolute URI like http://example.com/fred
                if has_drive:
                    # Assume split.scheme is actually a drive, e.g. "C:"
                    # so we'll recombine into a path
                    path_with_drive = urllib.parse.urlunsplit(
                        (split.scheme, "", split.path, "", "")
                    )
                    # Compose new file:/// URI with path_with_drive
                    # .. carrying over any #fragment (?query just in case..)
                    return urllib.parse.urlunsplit(
                        ("file", netloc, path_with_drive, split.query, split.fragment)
                    )
                if (
                    not split.scheme
                    and not netloc
                    and split.path
                    and split.path.startswith("/")
                ):
                    # Relative - but does it have a drive?
                    base_drive = _re_drive.match(basesplit.path)
                    drive = _re_drive.match(split.path)
                    if base_drive and not drive:
                        # Keep drive letter from base_url
                        # https://tools.ietf.org/html/rfc8089#appendix-E.2.1
                        # e.g. urljoin("file:///D:/bar/a.txt", "/foo/b.txt")
                        #          == file:///D:/foo/b.txt
                        path_with_drive = "/{}:{}".format(
                            base_drive.group(1), split.path
                        )
                        return urllib.parse.urlunsplit(
                            (
                                "file",
                                netloc,
                                path_with_drive,
                                split.query,
                                split.fragment,
                            )
                        )

                # else: fall-through to resolve as relative URI
            elif has_drive:
                # Base is http://something but url is C:/something - which urllib
                # would wrongly resolve as an absolute path that could later be used
                # to access local files
                raise ValidationException(
                    "Not resolving potential remote exploit {} from base {}".format(
                        url, base_url
                    )
                )

        return urllib.parse.urljoin(base_url, url)


idx_type = Dict[Text, Union[CommentedMap, CommentedSeq, Text, None]]
fetcher_sig = Callable[
    [Dict[Text, Union[Text, bool]], requests.sessions.Session], Fetcher
]
attachements_sig = Callable[[Union[CommentedMap, CommentedSeq]], bool]


class Loader(object):
    def __init__(
        self,
        ctx,  # type: ContextType
        schemagraph=None,  # type: Optional[Graph]
        foreign_properties=None,  # type: Optional[Set[Text]]
        idx=None,  # type: Optional[idx_type]
        cache=None,  # type: Optional[Dict[Text, Any]]
        session=None,  # type: Optional[requests.sessions.Session]
        fetcher_constructor=None,  # type: Optional[fetcher_sig]
        skip_schemas=None,  # type: Optional[bool]
        url_fields=None,  # type: Optional[Set[Text]]
        allow_attachments=None,  # type: Optional[attachements_sig]
    ):
        # type: (...) -> None

        if idx is not None:
            self.idx = idx
        else:
            self.idx = NormDict(lambda url: urllib.parse.urlsplit(url).geturl())

        self.ctx = {}  # type: ContextType
        if schemagraph is not None:
            self.graph = schemagraph
        else:
            self.graph = Graph()

        if foreign_properties is not None:
            self.foreign_properties = set(foreign_properties)
        else:
            self.foreign_properties = set()

        if cache is not None:
            self.cache = cache
        else:
            self.cache = {}

        if skip_schemas is not None:
            self.skip_schemas = skip_schemas
        else:
            self.skip_schemas = False

        if session is None:
            if "HOME" in os.environ:
                self.session = CacheControl(
                    requests.Session(),
                    cache=FileCache(
                        os.path.join(os.environ["HOME"], ".cache", "salad")
                    ),
                )
            elif "TMP" in os.environ:
                self.session = CacheControl(
                    requests.Session(),
                    cache=FileCache(os.path.join(os.environ["TMP"], ".cache", "salad")),
                )
            else:
                self.session = CacheControl(
                    requests.Session(),
                    cache=FileCache(os.path.join("/tmp", ".cache", "salad")),
                )
        else:
            self.session = session

        if fetcher_constructor is not None:
            self.fetcher_constructor = fetcher_constructor
        else:
            self.fetcher_constructor = DefaultFetcher
        self.fetcher = self.fetcher_constructor(self.cache, self.session)
        self.fetch_text = self.fetcher.fetch_text
        self.check_exists = self.fetcher.check_exists

        if url_fields is None:
            self.url_fields = set()  # type: Set[Text]
        else:
            self.url_fields = set(url_fields)

        self.scoped_ref_fields = {}  # type: Dict[Text, int]
        self.vocab_fields = set()  # type: Set[Text]
        self.identifiers = []  # type: List[Text]
        self.identity_links = set()  # type: Set[Text]
        self.standalone = None  # type: Optional[Set[Text]]
        self.nolinkcheck = set()  # type: Set[Text]
        self.vocab = {}  # type: Dict[Text, Text]
        self.rvocab = {}  # type: Dict[Text, Text]
        self.idmap = {}  # type: Dict[Text, Any]
        self.mapPredicate = {}  # type: Dict[Text, Text]
        self.type_dsl_fields = set()  # type: Set[Text]
        self.subscopes = {}  # type: Dict[Text, Text]
        self.secondaryFile_dsl_fields = set()  # type: Set[Text]
        self.allow_attachments = allow_attachments

        self.add_context(ctx)

    def expand_url(
        self,
        url,  # type: Text
        base_url,  # type: Text
        scoped_id=False,  # type: bool
        vocab_term=False,  # type: bool
        scoped_ref=None,  # type: Optional[int]
    ):
        # type: (...) -> Text
        if url in (u"@id", u"@type") or url is None:
            return url

        if vocab_term and url in self.vocab:
            return url

        if url.startswith("_:"):
            return url

        if bool(self.vocab) and u":" in url:
            prefix = url.split(u":")[0]
            if prefix in self.vocab:
                url = self.vocab[prefix] + url[len(prefix) + 1 :]
            elif prefix not in self.fetcher.supported_schemes():
                _logger.warning(
                    "URI prefix '%s' of '%s' not recognized, are you missing a "
                    "$namespaces section?",
                    prefix,
                    url,
                )

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
        elif scoped_ref is not None and not split.fragment:
            pass
        else:
            url = self.fetcher.urljoin(base_url, url)

        if vocab_term and url in self.rvocab:
            return self.rvocab[url]
        else:
            return url

    def _add_properties(self, s):  # type: (Text) -> None
        for _, _, rng in self.graph.triples((s, RDFS.range, None)):
            literal = (
                Text(rng).startswith(u"http://www.w3.org/2001/XMLSchema#")
                and not Text(rng) == u"http://www.w3.org/2001/XMLSchema#anyURI"
            ) or Text(rng) == u"http://www.w3.org/2000/01/rdf-schema#Literal"
            if not literal:
                self.url_fields.add(Text(s))
        self.foreign_properties.add(Text(s))

    def add_namespaces(self, ns):  # type: (Dict[Text, Text]) -> None
        self.vocab.update(ns)

    def add_schemas(self, ns, base_url):
        # type: (Union[List[Text], Text], Text) -> None
        if self.skip_schemas:
            return
        for sch in aslist(ns):
            try:
                fetchurl = self.fetcher.urljoin(base_url, sch)
                if fetchurl not in self.cache or self.cache[fetchurl] is True:
                    _logger.debug("Getting external schema %s", fetchurl)
                    content = self.fetch_text(fetchurl)
                    self.cache[fetchurl] = Graph()
                    for fmt in ["xml", "turtle", "rdfa"]:
                        try:
                            self.cache[fetchurl].parse(
                                data=content, format=fmt, publicID=str(fetchurl)
                            )
                            self.graph += self.cache[fetchurl]
                            break
                        except xml.sax.SAXParseException:
                            pass
                        except TypeError:
                            pass
                        except BadSyntax:
                            pass
            except Exception as e:
                _logger.warning(
                    "Could not load extension schema %s: %s", fetchurl, Text(e)
                )

        for s, _, _ in self.graph.triples((None, RDF.type, RDF.Property)):
            self._add_properties(s)
        for s, _, o in self.graph.triples((None, RDFS.subPropertyOf, None)):
            self._add_properties(s)
            self._add_properties(o)
        for s, _, _ in self.graph.triples((None, RDFS.range, None)):
            self._add_properties(s)
        for s, _, _ in self.graph.triples((None, RDF.type, OWL.ObjectProperty)):
            self._add_properties(s)

        for s, _, _ in self.graph.triples((None, None, None)):
            self.idx[Text(s)] = None

    def add_context(self, newcontext, baseuri=""):
        # type: (ContextType, Text) -> None
        if bool(self.vocab):
            raise ValidationException("Refreshing context that already has stuff in it")

        self.url_fields = set(("$schemas",))
        self.scoped_ref_fields = {}
        self.vocab_fields = set()
        self.identifiers = []
        self.identity_links = set()
        self.standalone = set()
        self.nolinkcheck = set()
        self.idmap = {}
        self.mapPredicate = {}
        self.vocab = {}
        self.rvocab = {}
        self.type_dsl_fields = set()
        self.secondaryFile_dsl_fields = set()
        self.subscopes = {}

        self.ctx.update(_copy_dict_without_key(newcontext, u"@context"))

        _logger.debug("ctx is %s", self.ctx)

        for key, value in self.ctx.items():
            if value == u"@id":
                self.identifiers.append(key)
                self.identity_links.add(key)
            elif isinstance(value, MutableMapping):
                if value.get(u"@type") == u"@id":
                    self.url_fields.add(key)
                    if u"refScope" in value:
                        self.scoped_ref_fields[key] = value[u"refScope"]
                    if value.get(u"identity", False):
                        self.identity_links.add(key)

                if value.get(u"@type") == u"@vocab":
                    self.url_fields.add(key)
                    self.vocab_fields.add(key)
                    if u"refScope" in value:
                        self.scoped_ref_fields[key] = value[u"refScope"]
                    if value.get(u"typeDSL"):
                        self.type_dsl_fields.add(key)

                if value.get(u"secondaryFilesDSL"):
                    self.secondaryFile_dsl_fields.add(key)

                if value.get(u"noLinkCheck"):
                    self.nolinkcheck.add(key)

                if value.get(u"mapSubject"):
                    self.idmap[key] = value[u"mapSubject"]

                if value.get(u"mapPredicate"):
                    self.mapPredicate[key] = value[u"mapPredicate"]

                if value.get(u"@id"):
                    self.vocab[key] = value[u"@id"]

                if value.get(u"subscope"):
                    self.subscopes[key] = value[u"subscope"]

            elif isinstance(value, string_types):
                self.vocab[key] = value

        for k, v in self.vocab.items():
            self.rvocab[self.expand_url(v, u"", scoped_id=False)] = k

        self.identifiers.sort()

        _logger.debug("identifiers is %s", self.identifiers)
        _logger.debug("identity_links is %s", self.identity_links)
        _logger.debug("url_fields is %s", self.url_fields)
        _logger.debug("vocab_fields is %s", self.vocab_fields)
        _logger.debug("vocab is %s", self.vocab)

    resolved_ref_type = Tuple[
        Optional[Union[CommentedMap, CommentedSeq, Text]], CommentedMap
    ]

    def resolve_ref(
        self,
        ref,  # type: Union[CommentedMap, CommentedSeq, Text]
        base_url=None,  # type: Optional[Text]
        checklinks=True,  # type: bool
        strict_foreign_properties=False,  # type: bool
    ):
        # type: (...) -> Loader.resolved_ref_type

        lref = ref  # type: Union[CommentedMap, CommentedSeq, Text, None]
        obj = None  # type: Optional[CommentedMap]
        resolved_obj = None  # type: Optional[Union[CommentedMap, CommentedSeq, Text]]
        inc = False
        mixin = None  # type: Optional[MutableMapping[Text, Any]]

        if not base_url:
            base_url = file_uri(os.getcwd()) + "/"

        sl = SourceLine(obj, None)
        # If `ref` is a dict, look for special directives.
        if isinstance(lref, CommentedMap):
            obj = lref
            if "$import" in obj:
                sl = SourceLine(obj, "$import")
                if len(obj) == 1:
                    lref = obj[u"$import"]
                    obj = None
                else:
                    raise ValidationException(
                        u"'$import' must be the only field in {}".format(obj), sl
                    )
            elif "$include" in obj:
                sl = SourceLine(obj, "$include")
                if len(obj) == 1:
                    lref = obj[u"$include"]
                    inc = True
                    obj = None
                else:
                    raise ValidationException(
                        u"'$include' must be the only field in {}".format(obj), sl
                    )
            elif "$mixin" in obj:
                sl = SourceLine(obj, "$mixin")
                lref = obj[u"$mixin"]
                mixin = obj
                obj = None
            else:
                lref = None
                for identifier in self.identifiers:
                    if identifier in obj:
                        lref = obj[identifier]
                        break
                if not lref:
                    raise ValidationException(
                        u"Object `{}` does not have identifier field in {}".format(
                            obj, self.identifiers
                        ),
                        sl,
                    )

        if not isinstance(lref, string_types):
            raise ValidationException(
                u"Expected CommentedMap or string, got {}: `{}`".format(
                    type(lref), lref
                )
            )

        if isinstance(lref, string_types) and os.sep == "\\":
            # Convert Windows path separator in ref
            lref = lref.replace("\\", "/")

        url = self.expand_url(lref, base_url, scoped_id=(obj is not None))
        # Has this reference been loaded already?
        if url in self.idx and (not mixin):
            resolved_obj = self.idx[url]
            if isinstance(resolved_obj, MutableMapping):
                metadata = self.idx.get(urllib.parse.urldefrag(url)[0], CommentedMap())
                if isinstance(metadata, MutableMapping):
                    if u"$graph" in resolved_obj:
                        metadata = _copy_dict_without_key(resolved_obj, u"$graph")
                        return resolved_obj[u"$graph"], metadata
                    else:
                        return resolved_obj, metadata
                else:
                    raise ValidationException(
                        u"Expected CommentedMap, got {}: `{}`".format(
                            type(metadata), metadata
                        )
                    )
            elif isinstance(resolved_obj, MutableSequence):
                metadata = self.idx.get(urllib.parse.urldefrag(url)[0], CommentedMap())
                if isinstance(metadata, MutableMapping):
                    return resolved_obj, metadata
                else:
                    return resolved_obj, CommentedMap()
            elif isinstance(resolved_obj, string_types):
                return resolved_obj, CommentedMap()
            else:
                raise ValidationException(
                    u"Expected MutableMapping or MutableSequence, got {}: `{}`".format(
                        type(resolved_obj), resolved_obj
                    )
                )

        # "$include" directive means load raw text
        if inc:
            return self.fetch_text(url), CommentedMap()

        doc = None
        if isinstance(obj, MutableMapping):
            for identifier in self.identifiers:
                obj[identifier] = url
            doc_url = url
        else:
            # Load structured document
            doc_url, frg = urllib.parse.urldefrag(url)
            if doc_url in self.idx and (not mixin):
                # If the base document is in the index, it was already loaded,
                # so if we didn't find the reference earlier then it must not
                # exist.
                raise ValidationException(
                    u"Reference `#{}` not found in file `{}`.".format(frg, doc_url), sl
                )
            doc = self.fetch(doc_url, inject_ids=(not mixin))

        # Recursively expand urls and resolve directives
        if bool(mixin):
            doc = copy.deepcopy(doc)
            if doc is not None and mixin is not None:
                doc.update(mixin)
                del doc["$mixin"]
            resolved_obj, metadata = self.resolve_all(
                doc,
                base_url,
                file_base=doc_url,
                checklinks=checklinks,
                strict_foreign_properties=strict_foreign_properties,
            )
        else:
            if doc:
                resolve_target = doc
            else:
                resolve_target = obj
            resolved_obj, metadata = self.resolve_all(
                resolve_target,
                doc_url,
                checklinks=checklinks,
                strict_foreign_properties=strict_foreign_properties,
            )

        # Requested reference should be in the index now, otherwise it's a bad
        # reference
        if not bool(mixin):
            if url in self.idx:
                resolved_obj = self.idx[url]
            else:
                raise ValidationException(
                    "Reference `{}` is not in the index. Index contains: {}".format(
                        url, ", ".join(self.idx)
                    )
                )

        if isinstance(resolved_obj, CommentedMap):
            if u"$graph" in resolved_obj:
                metadata = _copy_dict_without_key(resolved_obj, u"$graph")
                return resolved_obj[u"$graph"], metadata
            else:
                return resolved_obj, metadata
        else:
            return resolved_obj, metadata

    def _resolve_idmap(
        self,
        document,  # type: CommentedMap
        loader,  # type: Loader
    ):
        # type: (...) -> None
        # Convert fields with mapSubject into lists
        # use mapPredicate if the mapped value isn't a dict.
        for idmapField in loader.idmap:
            if idmapField in document:
                idmapFieldValue = document[idmapField]
                if (
                    isinstance(idmapFieldValue, MutableMapping)
                    and "$import" not in idmapFieldValue
                    and "$include" not in idmapFieldValue
                ):
                    ls = CommentedSeq()
                    for k in sorted(idmapFieldValue.keys()):
                        val = idmapFieldValue[k]
                        v = None  # type: Optional[CommentedMap]
                        if not isinstance(val, CommentedMap):
                            if idmapField in loader.mapPredicate:
                                v = CommentedMap(
                                    ((loader.mapPredicate[idmapField], val),)
                                )
                                v.lc.add_kv_line_col(
                                    loader.mapPredicate[idmapField],
                                    document[idmapField].lc.data[k],
                                )
                                v.lc.filename = document.lc.filename
                            else:
                                raise ValidationException(
                                    "mapSubject '{}' value '{}' is not a dict "
                                    "and does not have a mapPredicate.".format(k, v)
                                )
                        else:
                            v = val

                        v[loader.idmap[idmapField]] = k
                        v.lc.add_kv_line_col(
                            loader.idmap[idmapField], document[idmapField].lc.data[k]
                        )
                        v.lc.filename = document.lc.filename

                        ls.lc.add_kv_line_col(len(ls), document[idmapField].lc.data[k])

                        ls.lc.filename = document.lc.filename
                        ls.append(v)

                    document[idmapField] = ls

    typeDSLregex = re.compile(Text(r"^([^[?]+)(\[\])?(\?)?$"))

    def _type_dsl(
        self,
        t,  # type: Union[Text, Dict[Text, Text], List[Text]]
        lc,  # type: LineCol
        filename,  # type: Text
    ):  # type: (...) -> Union[Text, Dict[Text, Text], List[Text]]

        if not isinstance(t, string_types):
            return t

        m = Loader.typeDSLregex.match(t)
        if not m:
            return t
        first = m.group(1)
        second = third = None
        if bool(m.group(2)):
            second = CommentedMap((("type", "array"), ("items", first)))
            second.lc.add_kv_line_col("type", lc)
            second.lc.add_kv_line_col("items", lc)
            second.lc.filename = filename
        if bool(m.group(3)):
            third = CommentedSeq([u"null", second or first])
            third.lc.add_kv_line_col(0, lc)
            third.lc.add_kv_line_col(1, lc)
            third.lc.filename = filename
        return third or second or first

    def _secondaryFile_dsl(
        self,
        t,  # type: Union[Text, Dict[Text, Text], List[Text]]
        lc,  # type: LineCol
        filename,  # type: Text
    ):  # type: (...) -> Union[Text, Dict[Text, Text], List[Text]]

        if not isinstance(t, string_types):
            return t
        pat = t
        req = None
        if t.endswith("?"):
            pat = t[0:-1]
            req = False

        second = CommentedMap((("pattern", pat), ("required", req)))
        second.lc.add_kv_line_col("pattern", lc)
        second.lc.add_kv_line_col("required", lc)
        second.lc.filename = filename
        return second

    def _apply_dsl(
        self,
        datum,  # type: Union[Text, Dict[Any, Any], List[Any]]
        d,  # type: Text
        loader,  # type: Loader
        lc,  # type: LineCol
        filename,  # type: Text
    ):
        # type: (...) -> Union[Text, Dict[Any, Any], List[Any]]
        if d in loader.type_dsl_fields:
            return self._type_dsl(datum, lc, filename)
        elif d in loader.secondaryFile_dsl_fields:
            return self._secondaryFile_dsl(datum, lc, filename)
        else:
            return datum

    def _resolve_dsl(
        self,
        document,  # type: CommentedMap
        loader,  # type: Loader
    ):
        # type: (...) -> None
        fields = list(loader.type_dsl_fields)
        fields.extend(loader.secondaryFile_dsl_fields)

        for d in fields:
            if d in document:
                datum2 = datum = document[d]
                if isinstance(datum, string_types):
                    datum2 = self._apply_dsl(
                        datum, d, loader, document.lc.data[d], document.lc.filename
                    )
                elif isinstance(datum, CommentedSeq):
                    datum2 = CommentedSeq()
                    for n, t in enumerate(datum):
                        if datum.lc and datum.lc.data:
                            datum2.lc.add_kv_line_col(len(datum2), datum.lc.data[n])
                            datum2.append(
                                self._apply_dsl(
                                    t, d, loader, datum.lc.data[n], document.lc.filename
                                )
                            )
                        else:
                            datum2.append(self._apply_dsl(t, d, loader, LineCol(), ""))
                if isinstance(datum2, CommentedSeq):
                    datum3 = CommentedSeq()
                    seen = []  # type: List[Text]
                    for i, item in enumerate(datum2):
                        if isinstance(item, CommentedSeq):
                            for j, v in enumerate(item):
                                if v not in seen:
                                    datum3.lc.add_kv_line_col(
                                        len(datum3), item.lc.data[j]
                                    )
                                    datum3.append(v)
                                    seen.append(v)
                        else:
                            if item not in seen:
                                if datum2.lc and datum2.lc.data:
                                    datum3.lc.add_kv_line_col(
                                        len(datum3), datum2.lc.data[i]
                                    )
                                datum3.append(item)
                                seen.append(item)
                    document[d] = datum3
                else:
                    document[d] = datum2

    def _resolve_identifier(self, document, loader, base_url):
        # type: (CommentedMap, Loader, Text) -> Text
        # Expand identifier field (usually 'id') to resolve scope
        for identifer in loader.identifiers:
            if identifer in document:
                if isinstance(document[identifer], string_types):
                    document[identifer] = loader.expand_url(
                        document[identifer], base_url, scoped_id=True
                    )
                    if document[identifer] not in loader.idx or isinstance(
                        loader.idx[document[identifer]], string_types
                    ):
                        loader.idx[document[identifer]] = document
                    base_url = document[identifer]
                else:
                    raise ValidationException(
                        "identifier field '{}' must be a string".format(
                            document[identifer]
                        )
                    )
        return base_url

    def _resolve_identity(self, document, loader, base_url):
        # type: (Dict[Text, List[Text]], Loader, Text) -> None
        # Resolve scope for identity fields (fields where the value is the
        # identity of a standalone node, such as enum symbols)
        for identifer in loader.identity_links:
            if identifer in document and isinstance(
                document[identifer], MutableSequence
            ):
                for n, _v in enumerate(document[identifer]):
                    if isinstance(document[identifer][n], string_types):
                        document[identifer][n] = loader.expand_url(
                            document[identifer][n], base_url, scoped_id=True
                        )
                        if document[identifer][n] not in loader.idx:
                            loader.idx[document[identifer][n]] = document[identifer][n]

    def _normalize_fields(self, document, loader):
        # type: (CommentedMap, Loader) -> None
        # Normalize fields which are prefixed or full URIn to vocabulary terms
        for d in list(document.keys()):
            d2 = loader.expand_url(d, u"", scoped_id=False, vocab_term=True)
            if d != d2:
                document[d2] = document[d]
                document.lc.add_kv_line_col(d2, document.lc.data[d])
                del document[d]

    def _resolve_uris(
        self,
        document,  # type: Dict[Text, Union[Text, List[Text]]]
        loader,  # type: Loader
        base_url,  # type: Text
    ):
        # type: (...) -> None
        # Resolve remaining URLs based on document base
        for d in loader.url_fields:
            if d in document:
                datum = document[d]
                if isinstance(datum, string_types):
                    document[d] = loader.expand_url(
                        datum,
                        base_url,
                        scoped_id=False,
                        vocab_term=(d in loader.vocab_fields),
                        scoped_ref=loader.scoped_ref_fields.get(d),
                    )
                elif isinstance(datum, MutableSequence):
                    for i, url in enumerate(datum):
                        if isinstance(url, string_types):
                            datum[i] = loader.expand_url(
                                url,
                                base_url,
                                scoped_id=False,
                                vocab_term=(d in loader.vocab_fields),
                                scoped_ref=loader.scoped_ref_fields.get(d),
                            )

    def resolve_all(
        self,
        document,  # type: Union[CommentedMap, CommentedSeq]
        base_url,  # type: Text
        file_base=None,  # type: Optional[Text]
        checklinks=True,  # type: bool
        strict_foreign_properties=False,  # type: bool
    ):
        # type: (...) -> Loader.resolved_ref_type
        loader = self
        metadata = CommentedMap()  # type: CommentedMap
        if file_base is None:
            file_base = base_url

        if isinstance(document, CommentedMap):
            # Handle $import and $include
            if u"$import" in document or u"$include" in document:
                return self.resolve_ref(
                    document,
                    base_url=file_base,
                    checklinks=checklinks,
                    strict_foreign_properties=strict_foreign_properties,
                )
            elif u"$mixin" in document:
                return self.resolve_ref(
                    document,
                    base_url=base_url,
                    checklinks=checklinks,
                    strict_foreign_properties=strict_foreign_properties,
                )
        elif isinstance(document, CommentedSeq):
            pass
        elif isinstance(document, (list, dict)):
            raise ValidationException(
                "Expected CommentedMap or CommentedSeq, got {}: `{}`".format(
                    type(document), document
                )
            )
        else:
            return (document, metadata)

        newctx = None  # type: Optional[Loader]
        if isinstance(document, CommentedMap):
            # Handle $base, $profile, $namespaces, $schemas and $graph
            if u"$base" in document:
                base_url = document[u"$base"]

            if u"$profile" in document:
                if newctx is None:
                    newctx = SubLoader(self)
                newctx.add_namespaces(document.get(u"$namespaces", CommentedMap()))
                newctx.add_schemas(document.get(u"$schemas", []), document[u"$profile"])

            if u"$namespaces" in document:
                if newctx is None:
                    newctx = SubLoader(self)
                newctx.add_namespaces(document[u"$namespaces"])

            if u"$schemas" in document:
                if newctx is None:
                    newctx = SubLoader(self)
                newctx.add_schemas(document[u"$schemas"], file_base)

            if newctx is not None:
                loader = newctx

            for identifer in loader.identity_links:
                if identifer in document:
                    if isinstance(document[identifer], string_types):
                        document[identifer] = loader.expand_url(
                            document[identifer], base_url, scoped_id=True
                        )
                        loader.idx[document[identifer]] = document

            metadata = document
            if u"$graph" in document:
                document = document[u"$graph"]

        if isinstance(document, CommentedMap):
            self._normalize_fields(document, loader)
            self._resolve_idmap(document, loader)
            self._resolve_dsl(document, loader)
            base_url = self._resolve_identifier(document, loader, base_url)
            self._resolve_identity(document, loader, base_url)
            self._resolve_uris(document, loader, base_url)

            try:
                for key, val in document.items():
                    subscope = ""  # type: Text
                    if key in loader.subscopes:
                        subscope = "/" + loader.subscopes[key]
                    document[key], _ = loader.resolve_all(
                        val, base_url + subscope, file_base=file_base, checklinks=False
                    )
            except ValidationException as v:
                _logger.warning("loader is %s", id(loader), exc_info=True)
                raise_from(
                    ValidationException(
                        "({}) ({}) Validation error in field {}:".format(
                            id(loader), file_base, key
                        ),
                        None,
                        [v],
                    ),
                    v,
                )

        elif isinstance(document, CommentedSeq):
            i = 0
            try:
                while i < len(document):
                    val = document[i]
                    if isinstance(val, CommentedMap) and (
                        u"$import" in val or u"$mixin" in val
                    ):
                        l, import_metadata = loader.resolve_ref(
                            val, base_url=file_base, checklinks=False
                        )
                        metadata.setdefault("$import_metadata", {})
                        for identifier in loader.identifiers:
                            if identifier in import_metadata:
                                metadata["$import_metadata"][
                                    import_metadata[identifier]
                                ] = import_metadata
                        if isinstance(l, CommentedSeq):
                            lc = document.lc.data[i]
                            del document[i]
                            llen = len(l)
                            for j in range(len(document) + llen, i + llen, -1):
                                document.lc.data[j - 1] = document.lc.data[j - llen]
                            for item in l:
                                document.insert(i, item)
                                document.lc.data[i] = lc
                                i += 1
                        else:
                            document[i] = l
                            i += 1
                    else:
                        document[i], _ = loader.resolve_all(
                            val, base_url, file_base=file_base, checklinks=False
                        )
                        i += 1
            except ValidationException as v:
                _logger.warning("failed", exc_info=True)
                raise_from(
                    ValidationException(
                        "({}) ({}) Validation error in position {}:".format(
                            id(loader), file_base, i
                        ),
                        None,
                        [v],
                    ),
                    v,
                )

        if checklinks:
            all_doc_ids = {}  # type: Dict[Text, Text]
            loader.validate_links(
                document,
                u"",
                all_doc_ids,
                strict_foreign_properties=strict_foreign_properties,
            )

        return document, metadata

    def fetch(self, url, inject_ids=True):  # type: (Text, bool) -> Any
        if url in self.idx:
            return self.idx[url]
        try:
            text = self.fetch_text(url)
            if isinstance(text, bytes):
                textIO = StringIO(text.decode("utf-8"))
            else:
                textIO = StringIO(text)
            textIO.name = str(url)
            attachments = yaml.round_trip_load_all(textIO, preserve_quotes=True)
            result = next(attachments)

            if self.allow_attachments is not None and self.allow_attachments(result):
                i = 1
                for a in attachments:
                    self.idx["{}#attachment-{}".format(url, i)] = a
                    i += 1
            add_lc_filename(result, url)
        except yaml.error.MarkedYAMLError as e:
            raise_from(to_validation_exception(e), e)
        if isinstance(result, CommentedMap) and inject_ids and bool(self.identifiers):
            for identifier in self.identifiers:
                if identifier not in result:
                    result[identifier] = url
                self.idx[
                    self.expand_url(result[identifier], url, scoped_id=True)
                ] = result
        self.idx[url] = result
        return result

    FieldType = TypeVar("FieldType", Text, CommentedSeq, CommentedMap)

    def validate_scoped(self, field, link, docid):
        # type: (Text, Text, Text) -> Text
        split = urllib.parse.urlsplit(docid)
        sp = split.fragment.split(u"/")
        n = self.scoped_ref_fields[field]
        while n > 0 and len(sp) > 0:
            sp.pop()
            n -= 1
        tried = []
        while True:
            sp.append(link)
            url = urllib.parse.urlunsplit(
                (split.scheme, split.netloc, split.path, split.query, u"/".join(sp))
            )
            tried.append(url)
            if url in self.idx:
                return url
            sp.pop()
            if len(sp) == 0:
                break
            sp.pop()
        if onWindows() and link.startswith("file:"):
            link = link.lower()
        raise ValidationException(
            "Field `{}` references unknown identifier `{}`, tried {}".format(
                field, link, ", ".join(tried)
            )
        )

    def validate_link(self, field, link, docid, all_doc_ids):
        # type: (Text, Loader.FieldType, Text, Dict[Text, Text]) -> Loader.FieldType
        if field in self.nolinkcheck:
            return link
        if isinstance(link, string_types):
            if field in self.vocab_fields:
                if (
                    link not in self.vocab
                    and link not in self.idx
                    and link not in self.rvocab
                ):
                    if field in self.scoped_ref_fields:
                        return self.validate_scoped(field, link, docid)
                    elif not self.check_exists(link):
                        raise ValidationException(
                            "Field `{}` contains undefined reference to `{}`".format(
                                field, link
                            )
                        )
            elif link not in self.idx and link not in self.rvocab:
                if field in self.scoped_ref_fields:
                    return self.validate_scoped(field, link, docid)
                elif not self.check_exists(link):
                    raise ValidationException(
                        "Field `{}` contains undefined reference to `{}`".format(
                            field, link
                        )
                    )
        elif isinstance(link, CommentedSeq):
            errors = []
            for n, i in enumerate(link):
                try:
                    link[n] = self.validate_link(field, i, docid, all_doc_ids)
                except ValidationException as v:
                    errors.append(v)
            if bool(errors):
                raise ValidationException("", None, errors)
        elif isinstance(link, CommentedMap):
            self.validate_links(link, docid, all_doc_ids)
        else:
            raise ValidationException(
                "`{}` field is {}, expected string, list, or a dict.".format(
                    field, type(link).__name__
                )
            )
        return link

    def getid(self, d):  # type: (Any) -> Optional[Text]
        if isinstance(d, MutableMapping):
            for i in self.identifiers:
                if i in d:
                    idd = d[i]
                    if isinstance(idd, string_types):
                        return idd
        return None

    def validate_links(
        self,
        document,  # type: Union[CommentedMap, CommentedSeq, Text, None]
        base_url,  # type: Text
        all_doc_ids,  # type: Dict[Text, Text]
        strict_foreign_properties=False,  # type: bool
    ):  # type: (...) -> None
        docid = self.getid(document)
        if not docid:
            docid = base_url

        errors = []  # type: List[SchemaSaladException]
        iterator = None  # type: Any
        if isinstance(document, MutableSequence):
            iterator = enumerate(document)
        elif isinstance(document, MutableMapping):
            for d in self.url_fields:
                sl = SourceLine(document, d, Text)
                try:
                    if d in document and d not in self.identity_links:
                        document[d] = self.validate_link(
                            d, document[d], docid, all_doc_ids
                        )
                except SchemaSaladException as v:
                    v = v.with_sourceline(sl)
                    if d == "$schemas" or (
                        d in self.foreign_properties and not strict_foreign_properties
                    ):
                        _logger.warning(v)
                    else:
                        errors.append(v)
            # TODO: Validator should local scope only in which
            # duplicated keys are prohibited.
            # See also https://github.com/common-workflow-language/common-workflow-language/issues/734  # noqa: B950
            # In the future, it should raise
            # ValidationException instead of _logger.warn
            try:
                for (
                    identifier
                ) in self.identifiers:  # validate that each id is defined uniquely
                    if identifier in document:
                        sl = SourceLine(document, identifier, Text)
                        if (
                            document[identifier] in all_doc_ids
                            and sl.makeLead() != all_doc_ids[document[identifier]]
                        ):
                            _logger.warning(
                                "%s object %s `%s` previously defined",
                                all_doc_ids[document[identifier]],
                                identifier,
                                relname(document[identifier]),
                            )
                        else:
                            all_doc_ids[document[identifier]] = sl.makeLead()
                            break
            except ValidationException as v:
                errors.append(v.with_sourceline(sl))

            if hasattr(document, "iteritems"):
                iterator = iteritems(document)
            else:
                iterator = list(document.items())
        else:
            return

        for key, val in iterator:
            sl = SourceLine(document, key, Text)
            try:
                self.validate_links(
                    val,
                    docid,
                    all_doc_ids,
                    strict_foreign_properties=strict_foreign_properties,
                )
            except ValidationException as v:
                if key in self.nolinkcheck or (
                    isinstance(key, string_types) and ":" in key
                ):
                    _logger.warning(v)
                else:
                    docid2 = self.getid(val)
                    if docid2 is not None:
                        errors.append(
                            ValidationException(
                                "checking object `{}`".format(relname(docid2)), sl, [v]
                            )
                        )
                    else:
                        if isinstance(key, string_types):
                            errors.append(
                                ValidationException(
                                    "checking field `{}`".format(key), sl, [v]
                                )
                            )
                        else:
                            errors.append(ValidationException("checking item", sl, [v]))
        if bool(errors):
            if len(errors) > 1:
                raise ValidationException("", None, errors)
            else:
                raise errors[0]
        return


D = TypeVar("D", CommentedMap, ContextType)


def _copy_dict_without_key(from_dict, filtered_key):
    # type: (D, Any) -> D
    new_dict = CommentedMap(from_dict.items())
    if filtered_key in new_dict:
        del new_dict[filtered_key]
    if isinstance(from_dict, CommentedMap):
        new_dict.lc.data = copy.copy(from_dict.lc.data)
        new_dict.lc.filename = from_dict.lc.filename
    return new_dict
