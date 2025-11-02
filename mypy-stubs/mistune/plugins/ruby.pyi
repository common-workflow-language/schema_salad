from typing import Match

from ..block_parser import BlockParser as BlockParser
from ..core import BaseRenderer as BaseRenderer
from ..core import BlockState as BlockState
from ..core import InlineState as InlineState
from ..core import Parser as Parser
from ..helpers import parse_link as parse_link
from ..helpers import parse_link_label as parse_link_label
from ..inline_parser import InlineParser as InlineParser
from ..markdown import Markdown as Markdown
from ..util import unikey as unikey

RUBY_PATTERN: str

def parse_ruby(inline: InlineParser, m: Match[str], state: InlineState) -> int: ...
def render_ruby(renderer: BaseRenderer, text: str, rt: str) -> str: ...
def ruby(md: Markdown) -> None: ...
