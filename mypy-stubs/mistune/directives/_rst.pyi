from typing import Match, Optional

from ..block_parser import BlockParser
from ..core import BlockState
from ..markdown import Markdown
from ._base import BaseDirective, DirectiveParser

__all__ = ["RSTDirective"]

class RSTParser(DirectiveParser):
    name: str
    @staticmethod
    def parse_type(m: Match[str]) -> str: ...
    @staticmethod
    def parse_title(m: Match[str]) -> str: ...
    @staticmethod
    def parse_content(m: Match[str]) -> str: ...

class RSTDirective(BaseDirective):
    parser = RSTParser
    directive_pattern: str
    def parse_directive(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Optional[int]: ...
    def __call__(self, markdown: Markdown) -> None: ...
