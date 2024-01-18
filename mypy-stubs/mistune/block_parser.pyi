from typing import ClassVar, Dict, Iterable, List, Match, Optional, Pattern, Tuple

from .core import BlockState as BlockState
from .core import Parser as Parser
from .helpers import BLOCK_TAGS as BLOCK_TAGS
from .helpers import HTML_ATTRIBUTES as HTML_ATTRIBUTES
from .helpers import HTML_TAGNAME as HTML_TAGNAME
from .helpers import LINK_LABEL as LINK_LABEL
from .helpers import PRE_TAGS as PRE_TAGS
from .helpers import parse_link_href as parse_link_href
from .helpers import parse_link_title as parse_link_title
from .helpers import unescape_char as unescape_char
from .list_parser import LIST_PATTERN as LIST_PATTERN
from .list_parser import parse_list as parse_list
from .util import escape_url as escape_url
from .util import expand_leading_tab as expand_leading_tab
from .util import expand_tab as expand_tab
from .util import unikey as unikey

class BlockParser(Parser[BlockState]):
    state_cls = BlockState
    BLANK_LINE: Pattern[str]
    RAW_HTML: str
    BLOCK_HTML: str
    SPECIFICATION: ClassVar[Dict[str, str]]
    DEFAULT_RULES: ClassVar[Iterable[str]]
    block_quote_rules: List[str]
    list_rules: List[str]
    max_nested_level: int
    def __init__(
        self,
        block_quote_rules: Optional[List[str]] = None,
        list_rules: Optional[List[str]] = None,
        max_nested_level: int = 6,
    ) -> None: ...
    def parse_blank_line(self, m: Match[str], state: BlockState) -> int: ...
    def parse_thematic_break(self, m: Match[str], state: BlockState) -> int: ...
    def parse_indent_code(self, m: Match[str], state: BlockState) -> int: ...
    def parse_fenced_code(self, m: Match[str], state: BlockState) -> Optional[int]: ...
    def parse_atx_heading(self, m: Match[str], state: BlockState) -> int: ...
    def parse_setex_heading(self, m: Match[str], state: BlockState) -> Optional[int]: ...
    def parse_ref_link(self, m: Match[str], state: BlockState) -> Optional[int]: ...
    def extract_block_quote(
        self, m: Match[str], state: BlockState
    ) -> Tuple[str, Optional[int]]: ...
    def parse_block_quote(self, m: Match[str], state: BlockState) -> int: ...
    def parse_list(self, m: Match[str], state: BlockState) -> int: ...
    def parse_block_html(self, m: Match[str], state: BlockState) -> Optional[int]: ...
    def parse_raw_html(self, m: Match[str], state: BlockState) -> Optional[int]: ...
    def parse(self, state: BlockState, rules: Optional[List[str]] = None) -> None: ...
