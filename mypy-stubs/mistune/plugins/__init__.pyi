from typing import Dict, Protocol

from mistune.inline_parser import RendererT
from mistune.markdown import Markdown
from mistune.renderers import DataT
from typing_extensions import Literal

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
