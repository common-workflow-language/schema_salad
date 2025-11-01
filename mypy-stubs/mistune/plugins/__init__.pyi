from typing import Protocol, TypeAlias

from ..markdown import Markdown

class Plugin(Protocol):
    def __call__(self, markdown: Markdown) -> None: ...

PluginRef: TypeAlias = str | Plugin

def import_plugin(name: PluginRef) -> Plugin: ...
