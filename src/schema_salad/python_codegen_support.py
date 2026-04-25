from __future__ import annotations

import copy

from collections.abc import MutableSequence, Sequence, MutableMapping
from io import StringIO
from itertools import chain
from typing import Any, Final, cast, Generic, TypeVar
from urllib.parse import urldefrag, urlsplit, urlunsplit

from ruamel.yaml.comments import CommentedMap

from schema_salad.exceptions import ValidationException, SchemaSaladException
from schema_salad.runtime import LoadingOptions, convert_typing, extract_type, Saveable
from schema_salad.sourceline import SourceLine, add_lc_filename
from schema_salad.utils import yaml_no_ts  # requires schema-salad v8.2+

S = TypeVar("S", bound=Saveable)


_vocab: Final[dict[str, str]] = {}
_rvocab: Final[dict[str, str]] = {}


class _Loader:
    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any | None:
        pass


class _AnyLoader(_Loader):
    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any:
        if doc is not None:
            return doc
        raise ValidationException("Expected non-null")


class _PrimitiveLoader(_Loader):
    def __init__(self, tp: type | tuple[type[str], type[str]]) -> None:
        self.tp: Final = tp

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any:
        if not isinstance(doc, self.tp):
            raise ValidationException(f"Expected a {self.tp} but got {doc.__class__.__name__}")
        return doc

    def __repr__(self) -> str:
        return str(self.tp)


class _ArrayLoader(_Loader):
    def __init__(self, items: _Loader) -> None:
        self.items: Final = items

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> list[Any]:
        if not isinstance(doc, MutableSequence):
            raise ValidationException(
                f"Value is a {convert_typing(extract_type(type(doc)))}, "
                f"but valid type for this field is an array."
            )
        r: Final[list[Any]] = []
        errors: Final[list[SchemaSaladException]] = []
        fields: Final[list[str]] = []
        for i in range(0, len(doc)):
            try:
                lf = _load_field(
                    doc[i], _UnionLoader([self, self.items]), baseuri, loadingOptions, lc=lc
                )
                flatten = loadingOptions.container != "@list"
                if flatten and isinstance(lf, MutableSequence):
                    r.extend(lf)
                else:
                    r.append(lf)

                if isinstance(doc[i], CommentedMap):
                    if doc[i].get("id") is not None:
                        if doc[i].get("id") in fields:
                            errors.append(
                                ValidationException(
                                    f"Duplicate field {doc[i].get('id')!r}",
                                    SourceLine(doc[i], "id", str),
                                    [],
                                )
                            )
                        else:
                            fields.append(doc[i].get("id"))

            except ValidationException as e:
                e = ValidationException(
                    "array item is invalid because", SourceLine(doc, i, str), [e]
                )
                errors.append(e)
        if errors:
            raise ValidationException("", None, errors)
        return r

    def __repr__(self) -> str:
        return f"array<{self.items}>"


class _MapLoader(_Loader):
    def __init__(
        self,
        values: _Loader,
        name: str | None = None,
        container: str | None = None,
        no_link_check: bool | None = None,
    ) -> None:
        self.values: Final = values
        self.name: Final = name
        self.container: Final = container
        self.no_link_check: Final = no_link_check

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> dict[str, Any]:
        if not isinstance(doc, MutableMapping):
            raise ValidationException(f"Expected a map, was {type(doc)}")
        if self.container is not None or self.no_link_check is not None:
            loadingOptions = LoadingOptions(
                copyfrom=loadingOptions, container=self.container, no_link_check=self.no_link_check
            )
        r: Final[dict[str, Any]] = {}
        errors: Final[list[SchemaSaladException]] = []
        for k, v in doc.items():
            try:
                lf = _load_field(v, self.values, baseuri, loadingOptions, lc)
                r[k] = lf
            except ValidationException as e:
                errors.append(e.with_sourceline(SourceLine(doc, k, str)))
        if errors:
            raise ValidationException("", None, errors)
        return r

    def __repr__(self) -> str:
        return self.name if self.name is not None else f"map<string, {self.values}>"


