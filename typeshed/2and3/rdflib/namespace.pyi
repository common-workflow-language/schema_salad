# Stubs for rdflib.namespace (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Optional

class Namespace(str):
    __doc__: Any = ...
    def __new__(cls, value: Any): ...
    @property
    def title(self): ...
    def term(self, name: Any): ...
    def __getitem__(self, key: Any, default: Optional[Any] = ...): ...
    def __getattr__(self, name: Any): ...

class URIPattern(str):
    __doc__: Any = ...
    def __new__(cls, value: Any): ...
    def __mod__(self, *args: Any, **kwargs: Any): ...
    def format(self, *args: Any, **kwargs: Any): ...

class ClosedNamespace:
    uri: Any = ...
    def __init__(self, uri: Any, terms: Any) -> None: ...
    def term(self, name: Any): ...
    def __getitem__(self, key: Any, default: Optional[Any] = ...): ...
    def __getattr__(self, name: Any): ...

class _RDFNamespace(ClosedNamespace):
    def __init__(self) -> None: ...
    def term(self, name: Any): ...

RDF: Any
RDFS: Any
OWL: Any
XSD: Any
SKOS: Any
DOAP: Any
FOAF: Any
DC: Any
DCTERMS: Any
VOID: Any

class NamespaceManager:
    graph: Any = ...
    def __init__(self, graph: Any) -> None: ...
    def reset(self) -> None: ...
    store: Any = ...
    def qname(self, uri: Any): ...
    def normalizeUri(self, rdfTerm: Any): ...
    def compute_qname(self, uri: Any, generate: bool = ...): ...
    def bind(self, prefix: Any, namespace: Any, override: bool = ..., replace: bool = ...) -> None: ...
    def namespaces(self) -> None: ...
    def absolutize(self, uri: Any, defrag: int = ...): ...

def is_ncname(name: Any): ...

XMLNS: str

def split_uri(uri: Any): ...
