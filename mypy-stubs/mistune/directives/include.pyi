from typing import Any, Dict, List, Match, Union

from ..block_parser import BlockParser as BlockParser
from ..core import BaseRenderer as BaseRenderer
from ..core import BlockState as BlockState
from ..markdown import Markdown as Markdown
from ._base import BaseDirective as BaseDirective
from ._base import DirectivePlugin as DirectivePlugin

class Include(DirectivePlugin):
    def parse(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...

def render_html_include(renderer: BaseRenderer, text: str, **attrs: Any) -> str: ...
