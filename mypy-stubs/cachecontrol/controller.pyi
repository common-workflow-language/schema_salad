from typing import Collection

from _typeshed import Incomplete

from .cache import BaseCache

class CacheController:
    cache: BaseCache
    cache_etags: bool
    serializer: Incomplete
    cacheable_status_codes: Collection[int] | None = None
    def __init__(
        self,
        cache: BaseCache | None = None,
        cache_etags: bool = True,
        serializer: Incomplete | None = None,
        status_codes: Collection[int] | None = None,
    ) -> None: ...
