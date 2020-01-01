import itertools
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
    Pattern,
    Tuple,
    Type,
    Union,
)

import ruamel.yaml
from ruamel.yaml.comments import CommentedBase, CommentedMap, CommentedSeq


lineno_re = re.compile("^(.*?:[0-9]+:[0-9]+: )(( *)(.*))")


def regex_chunk(lines, regex):
    # type: (List[str], Pattern[str]) -> List[List[str]]
    lst = list(itertools.dropwhile(lambda x: not regex.match(x), lines))
    arr = []
    while lst:
        ret = [lst[0]] + list(
            itertools.takewhile(lambda x: not regex.match(x), lst[1:])
        )
        arr.append(ret)
        lst = list(itertools.dropwhile(lambda x: not regex.match(x), lst[1:]))
    return arr


def chunk_messages(message):  # type: (str) -> List[Tuple[int, str]]
    file_regex = re.compile(r"^(.+:\d+:\d+:)(\s+)(.+)$")
    item_regex = re.compile(r"^\s*\*\s+")
    arr = []
    for chun in regex_chunk(message.splitlines(), file_regex):
        fst = chun[0]
        mat = file_regex.match(fst)
        if mat:
            place = mat.group(1)
            indent = len(mat.group(2))

            lst = [mat.group(3)] + chun[1:]
            if [x for x in lst if item_regex.match(x)]:
                for item in regex_chunk(lst, item_regex):
                    msg = re.sub(item_regex, "", "\n".join(item))
                    arr.append((indent, place + " " + re.sub(r"[\n\s]+", " ", msg)))
            else:
                msg = re.sub(item_regex, "", "\n".join(lst))
                arr.append((indent, place + " " + re.sub(r"[\n\s]+", " ", msg)))
    return arr


def reformat_yaml_exception_message(message):  # type: (str) -> str
    line_regex = re.compile(r'^\s+in "(.+)", line (\d+), column (\d+)$')
    fname_regex = re.compile(r"^file://" + re.escape(os.getcwd()) + "/")
    msgs = message.splitlines()
    ret = []

    if len(msgs) == 3:
        msgs = msgs[1:]
        nblanks = 0
    elif len(msgs) == 4:
        c_msg = msgs[0]
        match = line_regex.match(msgs[1])
        if match:
            c_file, c_line, c_column = match.groups()
            c_file = re.sub(fname_regex, "", c_file)
            ret.append("{}:{}:{}: {}".format(c_file, c_line, c_column, c_msg))

        msgs = msgs[2:]
        nblanks = 2

    p_msg = msgs[0]
    match = line_regex.match(msgs[1])
    if match:
        p_file, p_line, p_column = match.groups()
        p_file = re.sub(fname_regex, "", p_file)
        ret.append(
            "{}:{}:{}:{} {}".format(p_file, p_line, p_column, " " * nblanks, p_msg)
        )
    return "\n".join(ret)


def _add_lc_filename(
    r, source
):  # type: (ruamel.yaml.comments.CommentedBase, AnyStr) -> None
    if isinstance(r, ruamel.yaml.comments.CommentedBase):
        r.lc.filename = source
    if isinstance(r, MutableSequence):
        for d in r:
            _add_lc_filename(d, source)
    elif isinstance(r, MutableMapping):
        for d in r.values():
            _add_lc_filename(d, source)


def relname(source):  # type: (str) -> str
    if source.startswith("file://"):
        source = source[7:]
        source = os.path.relpath(source)
    return source


def add_lc_filename(
    r, source
):  # type: (ruamel.yaml.comments.CommentedBase, str) -> None
    _add_lc_filename(r, relname(source))


def reflow_all(text, maxline=None):  # type: (str, Optional[int]) -> str
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


def reflow(text, maxline, shift=""):  # type: (str, int, str) -> str
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


def indent(
    v, nolead=False, shift="  ", bullet="  "
):  # type: (str, bool, str, str) -> str
    if nolead:
        return v.splitlines()[0] + "\n".join([shift + l for l in v.splitlines()[1:]])
    else:

        def lineno(i, l):  # type: (int, str) -> str
            r = lineno_re.match(l)
            if r is not None:
                return r.group(1) + (bullet if i == 0 else shift) + r.group(2)
            else:
                return (bullet if i == 0 else shift) + l

        return "\n".join([lineno(i, l) for i, l in enumerate(v.splitlines())])


def bullets(textlist, bul):  # type: (List[str], str) -> str
    if len(textlist) == 1:
        return textlist[0]
    else:
        return "\n".join(indent(t, bullet=bul) for t in textlist)


def strip_duplicated_lineno(text):  # type: (str) -> str
    """Same as `strip_dup_lineno` but without reflow"""
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


def strip_dup_lineno(text, maxline=None):  # type: (str, Optional[int]) -> str
    if maxline is None:
        maxline = int(os.environ.get("COLUMNS", "100"))
    pre = None
    msg = []
    maxno = 0
    for l in text.splitlines():
        g = lineno_re.match(l)
        if not g:
            continue
        maxno = max(maxno, len(g.group(1)))

    for l in text.splitlines():
        g = lineno_re.match(l)
        if not g:
            msg.append(l)
            continue
        if g.group(1) != pre:
            shift = maxno + len(g.group(3))
            g2 = reflow(g.group(2), maxline - shift, " " * shift)
            pre = g.group(1)
            msg.append(pre + " " * (maxno - len(g.group(1))) + g2)
        else:
            g2 = reflow(g.group(2), maxline - maxno, " " * (maxno + len(g.group(3))))
            msg.append(" " * maxno + g2)
    return "\n".join(msg)


def cmap(
    d,  # type: Union[int, float, str, str, Dict[str, Any], List[Dict[str, Any]]]
    lc=None,  # type: Optional[List[int]]
    fn=None,  # type: Optional[str]
):  # type: (...) -> Union[int, float, str, str, CommentedMap, CommentedSeq]
    if lc is None:
        lc = [0, 0, 0, 0]
    if fn is None:
        fn = "test"

    if isinstance(d, CommentedMap):
        fn = d.lc.filename if hasattr(d.lc, "filename") else fn
        for k, v in d.items():
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
        raise_type=str,  # type: Union[Type[str], Type[Exception]]
        include_traceback=False,  # type: bool
    ):  # type: (...) -> None
        self.item = item
        self.key = key
        self.raise_type = raise_type
        self.include_traceback = include_traceback

    def __enter__(self):  # type: () -> SourceLine
        return self

    def __exit__(
        self,
        exc_type,  # type: Any
        exc_value,  # type: Any
        tb,  # type: Any
    ):  # type: (...) -> None
        if not exc_value:
            return
        raise self.makeError(str(exc_value)) from exc_value

    def file(self):  # type: () -> Optional[str]
        if hasattr(self.item, "lc") and hasattr(self.item.lc, "filename"):
            return str(self.item.lc.filename)
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

    def makeLead(self):  # type: () -> str
        if self.file():
            lcol = self.start()
            line, col = lcol if lcol else ("", "")
            return "{}:{}:{}:".format(self.file(), line, col)
        else:
            return ""

    def makeError(self, msg):  # type: (str) -> Any
        if not isinstance(self.item, ruamel.yaml.comments.CommentedBase):
            return self.raise_type(msg)
        errs = []
        lead = self.makeLead()
        for m in msg.splitlines():
            if bool(lineno_re.match(m)):
                errs.append(m)
            else:
                errs.append("{} {}".format(lead, m))
        return self.raise_type("\n".join(errs))
