from __future__ import absolute_import

import json
import os
from typing import IO, Any, AnyStr, Dict, List, Mapping, MutableSequence, Union

import six
from typing_extensions import Text  # pylint: disable=unused-import
# move to a regular typing import when Python 3.3-3.6 is no longer supported


def add_dictlist(di, key, val):  # type: (Dict, Any, Any) -> None
    if key not in di:
        di[key] = []
    di[key].append(val)


def aslist(l):  # type: (Any) -> MutableSequence
    """Convenience function to wrap single items and lists, and return lists unchanged."""

    if isinstance(l, MutableSequence):
        return l
    else:
        return [l]

# http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html

def flatten(l, ltypes=(list, tuple)):
    # type: (Any, Any) -> Any
    if l is None:
        return []
    if not isinstance(l, ltypes):
        return [l]

    ltype = type(l)
    lst = list(l)
    i = 0
    while i < len(lst):
        while isinstance(lst[i], ltypes):
            if not lst[i]:
                lst.pop(i)
                i -= 1
                break
            else:
                lst[i:i + 1] = lst[i]
        i += 1
    return ltype(lst)

# Check if we are on windows OS
def onWindows():
    # type: () -> (bool)
    return os.name == 'nt'

def convert_to_dict(j4):  # type: (Any) -> Any
    if isinstance(j4, Mapping):
        return {k: convert_to_dict(v) for k, v in j4.items()}
    elif isinstance(j4, MutableSequence):
        return [convert_to_dict(v) for v in j4]
    else:
        return j4

def json_dump(obj,       # type: Any
              fp,        # type: IO[str]
              **kwargs   # type: Any
             ):  # type: (...) -> None
    """ Force use of unicode. """
    if six.PY2:
        kwargs['encoding'] = 'utf-8'
    json.dump(convert_to_dict(obj), fp, **kwargs)


def json_dumps(obj,       # type: Any
               **kwargs   # type: Any
              ):  # type: (...) -> str
    """ Force use of unicode. """
    if six.PY2:
        kwargs['encoding'] = 'utf-8'
    return json.dumps(convert_to_dict(obj), **kwargs)
