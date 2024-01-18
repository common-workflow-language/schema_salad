from typing import Any, Dict, List, Match, Optional

from ..block_parser import BlockParser
from ..core import BlockState
from ..markdown import Markdown
from ._base import BaseDirective, DirectivePlugin

__all__ = ["Image", "Figure"]

class Image(DirectivePlugin):
    NAME: str
    def parse(self, block: BlockParser, m: Match[str], state: BlockState) -> Dict[str, Any]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...

class Figure(DirectivePlugin):
    NAME: str
    def parse_directive_content(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Optional[List[Dict[str, Any]]]: ...
    def parse(self, block: BlockParser, m: Match[str], state: BlockState) -> Dict[str, Any]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...
