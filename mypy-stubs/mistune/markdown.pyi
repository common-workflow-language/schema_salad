from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
    Union
)

from mistune._types import DataT, State
from mistune.block_parser import BlockParser
from mistune.inline_parser import InlineParser, RendererT
from mistune.renderers import BaseRenderer

Tokens = List[Dict[str, Any]]
ParseHook = Callable[[Markdown[DataT, RendererT], str, State], Tuple[str, State]]
RenderHook = Callable[[Markdown[DataT, RendererT], Tokens, State], Tokens]

class Markdown(Generic[DataT, RendererT]):
    renderer: BaseRenderer[DataT]
    inline: InlineParser[RendererT]
    block: BlockParser
    before_parse_hooks: List[ParseHook[DataT, RendererT]]
    before_render_hooks: List[RenderHook[DataT, RendererT]]
    after_render_hooks: List[RenderHook[DataT, RendererT]]

    def __init__(
        self,
        renderer: BaseRenderer[DataT],
        block: Optional[BlockParser] = None,
        inline: Optional[InlineParser[RendererT]] = None,
        plugins: Optional[Iterable[Union[ParseHook, RenderHook]]] = None,
    ) -> None: ...
    def before_parse(self, s: str, state: State) -> Tuple[str, State]: ...
    def before_render(self, tokens: Tokens, state: State) -> Tokens: ...
    def after_render(self, tokens: Tokens, state: State) -> Tokens: ...
    def parse(self, s: str, state: Optional[State] = None) -> str: ...
    def read(self, filepath: str, state: Optional[State] = None) -> str: ...
    def __call__(self, s: str) -> str: ...

def preprocess(s: str, state: State) -> Tuple[str, State]: ...
