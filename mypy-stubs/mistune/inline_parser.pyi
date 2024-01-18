from typing import (
    Any,
    ClassVar,
    Dict,
    Iterable,
    List,
    Match,
    MutableMapping,
    Optional,
    Pattern,
)

from .core import InlineState as InlineState
from .core import Parser as Parser
from .helpers import HTML_ATTRIBUTES as HTML_ATTRIBUTES
from .helpers import HTML_TAGNAME as HTML_TAGNAME
from .helpers import PREVENT_BACKSLASH as PREVENT_BACKSLASH
from .helpers import PUNCTUATION as PUNCTUATION
from .helpers import parse_link as parse_link
from .helpers import parse_link_label as parse_link_label
from .helpers import parse_link_text as parse_link_text
from .helpers import unescape_char as unescape_char
from .util import escape as escape
from .util import escape_url as escape_url
from .util import unikey as unikey

PAREN_END_RE: Pattern[str]
AUTO_EMAIL: str
INLINE_HTML: str
EMPHASIS_END_RE: Dict[str, Pattern[str]]

class InlineParser(Parser[InlineState]):
    sc_flag: int
    state_cls = InlineState
    STD_LINEBREAK: str
    HARD_LINEBREAK: str
    SPECIFICATION: ClassVar[Dict[str, str]]
    DEFAULT_RULES: ClassVar[Iterable[str]]
    hard_wrap: bool
    def __init__(self, hard_wrap: bool = False) -> None: ...
    def parse_escape(self, m: Match[str], state: InlineState) -> int: ...
    def parse_link(self, m: Match[str], state: InlineState) -> Optional[int]: ...
    def parse_auto_link(self, m: Match[str], state: InlineState) -> int: ...
    def parse_auto_email(self, m: Match[str], state: InlineState) -> int: ...
    def parse_emphasis(self, m: Match[str], state: InlineState) -> int: ...
    def parse_codespan(self, m: Match[str], state: InlineState) -> int: ...
    def parse_linebreak(self, m: Match[str], state: InlineState) -> int: ...
    def parse_softbreak(self, m: Match[str], state: InlineState) -> int: ...
    def parse_inline_html(self, m: Match[str], state: InlineState) -> int: ...
    def process_text(self, text: str, state: InlineState) -> None: ...
    def parse(self, state: InlineState) -> List[Dict[str, Any]]: ...
    def precedence_scan(
        self, m: Match[str], state: InlineState, end_pos: int, rules: Optional[List[str]] = None
    ) -> Optional[int]: ...
    def render(self, state: InlineState) -> List[Dict[str, Any]]: ...
    def __call__(self, s: str, env: MutableMapping[str, Any]) -> List[Dict[str, Any]]: ...
