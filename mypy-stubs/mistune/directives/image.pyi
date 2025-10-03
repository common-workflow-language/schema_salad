from re import Match
from typing import Any

from ..block_parser import BlockParser
from ..core import BlockState
from ..markdown import Markdown
from ._base import BaseDirective, DirectivePlugin

__all__ = ["Image", "Figure"]

class Image(DirectivePlugin):
    NAME: str
    def parse(self, block: BlockParser, m: Match[str], state: BlockState) -> dict[str, Any]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...

class Figure(DirectivePlugin):
    NAME: str
    def parse_directive_content(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> list[dict[str, Any]] | None: ...
    def parse(self, block: BlockParser, m: Match[str], state: BlockState) -> dict[str, Any]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...
