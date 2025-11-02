from typing import Match

from .block_parser import BlockParser as BlockParser
from .core import BlockState as BlockState
from .util import expand_leading_tab as expand_leading_tab
from .util import expand_tab as expand_tab
from .util import strip_end as strip_end

LIST_PATTERN: str

def parse_list(block: BlockParser, m: Match[str], state: BlockState) -> int: ...
