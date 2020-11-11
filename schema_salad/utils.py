import json
import os
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Mapping,
    MutableSequence,
    Tuple,
    TypeVar,
    Union,
)

import requests
from rdflib.graph import Graph
from ruamel.yaml.comments import CommentedMap, CommentedSeq

if TYPE_CHECKING:
    from .fetcher import Fetcher

ContextType = Dict[str, Union[Dict[str, Any], str, Iterable[str]]]
DocumentType = TypeVar("DocumentType", CommentedSeq, CommentedMap)
DocumentOrStrType = TypeVar("DocumentOrStrType", CommentedSeq, CommentedMap, str)
FieldType = TypeVar("FieldType", str, CommentedSeq, CommentedMap)
ResolveType = Union[int, float, str, CommentedMap, CommentedSeq, None]
ResolvedRefType = Tuple[ResolveType, CommentedMap]
IdxResultType = Union[CommentedMap, CommentedSeq, str, None]
IdxType = Dict[str, IdxResultType]
CacheType = Dict[str, Union[str, Graph, bool]]
FetcherCallableType = Callable[[CacheType, requests.sessions.Session], "Fetcher"]
AttachmentsType = Callable[[Union[CommentedMap, CommentedSeq]], bool]


def add_dictlist(di, key, val):  # type: (Dict[Any, Any], Any, Any) -> None
    if key not in di:
        di[key] = []
    di[key].append(val)


def aslist(thing):  # type: (Any) -> MutableSequence[Any]
    """
    Convenience function to wrap single items and lists.

    Return lists unchanged.
    """

    if isinstance(thing, MutableSequence):
        return thing
    else:
        return [thing]


# http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html


def flatten(thing, ltypes=(list, tuple)):
    # type: (Any, Any) -> Any
    if thing is None:
        return []
    if not isinstance(thing, ltypes):
        return [thing]

    ltype = type(thing)
    lst = list(thing)
    i = 0
    while i < len(lst):
        while isinstance(lst[i], ltypes):
            if not lst[i]:
                lst.pop(i)
                i -= 1
                break
            else:
                lst[i : i + 1] = lst[i]
        i += 1
    return ltype(lst)


# Check if we are on windows OS
def onWindows():
    # type: () -> (bool)
    return os.name == "nt"


def convert_to_dict(j4):  # type: (Any) -> Any
    if isinstance(j4, Mapping):
        return {k: convert_to_dict(v) for k, v in j4.items()}
    elif isinstance(j4, MutableSequence):
        return [convert_to_dict(v) for v in j4]
    else:
        return j4


def json_dump(
    obj,  # type: Any
    fp,  # type: IO[str]
    **kwargs  # type: Any
):  # type: (...) -> None
    """ Force use of unicode. """
    json.dump(convert_to_dict(obj), fp, **kwargs)


def json_dumps(
    obj,  # type: Any
    **kwargs  # type: Any
):  # type: (...) -> str
    """ Force use of unicode. """
    return json.dumps(convert_to_dict(obj), **kwargs)
