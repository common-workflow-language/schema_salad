import sys
from typing import (
    Any,
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

from mistune._types import State, Tokens
from mistune.inline_parser import InlineParser, RendererT
from mistune.renderers import DataT
from mistune.scanner import Matcher, ScannerParser
from typing_extensions import Literal, NotRequired, Required, TypeAlias, TypedDict

ParsedBlockType = Literal[
    # base block parsers
    "heading",
    "newline",
    "thematic_break",
    "block_code",
    "block_html",
    "block_quote",
    "block_text",
    "list",
    "list_item",
    "paragraph",
    # plugin 'table'
    "table",
    "table_head",
    "table_body",
    "table_cell",
    "table_row",
    # plugin 'url'
    "url",
]
_ParsedBlock: TypeAlias = "ParsedBlock"
if sys.version_info >= (3, 7):
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
    ParsedBlockHeading = ParsedBlock[Literal["heading"]]
    ParsedBlockNewline = ParsedBlock[Literal["newline"]]
    ParsedBlockThematicBreak = ParsedBlock[Literal["thematic_break"]]
    ParsedBlockBlockCode = ParsedBlock[Literal["block_code"]]
    ParsedBlockBlockHTML = ParsedBlock[Literal["block_html"]]
    ParsedBlockBlockQuote = ParsedBlock[Literal["block_quote"]]
    ParsedBlockBlockText = ParsedBlock[Literal["block_text"]]
    ParsedBlockList = ParsedBlock[Literal["list"]]
    ParsedBlockListItem = ParsedBlock[Literal["list_item"]]
    ParsedBlockParagraph = ParsedBlock[Literal["paragraph"]]
else:  # python 3.6  # no TypedDict+Generic support with TypeVar
    ParsedBlock = TypedDict(
        "ParsedBlock",
        {
            # best we can do is define an 'AnyOf' allowed literals
            # we cannot provide explicitly which literal is returned each time
            "type": Required[ParsedBlockType],
            "blank": NotRequired[bool],
            "raw": NotRequired[str],
            "text": NotRequired[str],
            "params": NotRequired[Tuple[Union[int, str], ...]],
            "children": NotRequired[List[_ParsedBlock]],
        },
        total=False,
    )
    ParsedBlockHeading = ParsedBlock
    ParsedBlockNewline = ParsedBlock
    ParsedBlockThematicBreak = ParsedBlock
    ParsedBlockBlockCode = ParsedBlock
    ParsedBlockBlockHTML = ParsedBlock
    ParsedBlockBlockQuote = ParsedBlock
    ParsedBlockBlockText = ParsedBlock
    ParsedBlockList = ParsedBlock
    ParsedBlockListItem = ParsedBlock
    ParsedBlockParagraph = ParsedBlock

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
    def parse_newline(self, m: Match[str], state: State) -> ParsedBlockNewline: ...
    def parse_thematic_break(
        self, m: Match[str], state: State
    ) -> ParsedBlockThematicBreak: ...
    def parse_indent_code(
        self, m: Match[str], state: State
    ) -> ParsedBlockBlockCode: ...
    def parse_fenced_code(
        self, m: Match[str], state: State
    ) -> ParsedBlockBlockCode: ...
    def tokenize_block_code(
        self, code: str, info: Tuple[str, ...], state: State
    ) -> ParsedBlockBlockCode: ...
    def parse_axt_heading(self, m: Match[str], state: State) -> ParsedBlockHeading: ...
    def parse_setex_heading(
        self, m: Match[str], state: State
    ) -> ParsedBlockHeading: ...
    def tokenize_heading(
        self, text: str, level: int, state: State
    ) -> ParsedBlockHeading: ...
    def get_block_quote_rules(self, depth: int) -> List[str]: ...
    def parse_block_quote(
        self, m: Match[str], state: State
    ) -> ParsedBlockBlockQuote: ...
    def get_list_rules(self, depth: int) -> List[str]: ...
    def parse_list_start(
        self, m: Match[str], state: State, string: str
    ) -> Tuple[ParsedBlockList, int]: ...
    def parse_list_item(
        self, text: str, depth: int, state: State, rules: List[str]
    ) -> ParsedBlockListItem: ...
    def normalize_list_item_text(self, text: str) -> str: ...
    def parse_block_html(self, m: Match[str], state: State) -> ParsedBlockBlockHTML: ...
    def parse_def_link(self, m: Match[str], state: State) -> None: ...
    def parse_text(
        self, text: str, state: State
    ) -> Union[ParsedBlockBlockText, List[ParsedBlockParagraph]]: ...
    def parse(
        self, s: str, state: State, rules: Optional[List[str]] = None
    ) -> Tokens: ...
    def render(
        self, tokens: Tokens, inline: InlineParser[RendererT], state: State
    ) -> Any: ...  # technically DataT, but defined by 'inline.renderer.finalize'
    def _iter_render(
        self, tokens: Tokens, inline: InlineParser[RendererT], state: State
    ) -> Iterator[DataT]: ...

def cleanup_lines(s: str) -> str: ...
def expand_leading_tab(text: str) -> str: ...
