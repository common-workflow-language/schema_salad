from typing import Any, List, Optional, Sequence, Tuple

from .sourceline import SourceLine, reflow_all, strip_duplicated_lineno


def to_one_line_messages(exc):  # type: (SchemaSaladException) -> str
    return "\n".join((c.summary() for c in exc.leaves()))


class SchemaSaladException(Exception):
    """Base class for all schema-salad exceptions."""

    def __init__(
        self,
        msg,  # type: str
        sl=None,  # type: Optional[SourceLine]
        children=None,  # type: Optional[Sequence[SchemaSaladException]]
        bullet_for_children="",  # type: str
    ):  # type: (...) -> None
        super(SchemaSaladException, self).__init__(msg)
        self.message = self.args[0]

        # It will be set by its parent
        self.bullet = ""  # type: str

        def simplify(exc):  # type: (SchemaSaladException) -> List[SchemaSaladException]
            return [exc] if len(exc.message) else exc.children

        def with_bullet(exc, bullet):
            # type: (SchemaSaladException, str) -> SchemaSaladException
            if exc.bullet == "":
                exc.bullet = bullet
            return exc

        if children is None:
            self.children = []  # type: List[SchemaSaladException]
        elif len(children) <= 1:
            self.children = sum((simplify(c) for c in children), [])
        else:
            self.children = sum(
                (simplify(with_bullet(c, bullet_for_children)) for c in children), []
            )

        self.with_sourceline(sl)
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
        if sl and sl.file():
            self.file = sl.file()  # type: Optional[str]
            self.start = sl.start()  # type: Optional[Tuple[int, int]]
            self.end = sl.end()  # type: Optional[Tuple[int, int]]
        else:
            self.file = None
            self.start = None
            self.end = None
        return self

    def leaves(self):  # type: () -> List[SchemaSaladException]
        if len(self.children):
            return sum((c.leaves() for c in self.children), [])
        elif len(self.message):
            return [self]
        else:
            return []

    def prefix(self):  # type: () -> str
        if self.file:
            linecol = self.start if self.start else ("", "")  # type: Tuple[Any, Any]
            return "{}:{}:{}: ".format(self.file, linecol[0], linecol[1])
        else:
            return ""

    def summary(self, level=0, with_bullet=False):  # type: (int, bool) -> str
        indent_per_level = 2
        spaces = (level * indent_per_level) * " "
        bullet = self.bullet + " " if len(self.bullet) and with_bullet else ""
        return "{}{}{}{}".format(self.prefix(), spaces, bullet, self.message)

    def __str__(self):  # type: () -> str
        return str(self.pretty_str())

    def pretty_str(self, level=0):  # type: (int) -> str
        if len(self.message):
            my_summary = [self.summary(level, True)]
            next_level = level + 1
        else:
            my_summary = []
            next_level = level

        ret = "\n".join(
            (e for e in my_summary + [c.pretty_str(next_level) for c in self.children])
        )
        if level == 0:
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
