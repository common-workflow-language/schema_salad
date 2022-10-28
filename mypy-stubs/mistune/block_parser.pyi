from typing import (
    ClassVar,
    Iterator,
    List,
    Match,
    Optional,
    Pattern,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from typing_extensions import Literal, NotRequired, Required, TypeAlias, TypedDict

from mistune._types import DataT, State, Tokens
from mistune.inline_parser import InlineParser
from mistune.scanner import Matcher, ScannerParser

_ParsedBlock: TypeAlias = "ParsedBlock"
ParsedTypeT = TypeVar("ParsedTypeT")
ParsedBlock = TypedDict(
    "ParsedBlock",
    {
        "type": Required[ParsedTypeT],
        "blank": NotRequired[bool],
        "raw": NotRequired[str],
        "text": NotRequired[str],
        "params": NotRequired[Tuple[Union[int, str], ...]],
        "children": NotRequired[List[_ParsedBlock]],
    },
    total=False,
)

class BlockParser(ScannerParser):
    NEWLINE: Pattern[str]
    DEF_LINK: Pattern[str]
    AXT_HEADING: Pattern[str]
    SETEX_HEADING: Pattern[str]
    THEMATIC_BREAK: Pattern[str]
    INDENT_CODE: Pattern[str]
    FENCED_CODE: Pattern[str]
    BLOCK_QUOTE: Pattern[str]
    LIST_START: Pattern[str]
    BLOCK_HTML: Pattern[str]
    LIST_MAX_DEPTH: ClassVar[int]
    BLOCK_QUOTE_MAX_DEPTH: ClassVar[int]

    scanner_cls: ClassVar[Type[Matcher]] = Matcher
    block_quote_rules: List[str]
    list_rules = List[str]

    def __init__(self) -> None: ...
    def parse_newline(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["newline"]]: ...
    def parse_thematic_break(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["thematic_break"]]: ...
    def parse_indent_code(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["block_code"]]: ...
    def parse_fenced_code(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["block_code"]]: ...
    def tokenize_block_code(
        self, code: str, info: Tuple[str, ...], state: State
    ) -> ParsedBlock[Literal["block_code"]]: ...
    def parse_axt_heading(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["heading"]]: ...
    def parse_setex_heading(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["heading"]]: ...
    def tokenize_heading(
        self, text: str, level: int, state: State
    ) -> ParsedBlock[Literal["heading"]]: ...
    def get_block_quote_rules(self, depth: int) -> List[str]: ...
    def parse_block_quote(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["block_quote"]]: ...
    def get_list_rules(self, depth: int) -> List[str]: ...
    def parse_list_start(
        self, m: Match[str], state: State, string: str
    ) -> Tuple[ParsedBlock[Literal["list"]], int]: ...
    def parse_list_item(
        self, text: str, depth: int, state: State, rules: List[str]
    ) -> ParsedBlock[Literal["list_item"]]: ...
    def normalize_list_item_text(self, text: str) -> str: ...
    def parse_block_html(
        self, m: Match[str], state: State
    ) -> ParsedBlock[Literal["block_html"]]: ...
    def parse_def_link(self, m: Match[str], state: State) -> None: ...
    def parse_text(
        self, text: str, state: State
    ) -> Union[
        ParsedBlock[Literal["block_text"]],
        List[ParsedBlock[Literal["paragraph"]]]
    ]: ...
    def parse(
        self, s: str, state: State, rules: Optional[List[str]] = None
    ) -> Tokens: ...
    def render(self, tokens: Tokens, inline: InlineParser, state: State) -> DataT: ...
    def _iter_render(
        self, tokens: Tokens, inline: InlineParser, state: State
    ) -> Iterator[DataT]: ...

def cleanup_lines(s: str) -> str: ...
def expand_leading_tab(text: str) -> str: ...
