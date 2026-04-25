"""Template code used by python_codegen.py."""

from __future__ import annotations

import logging
import os
import pathlib
import sys
import tempfile
import xml.sax  # nosec
from abc import ABCMeta, abstractmethod
from collections.abc import MutableMapping, MutableSequence
from typing import Any, Final, TypeAlias, cast
from urllib.parse import quote, urlparse, urlsplit
from urllib.request import pathname2url

from mypy_extensions import trait
from rdflib import Graph
from rdflib.plugins.parsers.notation3 import BadSyntax

from schema_salad.fetcher import DefaultFetcher, Fetcher, MemoryCachingFetcher
from schema_salad.utils import CacheType  # requires schema-salad v8.2+

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

_logger: Final = logging.getLogger("salad")


IdxType: TypeAlias = MutableMapping[str, tuple[Any, "LoadingOptions"]]


class LoadingOptions:
    idx: Final[IdxType]
    fileuri: Final[str | None]
    baseuri: Final[str]
    namespaces: Final[MutableMapping[str, str]]
    schemas: Final[MutableSequence[str]]
    original_doc: Final[Any | None]
    addl_metadata: Final[MutableMapping[str, Any]]
    fetcher: Final[Fetcher]
    vocab: Final[dict[str, str]]
    rvocab: Final[dict[str, str]]
    cache: Final[CacheType]
    imports: Final[list[str]]
    includes: Final[list[str]]
    no_link_check: Final[bool | None]
    container: Final[str | None]

    def __init__(
        self,
        fetcher: Fetcher | None = None,
        namespaces: dict[str, str] | None = None,
        schemas: list[str] | None = None,
        fileuri: str | None = None,
        copyfrom: LoadingOptions | None = None,
        original_doc: Any | None = None,
        addl_metadata: dict[str, str] | None = None,
        baseuri: str | None = None,
        idx: IdxType | None = None,
        imports: list[str] | None = None,
        includes: list[str] | None = None,
        no_link_check: bool | None = None,
        container: str | None = None,
    ) -> None:
        """Create a LoadingOptions object."""
        self.original_doc = original_doc

        if idx is not None:
            temp_idx = idx
        else:
            temp_idx = copyfrom.idx if copyfrom is not None else {}
        self.idx = temp_idx

        if fileuri is not None:
            temp_fileuri: str | None = fileuri
        else:
            temp_fileuri = copyfrom.fileuri if copyfrom is not None else None
        self.fileuri = temp_fileuri

        if baseuri is not None:
            temp_baseuri = baseuri
        else:
            temp_baseuri = copyfrom.baseuri if copyfrom is not None else ""
        self.baseuri = temp_baseuri

        if namespaces is not None:
            temp_namespaces: MutableMapping[str, str] = namespaces
        else:
            temp_namespaces = copyfrom.namespaces if copyfrom is not None else {}
        self.namespaces = temp_namespaces

        if schemas is not None:
            temp_schemas: MutableSequence[str] = schemas
        else:
            temp_schemas = copyfrom.schemas if copyfrom is not None else []
        self.schemas = temp_schemas

        if addl_metadata is not None:
            temp_addl_metadata: MutableMapping[str, Any] = addl_metadata
        else:
            temp_addl_metadata = copyfrom.addl_metadata if copyfrom is not None else {}
        self.addl_metadata = temp_addl_metadata

        if imports is not None:
            temp_imports = imports
        else:
            temp_imports = copyfrom.imports if copyfrom is not None else []
        self.imports = temp_imports

        if includes is not None:
            temp_includes = includes
        else:
            temp_includes = copyfrom.includes if copyfrom is not None else []
        self.includes = temp_includes

        if no_link_check is not None:
            temp_no_link_check: bool | None = no_link_check
        else:
            temp_no_link_check = copyfrom.no_link_check if copyfrom is not None else False
        self.no_link_check = temp_no_link_check

        if container is not None:
            temp_container: str | None = container
        else:
            temp_container = copyfrom.container if copyfrom is not None else None
        self.container = temp_container

        if fetcher is not None:
            temp_fetcher = fetcher
        elif copyfrom is not None:
            temp_fetcher = copyfrom.fetcher
        else:
            import requests
            from cachecontrol.caches import SeparateBodyFileCache
            from cachecontrol.wrapper import CacheControl

            root = pathlib.Path(os.environ.get("HOME", tempfile.gettempdir()))
            session = CacheControl(
                requests.Session(),
                cache=SeparateBodyFileCache(root / ".cache" / "salad"),
            )
            temp_fetcher = DefaultFetcher({}, session)
        self.fetcher = temp_fetcher

        self.cache = self.fetcher.cache if isinstance(self.fetcher, MemoryCachingFetcher) else {}
        self.vocab = {k: v for k, v in self.namespaces.items()}
        self.rvocab = {v: k for k, v in self.namespaces.items()}

    @property
    def graph(self) -> Graph:
        """Generate a merged rdflib.Graph from all entries in self.schemas."""
        graph = Graph()
        if not self.schemas:
            return graph
        key: Final = str(hash(tuple(self.schemas)))
        if key in self.cache:
            return cast(Graph, self.cache[key])
        for schema in self.schemas:
            fetchurl = (
                self.fetcher.urljoin(self.fileuri, schema)
                if self.fileuri is not None
                else pathlib.Path(schema).resolve().as_uri()
            )
            if fetchurl not in self.cache or self.cache[fetchurl] is True:
                _logger.debug("Getting external schema %s", fetchurl)
                try:
                    content = self.fetcher.fetch_text(fetchurl)
                except Exception as e:
                    _logger.warning("Could not load extension schema %s: %s", fetchurl, str(e))
                    continue
                newGraph = Graph()
                err_msg = "unknown error"
                for fmt in ["xml", "turtle"]:
                    try:
                        newGraph.parse(data=content, format=fmt, publicID=str(fetchurl))
                        self.cache[fetchurl] = newGraph
                        graph += newGraph
                        break
                    except (xml.sax.SAXParseException, TypeError, BadSyntax) as e:
                        err_msg = str(e)
                else:
                    _logger.warning("Could not load extension schema %s: %s", fetchurl, err_msg)
        self.cache[key] = graph
        return graph


