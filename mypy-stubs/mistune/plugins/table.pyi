import sys
from typing import Match

from mistune._types import State
from mistune.block_parser import BlockParser, ParsedBlock
from mistune.inline_parser import RendererT
from mistune.markdown import Markdown
from mistune.renderers import DataT
from typing_extensions import Literal

if sys.version_info >= (3, 7):
    ParsedBlockTable = ParsedBlock[Literal["paragraph"]]
else:
    ParsedBlockTable = ParsedBlock

def parse_table(self: BlockParser, m: Match[str], state: State) -> ParsedBlockTable: ...
def plugin_table(md: Markdown[DataT, RendererT]) -> None: ...
