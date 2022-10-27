from typing import Any, List, Optional
from mistune.renderers import BaseRenderer

def markdown(
    text: str,
    escape: bool = True,
    renderer: Optional[BaseRenderer[Any]] = None,
    plugins: Optional[List[str]] = None,
) -> str: ...

__version__: str
