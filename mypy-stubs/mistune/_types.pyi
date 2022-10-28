from typing import Any, Callable, Dict, List, TypeVar, Union

# type aliases shared across modules
DataT = TypeVar("DataT")
State = Dict[str, Any]  # extra options that work with a given 'ParsedType'
Tokens = List[str]

RenderMethod = Union[
    Callable[[], DataT],  # blank
    Callable[[DataT, Any], DataT],
]
