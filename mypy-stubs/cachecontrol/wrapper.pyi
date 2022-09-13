from typing import Collection, Type

from _typeshed import Incomplete
from requests import Session

from .cache import BaseCache
from .controller import CacheController

def CacheControl(
    sess: Session,
    cache: BaseCache | None = None,
    cache_etags: bool = True,
    serializer: Incomplete | None = None,
    heuristic: Incomplete | None = None,
    controller_class: Type[CacheController] | None = None,
    adapter_class: Incomplete | None = None,
    cacheable_methods: Collection[str] | None = None,
) -> Session: ...
