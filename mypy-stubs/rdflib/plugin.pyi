from typing import Any, Generic, Iterator, Optional, Type, TypeVar, overload

from rdflib.exceptions import Error

class PluginException(Error):
    pass

#: A generic type variable for plugins
PluginT = TypeVar("PluginT")

class Plugin(Generic[PluginT]):
    name: str
    kind: Type[PluginT]
    module_path: str
    class_name: str
    _class: Optional[Type[PluginT]]

    def __init__(
        self, name: str, kind: Type[PluginT], module_path: str, class_name: str
    ) -> None: ...
    def getClass(self) -> Type[PluginT]: ...

def register(name: str, kind: Type[Any], module_path: str, class_name: str) -> None: ...
def get(name: str, kind: Type[PluginT]) -> Type[PluginT]: ...
@overload
def plugins(name: Optional[str] = ..., kind: Type[PluginT] = ...) -> Iterator[Plugin[PluginT]]: ...
@overload
def plugins(name: Optional[str] = ..., kind: None = ...) -> Iterator[Plugin[Any]]: ...
