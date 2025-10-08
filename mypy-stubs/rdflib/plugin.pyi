from collections.abc import Iterator
from typing import Any, Generic, TypeVar, overload

from rdflib.exceptions import Error

class PluginException(Error):
    pass

#: A generic type variable for plugins
PluginT = TypeVar("PluginT")

class Plugin(Generic[PluginT]):
    name: str
    kind: type[PluginT]
    module_path: str
    class_name: str
    _class: type[PluginT] | None

    def __init__(
        self, name: str, kind: type[PluginT], module_path: str, class_name: str
    ) -> None: ...
    def getClass(self) -> type[PluginT]: ...

def register(name: str, kind: type[Any], module_path: str, class_name: str) -> None: ...
def get(name: str, kind: type[PluginT]) -> type[PluginT]: ...
@overload
def plugins(name: str | None = ..., kind: type[PluginT] = ...) -> Iterator[Plugin[PluginT]]: ...
@overload
def plugins(name: str | None = ..., kind: None = ...) -> Iterator[Plugin[Any]]: ...
