from re import Match
from typing import Any

from ..block_parser import BlockParser as BlockParser
from ..core import BaseRenderer as BaseRenderer
from ..core import BlockState as BlockState
from ..markdown import Markdown as Markdown
from ._base import BaseDirective as BaseDirective
from ._base import DirectivePlugin as DirectivePlugin

class Include(DirectivePlugin):
    def parse(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> dict[str, Any] | list[dict[str, Any]]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...

def render_html_include(renderer: BaseRenderer, text: str, **attrs: Any) -> str: ...
