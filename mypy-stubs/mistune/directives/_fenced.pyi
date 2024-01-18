from typing import List, Match, Optional

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
    def __init__(self, plugins: List[DirectivePlugin], markers: str = "`~") -> None: ...
    def parse_directive(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Optional[int]: ...
    def parse_fenced_code(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Optional[int]: ...
    def __call__(self, md: Markdown) -> None: ...
