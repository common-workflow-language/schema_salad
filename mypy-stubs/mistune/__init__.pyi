from typing import Any, Iterable, Optional, Union
from typing_extensions import Literal

from mistune._types import DataT
from mistune.markdown import Markdown, ParseHook, RenderHook
from mistune.renderers import BaseRenderer, HTMLRenderer

html: Markdown[str, HTMLRenderer]

PluginName = Literal[
    "url",
    "strikethrough",
    "footnotes",
    "table",
    "task_lists",
    "def_list",
    "abbr",
]
PluginFunc = Union[ParseHook, RenderHook]
Plugin = Union[PluginName, PluginFunc]

def create_markdown(
    escape: bool = False,
    hard_wrap: bool = False,
    renderer: Optional[Union[Literal["html", "ast"], BaseRenderer[DataT]]] = None,
    plugins: Optional[Iterable[Plugin]] = None,
) -> Markdown[DataT, HTMLRenderer]: ...
def markdown(
    text: str,
    escape: bool = True,
    renderer: Optional[BaseRenderer[Any]] = None,
    plugins: Optional[Iterable[Plugin]] = None,
) -> str: ...

__version__: str