@trait
class Saveable(metaclass=ABCMeta):
    """Mark classes than have a save() and fromDoc() function."""

    @classmethod
    @abstractmethod
    def fromDoc(
        cls,
        _doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
    ) -> Self:
        """Construct this object from the result of yaml.load()."""

    @abstractmethod
    def save(
        self, top: bool = False, base_url: str = "", relative_uris: bool = True
    ) -> dict[str, Any]:
        """Convert this object to a JSON/YAML friendly dictionary."""


save_type: TypeAlias = (
    None | MutableMapping[str, Any] | MutableSequence[Any] | int | float | bool | str
)


def extract_type(val_type: type[Any]) -> str:
    """Take a type of value, and extracts the value as a string."""
    val_str: Final = str(val_type)
    return val_str.split("'")[1]


def convert_typing(val_type: str) -> str:
    """Normalize type names to schema-salad types."""
    if "None" in val_type:
        return "null"
    if "CommentedSeq" in val_type or "list" in val_type:
        return "array"
    if "CommentedMap" in val_type or "dict" in val_type:
        return "object"
    if "False" in val_type or "True" in val_type:
        return "boolean"
    return val_type


def parse_errors(error_message: str) -> tuple[str, str, str]:
    """Parse error messages from several loaders into one error message."""
    if not error_message.startswith("Expected"):
        return error_message, "", ""
    vals: Final = error_message.split("\n")
    if len(vals) == 1:
        return error_message, "", ""
    types1: Final = set()
    for val in vals:
        individual_vals = val.split(" ")
        if val == "":
            continue
        if individual_vals[1] == "one":
            individual_vals = val.split("(")[1].split(",")
            for t in individual_vals:
                types1.add(t.strip(" ").strip(")\n"))
        elif individual_vals[2] == "<class":
            types1.add(individual_vals[3].strip(">").replace("'", ""))
        elif individual_vals[0] == "Value":
            types1.add(individual_vals[-1].strip("."))
        else:
            types1.add(individual_vals[1].replace(",", ""))
    types2: Final = {val for val in types1 if val != "NoneType"}
    if "str" in types2:
        types3 = {convert_typing(val) for val in types2 if "'" not in val}
    else:
        types3 = types2
    to_print = ""
    for val in types3:
        if "'" in val:
            to_print = "value" if len(types3) == 1 else "values"

    if to_print == "":
        to_print = "type" if len(types3) == 1 else "types"

    verb_tensage: Final = "is" if len(types3) == 1 else "are"

    return str(types3).replace("{", "(").replace("}", ")").replace("'", ""), to_print, verb_tensage


