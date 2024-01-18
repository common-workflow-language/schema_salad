from typing import Any, Dict

from ..core import BaseRenderer as BaseRenderer
from ..core import BlockState as BlockState
from ..util import strip_end as strip_end

def render_list(renderer: BaseRenderer, token: Dict[str, Any], state: BlockState) -> str: ...