class _EnumLoader(_Loader):
    def __init__(self, symbols: Sequence[str], name: str) -> None:
        self.symbols: Final = symbols
        self.name: Final = name

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> str:
        if doc in self.symbols:
            return cast(str, doc)
        raise ValidationException(f"Expected one of {self.symbols}")

    def __repr__(self) -> str:
        return self.name


class _SecondaryDSLLoader(_Loader):
    def __init__(self, inner: _Loader) -> None:
        self.inner: Final = inner

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any:
        r: Final[list[dict[str, Any]]] = []
        match doc:
            case MutableSequence() as dlist:
                for d in dlist:
                    if isinstance(d, str):
                        if d.endswith("?"):
                            r.append({"pattern": d[:-1], "required": False})
                        else:
                            r.append({"pattern": d})
                    elif isinstance(d, dict):
                        new_dict1: dict[str, Any] = {}
                        dict_copy = copy.deepcopy(d)
                        if "pattern" in dict_copy:
                            new_dict1["pattern"] = dict_copy.pop("pattern")
                        else:
                            raise ValidationException(
                                f"Missing pattern in secondaryFiles specification entry: {d}"
                            )
                        new_dict1["required"] = (
                            dict_copy.pop("required") if "required" in dict_copy else None
                        )

                        if len(dict_copy):
                            raise ValidationException(
                                "Unallowed values in secondaryFiles specification entry: {}".format(
                                    dict_copy
                                )
                            )
                        r.append(new_dict1)

                    else:
                        raise ValidationException(
                            "Expected a string or sequence of (strings or mappings)."
                        )
            case MutableMapping() as decl:
                new_dict2 = {}
                doc_copy = copy.deepcopy(decl)
                if "pattern" in doc_copy:
                    new_dict2["pattern"] = doc_copy.pop("pattern")
                else:
                    raise ValidationException(
                        f"Missing pattern in secondaryFiles specification entry: {decl}"
                    )
                new_dict2["required"] = doc_copy.pop("required") if "required" in doc_copy else None

                if len(doc_copy):
                    raise ValidationException(
                        f"Unallowed values in secondaryFiles specification entry: {doc_copy}"
                    )
                r.append(new_dict2)

            case str(decl):
                if decl.endswith("?"):
                    r.append({"pattern": decl[:-1], "required": False})
                else:
                    r.append({"pattern": decl})
            case _:
                raise ValidationException("Expected str or sequence of str")
        return self.inner.load(r, baseuri, loadingOptions, docRoot, lc=lc)


class _RecordLoader(_Loader, Generic[S]):
    def __init__(
        self,
        classtype: type[S],
        container: str | None = None,
        no_link_check: bool | None = None,
    ) -> None:
        self.classtype: Final = classtype
        self.container: Final = container
        self.no_link_check: Final = no_link_check

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> S:
        if not isinstance(doc, MutableMapping):
            raise ValidationException(
                f"Value is a {convert_typing(extract_type(type(doc)))}, "
                f"but valid type for this field is an object."
            )
        if self.container is not None or self.no_link_check is not None:
            loadingOptions = LoadingOptions(
                copyfrom=loadingOptions, container=self.container, no_link_check=self.no_link_check
            )
        return self.classtype.fromDoc(doc, baseuri, loadingOptions, docRoot=docRoot)

    def __repr__(self) -> str:
        return str(self.classtype.__name__)


class _ExpressionLoader(_Loader):
    def __init__(self, items: type[str]) -> None:
        self.items: Final = items

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> str:
        if not isinstance(doc, str):
            raise ValidationException(
                f"Value is a {convert_typing(extract_type(type(doc)))}, "
                f"but valid type for this field is a str."
            )
        else:
            return doc


