from collections.abc import Callable, Iterable
from typing import Any

from .core import BlockState as BlockState
from .markdown import Markdown as Markdown
from .util import striptags as striptags

def add_toc_hook(
    md: Markdown,
    min_level: int = 1,
    max_level: int = 3,
    heading_id: Callable[[dict[str, Any], int], str] | None = None,
) -> None: ...
def normalize_toc_item(md: Markdown, token: dict[str, Any]) -> tuple[int, str, str]: ...
def render_toc_ul(toc: Iterable[tuple[int, str, str]]) -> str: ...