def save(
    val: Any,
    top: bool = True,
    base_url: str = "",
    relative_uris: bool = True,
) -> save_type:
    if isinstance(val, Saveable):
        return val.save(top=top, base_url=base_url, relative_uris=relative_uris)
    if isinstance(val, MutableSequence):
        return [save(v, top=False, base_url=base_url, relative_uris=relative_uris) for v in val]
    if isinstance(val, MutableMapping):
        newdict: Final = {}
        for key in val:
            newdict[key] = save(val[key], top=False, base_url=base_url, relative_uris=relative_uris)
        return newdict
    if val is None or isinstance(val, (int, float, bool, str)):
        return val
    raise Exception("Not Saveable: %s" % type(val))


def save_with_metadata(
    val: Any,
    valLoadingOpts: LoadingOptions,
    top: bool = True,
    base_url: str = "",
    relative_uris: bool = True,
) -> save_type:
    """Save and set $namespaces, $schemas, $base and any other metadata fields at the top level."""
    saved_val: Final = save(val, top, base_url, relative_uris)
    newdict: MutableMapping[str, Any] = {}
    if isinstance(saved_val, MutableSequence):
        newdict = {"$graph": saved_val}
    elif isinstance(saved_val, MutableMapping):
        newdict = saved_val

    if valLoadingOpts.namespaces:
        newdict["$namespaces"] = valLoadingOpts.namespaces
    if valLoadingOpts.schemas:
        newdict["$schemas"] = valLoadingOpts.schemas
    if valLoadingOpts.baseuri:
        newdict["$base"] = valLoadingOpts.baseuri
    for k, v in valLoadingOpts.addl_metadata.items():
        if k not in newdict:
            newdict[k] = v

    return newdict


def file_uri(path: str, split_frag: bool = False) -> str:
    """Transform a file path into a URL with file scheme."""
    if path.startswith("file://"):
        return path
    if split_frag:
        pathsp: Final = path.split("#", 2)
        frag = "#" + quote(str(pathsp[1])) if len(pathsp) == 2 else ""
        urlpath = pathname2url(str(pathsp[0]))
    else:
        urlpath = pathname2url(path)
        frag = ""
    if urlpath.startswith("//"):
        return f"file:{urlpath}{frag}"
    return f"file://{urlpath}{frag}"


def prefix_url(url: str, namespaces: dict[str, str]) -> str:
    """Expand short forms into full URLs using the given namespace dictionary."""
    for k, v in namespaces.items():
        if url.startswith(v):
            return k + ":" + url[len(v) :]
    return url


def save_relative_uri(
    uri: Any,
    base_url: str,
    scoped_id: bool,
    ref_scope: int | None,
    relative_uris: bool,
) -> Any:
    """Convert any URI to a relative one, obeying the scoping rules."""
    if isinstance(uri, MutableSequence):
        return [save_relative_uri(u, base_url, scoped_id, ref_scope, relative_uris) for u in uri]
    elif isinstance(uri, str):
        if not relative_uris or uri == base_url:
            return uri
        urisplit: Final = urlsplit(uri)
        basesplit: Final = urlsplit(base_url)
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
            return urisplit.fragment
        return uri
    else:
        return save(uri, top=False, base_url=base_url, relative_uris=relative_uris)


def shortname(inputid: str) -> str:
    """
    Compute the shortname of a fully qualified identifier.

    See https://w3id.org/cwl/v1.2/SchemaSalad.html#Short_names.
    """
    parsed_id: Final = urlparse(inputid)
    if parsed_id.fragment:
        return parsed_id.fragment.split("/")[-1]
    return parsed_id.path.split("/")[-1]
