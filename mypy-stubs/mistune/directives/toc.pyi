from typing import Any, Dict, Match

from _typeshed import Incomplete

from ..block_parser import BlockParser as BlockParser
from ..core import BaseRenderer as BaseRenderer
from ..core import BlockState as BlockState
from ..markdown import Markdown as Markdown
from ..toc import normalize_toc_item as normalize_toc_item
from ..toc import render_toc_ul as render_toc_ul
from ._base import BaseDirective as BaseDirective
from ._base import DirectivePlugin as DirectivePlugin

class TableOfContents(DirectivePlugin):
    min_level: Incomplete
    max_level: Incomplete
    def __init__(self, min_level: int = 1, max_level: int = 3) -> None: ...
    def generate_heading_id(self, token: Dict[str, Any], index: int) -> str: ...
    def parse(self, block: BlockParser, m: Match[str], state: BlockState) -> Dict[str, Any]: ...
    def toc_hook(self, md: Markdown, state: BlockState) -> None: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...

def render_html_toc(
    renderer: BaseRenderer, title: str, collapse: bool = False, **attrs: Any
) -> str: ...
