from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from _typeshed import Incomplete

from .block_parser import BlockParser as BlockParser
from .core import BaseRenderer as BaseRenderer
from .core import BlockState as BlockState
from .inline_parser import InlineParser as InlineParser
from .plugins import Plugin as Plugin

class Markdown:
    renderer: Incomplete
    block: Incomplete
    inline: Incomplete
    before_parse_hooks: Incomplete
    before_render_hooks: Incomplete
    after_render_hooks: Incomplete
    def __init__(
        self,
        renderer: Optional[BaseRenderer] = None,
        block: Optional[BlockParser] = None,
        inline: Optional[InlineParser] = None,
        plugins: Optional[Iterable[Plugin]] = None,
    ) -> None: ...
    def use(self, plugin: Plugin) -> None: ...
    def render_state(self, state: BlockState) -> Union[str, List[Dict[str, Any]]]: ...
    def parse(
        self, s: str, state: Optional[BlockState] = None
    ) -> Tuple[Union[str, List[Dict[str, Any]]], BlockState]: ...
    def read(
        self, filepath: str, encoding: str = "utf-8", state: Optional[BlockState] = None
    ) -> Tuple[Union[str, List[Dict[str, Any]]], BlockState]: ...
    def __call__(self, s: str) -> Union[str, List[Dict[str, Any]]]: ...
