from typing import Any, List, Optional, Union
from mistune.renderers import AstRenderer, BaseRenderer, HTMLRenderer

def markdown(
    text: str,
    escape: bool = True,
    renderer: Optional[BaseRenderer[Any]] = None,
    plugins: Optional[List[str]] = None,
) -> str: ...

__version__: str