class _UnionLoader(_Loader):
    def __init__(self, alternates: Sequence[_Loader], name: str | None = None) -> None:
        self.alternates = alternates
        self.name: Final = name

    def add_loaders(self, loaders: Sequence[_Loader]) -> None:
        self.alternates = tuple(loader for loader in chain(self.alternates, loaders))

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any:
        errors: Final = []

        if lc is None:
            lc = []

        for t in self.alternates:
            try:
                return t.load(doc, baseuri, loadingOptions, docRoot=docRoot, lc=lc)
            except ValidationException as e:
                if isinstance(t, _ArrayLoader) and len(self.alternates) > 1:
                    continue
                if isinstance(doc, (CommentedMap, dict)):
                    if "class" in doc:
                        if str(doc.get("class")) == str(t):
                            errors.append(
                                ValidationException(
                                    f"Object `{baseuri.split('/')[-1]}` is not valid because:",
                                    SourceLine(doc, next(iter(doc)), str),
                                    [e],
                                )
                            )
                    else:
                        if "array" in str(t):
                            continue
                        else:
                            if "id" in doc:
                                id = baseuri.split("/")[-1] + "#" + str(doc.get("id"))
                                if "id" in lc:
                                    errors.append(
                                        ValidationException(
                                            f"checking object `{id}` using `{t}`",
                                            SourceLine(lc, "id", str),
                                            [e],
                                        )
                                    )
                                else:
                                    errors.append(
                                        ValidationException(
                                            f"checking object `{id}` using `{t}`",
                                            SourceLine(lc, doc.get("id"), str),
                                            [e],
                                        )
                                    )
                            else:
                                if not isinstance(
                                    t, (_PrimitiveLoader)
                                ):  # avoids 'tried <class "NoneType"> was {x}' errors
                                    errors.append(
                                        ValidationException(f"tried `{t}` but", None, [e])
                                    )
                else:
                    # avoids "tried <class "CWLType"> but x" and instead returns the values for parsing
                    errors.append(ValidationException("", None, [e]))

        if isinstance(doc, (CommentedMap, dict)) and "class" in doc:
            if str(doc.get("class")) not in str(self.alternates):
                errors.append(
                    ValidationException(
                        "Field `class` contains undefined reference to "
                        + "`"
                        + "/".join(baseuri.split("/")[0:-1])
                        + "/"
                        + str(doc.get("class"))
                        + "`",
                        SourceLine(doc, "class", str),
                        [],
                    )
                )
        raise ValidationException("", None, errors, "*")

    def __repr__(self) -> str:
        return self.name if self.name is not None else " | ".join(str(a) for a in self.alternates)


class _URILoader(_Loader):
    def __init__(
        self,
        inner: _Loader,
        scoped_id: bool,
        vocab_term: bool,
        scoped_ref: int | None,
        no_link_check: bool | None,
    ) -> None:
        self.inner: Final = inner
        self.scoped_id: Final = scoped_id
        self.vocab_term: Final = vocab_term
        self.scoped_ref: Final = scoped_ref
        self.no_link_check: Final = no_link_check

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any:
        if self.no_link_check is not None:
            loadingOptions = LoadingOptions(
                copyfrom=loadingOptions, no_link_check=self.no_link_check
            )
        match doc:
            case MutableSequence() as decl:
                newdoc: Final = []
                for i in decl:
                    if isinstance(i, str):
                        newdoc.append(
                            _expand_url(
                                i,
                                baseuri,
                                loadingOptions,
                                self.scoped_id,
                                self.vocab_term,
                                self.scoped_ref,
                            )
                        )
                    else:
                        newdoc.append(i)
                doc = newdoc
            case str(decl):
                doc = _expand_url(
                    decl,
                    baseuri,
                    loadingOptions,
                    self.scoped_id,
                    self.vocab_term,
                    self.scoped_ref,
                )
        if isinstance(doc, str):
            if not loadingOptions.no_link_check:
                errors: Final = []
                try:
                    if not loadingOptions.fetcher.check_exists(doc):
                        errors.append(
                            ValidationException(f"contains undefined reference to `{doc}`")
                        )
                except ValidationException:
                    pass
                if len(errors) > 0:
                    raise ValidationException("", None, errors)
        return self.inner.load(doc, baseuri, loadingOptions, lc=lc)


