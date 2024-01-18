from typing import Protocol, Union

from ..markdown import Markdown

class Plugin(Protocol):
    def __call__(self, markdown: Markdown) -> None: ...

PluginRef = Union[str, Plugin]

def import_plugin(name: PluginRef) -> Plugin: ...
