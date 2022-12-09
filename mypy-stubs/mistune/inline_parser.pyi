from typing import (
    ClassVar,
    Generic,
    Iterator,
    List,
    Match,
    Optional,
    Pattern,
    Tuple,
    TypeVar,
    Union,
)

from mistune._types import State
from mistune.renderers import AstRenderer, DataT, HTMLRenderer
from mistune.scanner import ScannerParser
from mistune.util import ESCAPE_TEXT
from typing_extensions import Literal

HTML_TAGNAME: str
HTML_ATTRIBUTES: str
ESCAPE_CHAR: Pattern[str]
LINK_TEXT: str
LINK_LABEL: str

# Union[BaseRenderer[DataT], AstRenderer, HTMLRenderer]
RendererT = TypeVar("RendererT", bound=Union[AstRenderer, HTMLRenderer])

class InlineParser(ScannerParser, Generic[RendererT]):
    ESCAPE: ClassVar[str] = ESCAPE_TEXT
    AUTO_LINK: ClassVar[str]
    STD_LINK: ClassVar[str]
    REF_LINK: ClassVar[str]
    REF_LINK2: ClassVar[str]
    ASTERISK_EMPHASIS: ClassVar[str]
    UNDERSCORE_EMPHASIS: ClassVar[str]
    CODESPAN: ClassVar[str]
    LINEBREAK: ClassVar[str]
    INLINE_HTML: ClassVar[str]
    RULE_NAMES: ClassVar[Tuple[str, ...]]

    renderer: RendererT

    def __init__(self, renderer: RendererT, hard_wrap: bool = False) -> None: ...
    def parse_escape(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["text"], str]: ...
    def parse_autolink(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["link"], str, str]: ...
    def parse_std_link(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["link"], str, str, str]: ...
    def parse_ref_link(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["link"], str, str, str]: ...
    def parse_ref_link2(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["link"], str, str, str]: ...
    def tokenize_link(
        self, line: str, link: str, text: str, title: str, state: State
    ) -> Tuple[Literal["link"], str, str, str]: ...
    def parse_asterisk_emphasis(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["strong", "emphasis"], str]: ...
    def parse_underscore_emphasis(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["strong", "emphasis"], str]: ...
    def tokenize_emphasis(self, m: Match[str], state: State) -> Tuple[str, str]: ...
    def parse_codespan(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["codespan"], str]: ...
    def parse_linebreak(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["linebreak"], str]: ...
    def parse_inline_html(
        self, m: Match[str], state: State
    ) -> Tuple[Literal["inline_html"], str]: ...
    def parse_text(self, text: str, state: State) -> Tuple[Literal["text"], str]: ...
    def parse(
        self, s: str, state: State, rules: Optional[List[str]]
    ) -> Iterator[DataT]: ...
    def render(
        self, s: str, state: State, rules: Optional[List[str]]
    ) -> Union[DataT, List[DataT]]: ...
    def __call__(self, s: str, state: State) -> Union[DataT, List[DataT]]: ...
