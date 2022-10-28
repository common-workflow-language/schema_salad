from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
)
from typing_extensions import TypeAlias

from mistune._types import DataT, State
from mistune.block_parser import BlockParser
from mistune.inline_parser import InlineParser
from mistune.renderers import BaseRenderer

Tokens = List[Dict[str, Any]]
MarkdownT: TypeAlias = "Markdown"
ParseHook = Callable[[MarkdownT[DataT], str, State], Tuple[str, State]]
RenderHook = Callable[[MarkdownT[DataT], Tokens, State], Tokens]

class Markdown(Generic[DataT]):
    renderer: BaseRenderer[DataT]
    inline: InlineParser
    block: BlockParser
    before_parse_hooks: List[ParseHook[DataT]]
    before_render_hooks: List[RenderHook[DataT]]
    after_render_hooks: List[RenderHook[DataT]]

    def __init__(
        self,
        renderer: BaseRenderer[DataT],
        block: Optional[BlockParser] = None,
        inline: Optional[InlineParser] = None,
        plugins: Optional[List[str]] = None,
    ) -> None: ...
    def before_parse(self, s: str, state: State) -> Tuple[str, State]: ...
    def before_render(self, tokens: Tokens, state: State) -> Tokens: ...
    def after_render(self, tokens: Tokens, state: State) -> Tokens: ...
    def parse(self, s: str, state: Optional[State] = None) -> str: ...
    def read(self, filepath: str, state: Optional[State] = None) -> str: ...
    def __call__(self, s: str) -> str: ...

def preprocess(s: str, state: State) -> Tuple[str, State]: ...
