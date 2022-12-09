from typing import Iterable, Optional, Union

from mistune._types import *
from mistune.inline_parser import RendererT
from mistune.markdown import Markdown, ParseHook, RenderHook
from mistune.plugins import Plugin, PluginName
from mistune.renderers import BaseRenderer, DataT, HTMLRenderer, HTMLType
from typing_extensions import Literal

html: Markdown[HTMLType, HTMLRenderer]

RendererRef = Union[Literal["html", "ast"], BaseRenderer[DataT]]
PluginRef = Union[PluginName, Plugin]  # reference to register a plugin

def create_markdown(
    escape: bool = False,
    hard_wrap: bool = False,
    renderer: Optional[RendererRef[DataT]] = None,
    plugins: Optional[Iterable[PluginRef]] = None,
) -> Markdown[DataT, RendererT]: ...
def markdown(
    text: str,
    escape: bool = True,
    renderer: Optional[BaseRenderer[DataT]] = None,
    plugins: Optional[Iterable[PluginRef]] = None,
) -> str: ...

__version__: str
