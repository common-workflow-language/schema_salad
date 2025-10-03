from collections.abc import Iterable
from typing import Any

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
        renderer: BaseRenderer | None = None,
        block: BlockParser | None = None,
        inline: InlineParser | None = None,
        plugins: Iterable[Plugin] | None = None,
    ) -> None: ...
    def use(self, plugin: Plugin) -> None: ...
    def render_state(self, state: BlockState) -> str | list[dict[str, Any]]: ...
    def parse(
        self, s: str, state: BlockState | None = None
    ) -> tuple[str | list[dict[str, Any]], BlockState]: ...
    def read(
        self, filepath: str, encoding: str = "utf-8", state: BlockState | None = None
    ) -> tuple[str | list[dict[str, Any]], BlockState]: ...
    def __call__(self, s: str) -> str | list[dict[str, Any]]: ...
