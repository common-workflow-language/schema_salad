
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Match,
    Optional,
    Pattern,
    Sequence,
    Tuple,
    Type,
)

Tokens = List[Dict[str, Any]]

from mistune.inline_parser import InlineParser

class Markdown:
    renderer: InlineParser
    inline = ...  # type: InlineLexer
    block = ...  # type: BlockLexer
    footnotes = ...  # type: List[Dict[str, Any]]
    tokens = ...  # type: Tokens
    def __init__(
        self,
        renderer: Optional[Renderer] = ...,
        inline: Optional[InlineLexer] = ...,
        block: Optional[BlockLexer] = ...,
        **kwargs: Any
    ) -> None: ...
    def __call__(self, text: str) -> str: ...
    def render(self, text: str) -> str: ...
    def parse(self, text: str) -> str: ...
    token = ...  # type: Dict[str, Any]
    def pop(self) -> Optional[Dict[str, Any]]: ...
    def peek(self) -> Optional[Dict[str, Any]]: ...
    def output(self, text: str, rules: Optional[Sequence[str]] = ...) -> str: ...
    def tok(self) -> str: ...
    def tok_text(self) -> str: ...
    def output_newline(self) -> str: ...
    def output_hrule(self) -> str: ...
    def output_heading(self) -> str: ...
    def output_code(self) -> str: ...
    def output_table(self) -> str: ...
    def output_block_quote(self) -> str: ...
    def output_list(self) -> str: ...
    def output_list_item(self) -> str: ...
    def output_loose_item(self) -> str: ...
    def output_footnote(self) -> str: ...
    def output_close_html(self) -> str: ...
    def output_open_html(self) -> str: ...
    def output_paragraph(self) -> str: ...
    def output_text(self) -> str: ...

def markdown(text: str, escape: bool = ..., **kwargs: Any) -> str: ...