class _TypeDSLLoader(_Loader):
    def __init__(
        self,
        inner: _Loader,
        refScope: int | None,
        salad_version: str,
    ) -> None:
        self.inner: Final = inner
        self.refScope: Final = refScope
        self.salad_version: Final = salad_version

    def resolve(
        self,
        doc: str,
        baseuri: str,
        loadingOptions: LoadingOptions,
    ) -> list[dict[str, Any] | str] | dict[str, Any] | str:
        doc_ = doc
        optional = False
        if doc_.endswith("?"):
            optional = True
            doc_ = doc_[0:-1]

        if doc_.endswith("[]"):
            salad_versions: Final = [int(v) for v in self.salad_version[1:].split(".")]
            items: list[dict[str, Any] | str] | dict[str, Any] | str = ""
            rest: Final = doc_[0:-2]
            if salad_versions < [1, 3]:
                if rest.endswith("[]"):
                    # To show the error message with the original type
                    return doc
                else:
                    items = _expand_url(
                        rest,
                        baseuri,
                        loadingOptions,
                        False,
                        True,
                        self.refScope,
                    )
            else:
                items = self.resolve(rest, baseuri, loadingOptions)
                if isinstance(items, str):
                    items = _expand_url(
                        items,
                        baseuri,
                        loadingOptions,
                        False,
                        True,
                        self.refScope,
                    )
            expanded: dict[str, Any] | str = {"type": "array", "items": items}
        else:
            expanded = _expand_url(
                doc_,
                baseuri,
                loadingOptions,
                False,
                True,
                self.refScope,
            )

        if optional:
            return ["null", expanded]
        else:
            return expanded

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any:
        if isinstance(doc, MutableSequence):
            r: Final[list[Any]] = []
            for d in doc:
                if isinstance(d, str):
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
        elif isinstance(doc, str):
            doc = self.resolve(doc, baseuri, loadingOptions)

        return self.inner.load(doc, baseuri, loadingOptions, lc=lc)


class _IdMapLoader(_Loader):
    def __init__(self, inner: _Loader, mapSubject: str, mapPredicate: str | None) -> None:
        self.inner: Final = inner
        self.mapSubject: Final = mapSubject
        self.mapPredicate: Final = mapPredicate

    def load(
        self,
        doc: Any,
        baseuri: str,
        loadingOptions: LoadingOptions,
        docRoot: str | None = None,
        lc: Any | None = None,
    ) -> Any:
        if isinstance(doc, MutableMapping):
            r: Final[list[Any]] = []
            for k in doc.keys():
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
        return self.inner.load(doc, baseuri, loadingOptions, lc=lc)


def _document_load(
    loader: _Loader,
    doc: str | MutableMapping[str, Any] | MutableSequence[Any],
    baseuri: str,
    loadingOptions: LoadingOptions,
    addl_metadata_fields: MutableSequence[str] | None = None,
) -> tuple[Any, LoadingOptions]:
    if isinstance(doc, str):
        return _document_load_by_url(
            loader,
            loadingOptions.fetcher.urljoin(baseuri, doc),
            loadingOptions,
            addl_metadata_fields=addl_metadata_fields,
        )

    if isinstance(doc, MutableMapping):
        addl_metadata: Final = {}
        if addl_metadata_fields is not None:
            for mf in addl_metadata_fields:
                if mf in doc:
                    addl_metadata[mf] = doc[mf]

        docuri: Final = baseuri
        if "$base" in doc:
            baseuri = doc["$base"]

        loadingOptions = LoadingOptions(
            copyfrom=loadingOptions,
            namespaces=doc.get("$namespaces", None),
            schemas=doc.get("$schemas", None),
            baseuri=doc.get("$base", None),
            addl_metadata=addl_metadata,
        )

        doc2: Final = copy.copy(doc)
        if "$namespaces" in doc2:
            doc2.pop("$namespaces")
        if "$schemas" in doc2:
            doc2.pop("$schemas")
        if "$base" in doc2:
            doc2.pop("$base")

        if "$graph" in doc2:
            loadingOptions.idx[baseuri] = (
                loader.load(doc2["$graph"], baseuri, loadingOptions),
                loadingOptions,
            )
        else:
            loadingOptions.idx[baseuri] = (
                loader.load(doc2, baseuri, loadingOptions, docRoot=baseuri),
                loadingOptions,
            )

        if docuri != baseuri:
            loadingOptions.idx[docuri] = loadingOptions.idx[baseuri]

        return loadingOptions.idx[baseuri]

    if isinstance(doc, MutableSequence):
        loadingOptions.idx[baseuri] = (
            loader.load(doc, baseuri, loadingOptions),
            loadingOptions,
        )
        return loadingOptions.idx[baseuri]

    raise ValidationException(
        "Expected URI string, MutableMapping or MutableSequence, got %s" % type(doc)
    )


