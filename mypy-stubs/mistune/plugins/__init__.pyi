from typing import Callable, Dict, Generic, Protocol, TypeVar, Union
from typing_extensions import Literal

from mistune.inline_parser import RendererT
from mistune.markdown import Markdown
from mistune.renderers import DataT


PluginName = Literal[
    "url",
    "strikethrough",
    "footnotes",
    "table",
    "task_lists",
    "def_list",
    "abbr",
]

class Plugin(Protocol):
    def __call__(self, markdown: Markdown[DataT, RendererT]) -> None: ...

PLUGINS: Dict[PluginName, Plugin]
