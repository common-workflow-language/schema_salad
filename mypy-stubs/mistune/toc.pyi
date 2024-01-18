from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from .core import BlockState as BlockState
from .markdown import Markdown as Markdown
from .util import striptags as striptags

def add_toc_hook(
    md: Markdown,
    min_level: int = 1,
    max_level: int = 3,
    heading_id: Optional[Callable[[Dict[str, Any], int], str]] = None,
) -> None: ...
def normalize_toc_item(md: Markdown, token: Dict[str, Any]) -> Tuple[int, str, str]: ...
def render_toc_ul(toc: Iterable[Tuple[int, str, str]]) -> str: ...
