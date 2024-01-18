from typing import Any, Dict, Match

from _typeshed import Incomplete

from ..block_parser import BlockParser as BlockParser
from ..core import BlockState as BlockState
from ..markdown import Markdown as Markdown
from ._base import BaseDirective as BaseDirective
from ._base import DirectivePlugin as DirectivePlugin

class Admonition(DirectivePlugin):
    SUPPORTED_NAMES: Incomplete
    def parse(self, block: BlockParser, m: Match[str], state: BlockState) -> Dict[str, Any]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...

def render_admonition(self, text: str, name: str, **attrs: Any) -> str: ...
def render_admonition_title(self, text: str) -> str: ...
def render_admonition_content(self, text: str) -> str: ...
