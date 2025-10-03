from re import Match

from _typeshed import Incomplete

from ..block_parser import BlockParser
from ..core import BlockState
from ..markdown import Markdown
from ._base import BaseDirective, DirectiveParser, DirectivePlugin

__all__ = ["FencedDirective"]

class FencedParser(DirectiveParser):
    name: str
    @staticmethod
    def parse_type(m: Match[str]) -> str: ...
    @staticmethod
    def parse_title(m: Match[str]) -> str: ...
    @staticmethod
    def parse_content(m: Match[str]) -> str: ...

class FencedDirective(BaseDirective):
    parser = FencedParser
    markers: Incomplete
    directive_pattern: Incomplete
    def __init__(self, plugins: list[DirectivePlugin], markers: str = "`~") -> None: ...
    def parse_directive(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> int | None: ...
    def parse_fenced_code(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> int | None: ...
    def __call__(self, md: Markdown) -> None: ...
