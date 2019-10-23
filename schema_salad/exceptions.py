from typing import Any, Sequence, Optional, Tuple
from typing_extensions import Text
from .sourceline import reflow_all, strip_duplicated_lineno, SourceLine


class SchemaSaladException(Exception):
    """Base class for all schema-salad exceptions."""

    def __init__(
        self,
        msg,  # type: Text
        sl=None,  # type: Optional[SourceLine]
        children=None,  # type: Optional[Sequence[SchemaSaladException]]
        bullet="",  # type: Text
    ):  # type: (...) -> None
        super(SchemaSaladException, self).__init__(msg)
        self.children = children if children else []
        self.bullet = bullet if len(self.children) > 1 else ""
        self.with_sourceline(sl)
        self.message = self.args[0]
        self.propagate_sourceline()

    def propagate_sourceline(self):  # type: () -> None
        if self.file is None:
            return
        for c in self.children:
            if c.file is None:
                c.file = self.file
                c.start = self.start
                c.end = self.end
                c.propagate_sourceline()

    def with_sourceline(
        self, sl
    ):  # type: (Optional[SourceLine]) -> SchemaSaladException
        if sl:
            self.file = sl.file()  # type: Optional[Text]
            self.start = (sl.line(), sl.column())  # type: Optional[Tuple[int, int]]
            self.end = (sl.line(), sl.column() + 1)  # type: Optional[Tuple[int, int]]
        else:
            self.file = None
            self.start = None
            self.end = None
        return self

    def prefix(self):  # type: () -> Text
        if self.file:
            linecol = self.start if self.start else ("", "")  # type: Tuple[Any, Any]
            return "{}:{}:{}: ".format(self.file, linecol[0], linecol[1])
        else:
            return ""

    def __str__(self):  # type: () -> str
        return str(self.pretty_str())

    def pretty_str(self, level=0, bullet=""):  # type: (int, Text) -> Text
        indent_per_level = 2
        ret = u""
        next_level = level + 1
        spaces = (level * indent_per_level) * " "
        if len(self.message):
            if self.file:
                ret = "{}{}{}{}".format(
                    self.prefix(),
                    spaces,
                    bullet + " " if len(bullet) else "",
                    self.message,
                )
            else:
                ret = "{}{}{}".format(
                    spaces, bullet + " " if len(bullet) else "", self.message
                )
        else:
            next_level = level

        ret = "\n".join(
            (
                e
                for e in [ret]
                + [c.pretty_str(next_level, self.bullet) for c in self.children]
                if len(e)
            )
        )
        if level == 0 and len(self.message):
            return strip_duplicated_lineno(reflow_all(ret))
        else:
            return ret


class SchemaException(SchemaSaladException):
    """Indicates error with the provided schema definition."""

    pass


class ValidationException(SchemaSaladException):
    """Indicates error with document against the provided schema."""

    pass


class ClassValidationException(ValidationException):
    pass
