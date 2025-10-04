from collections.abc import Iterable
from typing import Any, Literal, TypeAlias

from .block_parser import BlockParser as BlockParser
from .core import BaseRenderer as BaseRenderer
from .core import BlockState as BlockState
from .core import InlineState as InlineState
from .inline_parser import InlineParser as InlineParser
from .markdown import Markdown as Markdown
from .plugins import PluginRef
from .renderers.html import HTMLRenderer as HTMLRenderer
from .util import escape as escape
from .util import escape_url as escape_url
from .util import safe_entity as safe_entity
from .util import unikey as unikey

__all__ = [
    "Markdown",
    "HTMLRenderer",
    "BlockParser",
    "BlockState",
    "BaseRenderer",
    "InlineParser",
    "InlineState",
    "escape",
    "escape_url",
    "safe_entity",
    "unikey",
    "html",
    "create_markdown",
    "markdown",
]

RendererRef: TypeAlias = Literal["html", "ast"] | BaseRenderer

def create_markdown(
    escape: bool = True,
    hard_wrap: bool = False,
    renderer: RendererRef | None = "html",
    plugins: Iterable[PluginRef] | None = None,
) -> Markdown: ...

html: Markdown

def markdown(
    text: str,
    escape: bool = True,
    renderer: RendererRef | None = "html",
    plugins: Iterable[Any] | None = None,
) -> str | list[dict[str, Any]]: ...