def _document_load_by_url(
    loader: _Loader,
    url: str,
    loadingOptions: LoadingOptions,
    addl_metadata_fields: MutableSequence[str] | None = None,
) -> tuple[Any, LoadingOptions]:
    if url in loadingOptions.idx:
        return loadingOptions.idx[url]

    doc_url, frg = urldefrag(url)

    text: Final = loadingOptions.fetcher.fetch_text(doc_url)
    textIO: Final = StringIO(text)
    textIO.name = str(doc_url)
    yaml: Final = yaml_no_ts()
    result: Final = yaml.load(textIO)
    add_lc_filename(result, doc_url)

    loadingOptions = LoadingOptions(copyfrom=loadingOptions, fileuri=doc_url)

    _document_load(
        loader,
        result,
        doc_url,
        loadingOptions,
        addl_metadata_fields=addl_metadata_fields,
    )

    return loadingOptions.idx[url]


def _expand_url(
    url: str,
    base_url: str,
    loadingOptions: LoadingOptions,
    scoped_id: bool = False,
    vocab_term: bool = False,
    scoped_ref: int | None = None,
) -> str:
    if url in ("@id", "@type"):
        return url

    vocab = _vocab | loadingOptions.vocab
    if vocab_term and url in vocab:
        return url

    if bool(vocab) and ":" in url:
        prefix: Final = url.split(":")[0]
        if prefix in vocab:
            url = vocab[prefix] + url[len(prefix) + 1 :]

    split1: Final = urlsplit(url)

    if (
        (bool(split1.scheme) and split1.scheme in loadingOptions.fetcher.supported_schemes())
        or url.startswith("$(")
        or url.startswith("${")
    ):
        pass
    elif scoped_id and not bool(split1.fragment):
        splitbase1: Final = urlsplit(base_url)
        frg: str
        if bool(splitbase1.fragment):
            frg = splitbase1.fragment + "/" + split1.path
        else:
            frg = split1.path
        pt: Final = splitbase1.path if splitbase1.path != "" else "/"
        url = urlunsplit((splitbase1.scheme, splitbase1.netloc, pt, splitbase1.query, frg))
    elif scoped_ref is not None and not bool(split1.fragment):
        splitbase2: Final = urlsplit(base_url)
        sp = splitbase2.fragment.split("/")
        n = scoped_ref
        while n > 0 and len(sp) > 0:
            sp.pop()
            n -= 1
        sp.append(url)
        url = urlunsplit(
            (
                splitbase2.scheme,
                splitbase2.netloc,
                splitbase2.path,
                splitbase2.query,
                "/".join(sp),
            )
        )
    else:
        url = loadingOptions.fetcher.urljoin(base_url, url)

    if vocab_term:
        split2: Final = urlsplit(url)
        if bool(split2.scheme):
            if url in (rvocab := _rvocab | loadingOptions.rvocab):
                return rvocab[url]
        else:
            raise ValidationException(f"Term {url!r} not in vocabulary")

    return url


def _load_field(
    val: Any | None,
    fieldtype: "_Loader",
    baseuri: str,
    loadingOptions: LoadingOptions,
    lc: Any | None = None,
) -> Any:
    """Load field."""
    if isinstance(val, MutableMapping):
        if "$import" in val:
            if loadingOptions.fileuri is None:
                raise SchemaSaladException("Cannot load $import without fileuri")
            url1: Final = loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$import"])
            result, metadata = _document_load_by_url(
                fieldtype,
                url1,
                loadingOptions,
            )
            loadingOptions.imports.append(url1)
            return result
        if "$include" in val:
            if loadingOptions.fileuri is None:
                raise SchemaSaladException("Cannot load $import without fileuri")
            url2: Final = loadingOptions.fetcher.urljoin(loadingOptions.fileuri, val["$include"])
            val = loadingOptions.fetcher.fetch_text(url2)
            loadingOptions.includes.append(url2)
    return fieldtype.load(val, baseuri, loadingOptions, lc=lc)
