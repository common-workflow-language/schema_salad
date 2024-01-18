from typing import Any, Dict, Iterable, List, Optional, Union

from typing_extensions import Literal

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

RendererRef = Union[Literal["html", "ast"], BaseRenderer]

def create_markdown(
    escape: bool = True,
    hard_wrap: bool = False,
    renderer: Optional[RendererRef] = "html",
    plugins: Optional[Iterable[PluginRef]] = None,
) -> Markdown: ...

html: Markdown

def markdown(
    text: str,
    escape: bool = True,
    renderer: Optional[RendererRef] = "html",
    plugins: Optional[Iterable[Any]] = None,
) -> Union[str, List[Dict[str, Any]]]: ...
