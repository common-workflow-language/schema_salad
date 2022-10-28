from typing import Any, List, Optional, Union
from typing_extensions import Literal

from mistune._types import DataT
from mistune.markdown import Markdown
from mistune.renderers import BaseRenderer, HTMLRenderer

html: Markdown[str, HTMLRenderer]

def create_markdown(
    escape: bool = False,
    hard_wrap: bool = False,
    renderer: Optional[Union[Literal["html", "ast"], BaseRenderer[DataT]]] = None,
    plugins: List[str] = ["strikethrough", "footnotes", "table"],  # noqa
) -> Markdown[DataT, HTMLRenderer]: ...
def markdown(
    text: str,
    escape: bool = True,
    renderer: Optional[BaseRenderer[Any]] = None,
    plugins: Optional[List[str]] = None,
) -> str: ...

__version__: str
