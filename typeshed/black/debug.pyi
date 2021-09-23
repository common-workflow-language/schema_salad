from typing import Iterator, TypeVar, Union

from black.nodes import Visitor as Visitor
from black.output import out as out
from black.parsing import lib2to3_parse as lib2to3_parse
from blib2to3.pytree import Leaf, Node

LN = Union[Leaf, Node]
T = TypeVar("T")

class DebugVisitor(Visitor[T]):
    tree_depth: int
    def visit_default(self, node: LN) -> Iterator[T]: ...
    @classmethod
    def show(cls, code: Union[str, Leaf, Node]) -> None: ...
