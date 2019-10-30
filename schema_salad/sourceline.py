from __future__ import absolute_import

import os
import re
from typing import (
    Any,
    AnyStr,
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Tuple,
    Union,
)

import six
from typing_extensions import Text  # pylint: disable=unused-import

import ruamel.yaml
from ruamel.yaml.comments import CommentedBase, CommentedMap, CommentedSeq

# move to a regular typing import when Python 3.3-3.6 is no longer supported


lineno_re = re.compile(u"^(.*?:[0-9]+:[0-9]+: )(( *)(.*))")


def _add_lc_filename(
    r, source
):  # type: (ruamel.yaml.comments.CommentedBase, AnyStr) -> None
    if isinstance(r, ruamel.yaml.comments.CommentedBase):
        r.lc.filename = source
    if isinstance(r, MutableSequence):
        for d in r:
            _add_lc_filename(d, source)
    elif isinstance(r, MutableMapping):
        for d in six.itervalues(r):
            _add_lc_filename(d, source)


def relname(source):  # type: (Text) -> Text
    if source.startswith("file://"):
        source = source[7:]
        source = os.path.relpath(source)
    return source


def add_lc_filename(
    r, source
):  # type: (ruamel.yaml.comments.CommentedBase, Text) -> None
    _add_lc_filename(r, relname(source))


def reflow_all(text, maxline=None):  # type: (Text, Optional[int]) -> Text
    if maxline is None:
        maxline = int(os.environ.get("COLUMNS", "100"))
    maxno = 0
    for l in text.splitlines():
        g = lineno_re.match(l)
        if not g:
            continue
        maxno = max(maxno, len(g.group(1)))
    maxno_text = maxline - maxno
    msg = []
    for l in text.splitlines():
        g = lineno_re.match(l)
        if not g:
            msg.append(l)
            continue
        pre = g.group(1)
        reflowed = reflow(g.group(2), maxno_text, g.group(3)).splitlines()
        msg.extend([pre.ljust(maxno, " ") + r for r in reflowed])
    return "\n".join(msg)


def reflow(text, maxline, shift=""):  # type: (Text, int, Text) -> Text
    if maxline < 20:
        maxline = 20
    if len(text) > maxline:
        sp = text.rfind(" ", 0, maxline)
        if sp < 1:
            sp = text.find(" ", sp + 1)
            if sp == -1:
                sp = len(text)
        if sp < len(text):
            return "{}\n{}{}".format(
                text[0:sp], shift, reflow(text[sp + 1 :], maxline, shift)
            )
    return text


def strip_duplicated_lineno(text):  # type: (Text) -> Text
    """Returns lines without the duplicated lineno part like `uniq` command """
    pre = None
    msg = []
    for l in text.splitlines():
        g = lineno_re.match(l)
        if not g:
            msg.append(l)
            continue
        elif g.group(1) != pre:
            msg.append(l)
            pre = g.group(1)
        else:
            msg.append(" " * len(g.group(1)) + g.group(2))
    return "\n".join(msg)


def cmap(
    d,  # type: Union[int, float, str, Text, Dict[Text, Any], List[Dict[Text, Any]]]
    lc=None,  # type: Optional[List[int]]
    fn=None,  # type: Optional[Text]
):  # type: (...) -> Union[int, float, str, Text, CommentedMap, CommentedSeq]
    if lc is None:
        lc = [0, 0, 0, 0]
    if fn is None:
        fn = "test"

    if isinstance(d, CommentedMap):
        fn = d.lc.filename if hasattr(d.lc, "filename") else fn
        for k, v in six.iteritems(d):
            if d.lc.data is not None and k in d.lc.data:
                d[k] = cmap(v, lc=d.lc.data[k], fn=fn)
            else:
                d[k] = cmap(v, lc, fn=fn)
        return d
    if isinstance(d, CommentedSeq):
        fn = d.lc.filename if hasattr(d.lc, "filename") else fn
        for k2, v2 in enumerate(d):
            if d.lc.data is not None and k2 in d.lc.data:
                d[k2] = cmap(v2, lc=d.lc.data[k2], fn=fn)
            else:
                d[k2] = cmap(v2, lc, fn=fn)
        return d
    if isinstance(d, MutableMapping):
        cm = CommentedMap()
        for k in sorted(d.keys()):
            v = d[k]
            if isinstance(v, CommentedBase):
                uselc = [v.lc.line, v.lc.col, v.lc.line, v.lc.col]
                vfn = v.lc.filename if hasattr(v.lc, "filename") else fn
            else:
                uselc = lc
                vfn = fn
            cm[k] = cmap(v, lc=uselc, fn=vfn)
            cm.lc.add_kv_line_col(k, uselc)
            cm.lc.filename = fn
        return cm
    if isinstance(d, MutableSequence):
        cs = CommentedSeq()
        for k3, v3 in enumerate(d):
            if isinstance(v3, CommentedBase):
                uselc = [v3.lc.line, v3.lc.col, v3.lc.line, v3.lc.col]
                vfn = v3.lc.filename if hasattr(v3.lc, "filename") else fn
            else:
                uselc = lc
                vfn = fn
            cs.append(cmap(v3, lc=uselc, fn=vfn))
            cs.lc.add_kv_line_col(k3, uselc)
            cs.lc.filename = fn
        return cs
    else:
        return d


class SourceLine(object):
    def __init__(
        self,
        item,  # type: Any
        key=None,  # type: Optional[Any]
    ):  # type: (...) -> None
        self.item = item
        self.key = key

    def file(self):  # type: () -> Optional[Text]
        if hasattr(self.item, "lc") and hasattr(self.item.lc, "filename"):
            return Text(self.item.lc.filename)
        else:
            return None

    def start(self):  # type: () -> Optional[Tuple[int, int]]
        if self.file() is None:
            return None
        elif (
            self.key is None
            or self.item.lc.data is None
            or self.key not in self.item.lc.data
        ):
            return ((self.item.lc.line or 0) + 1, (self.item.lc.col or 0) + 1)
        else:
            return (
                (self.item.lc.data[self.key][0] or 0) + 1,
                (self.item.lc.data[self.key][1] or 0) + 1,
            )

    def end(self):  # type: () -> Optional[Tuple[int, int]]
        return None

    def makeLead(self):  # type: () -> Text
        if self.file():
            lcol = self.start()
            line, col = lcol if lcol else ("", "")
            return "{}:{}:{}:".format(self.file(), line, col)
        else:
            return ""
