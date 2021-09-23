from pathlib import Path
from typing import Any, Dict, Iterable, Set, Tuple

from black.mode import Mode as Mode

Timestamp = float
FileSize = int
CacheInfo = Tuple[Timestamp, FileSize]
Cache = Dict[str, CacheInfo]
CACHE_DIR: Any

def read_cache(mode: Mode) -> Cache: ...
def get_cache_file(mode: Mode) -> Path: ...
def get_cache_info(path: Path) -> CacheInfo: ...
def filter_cached(
    cache: Cache, sources: Iterable[Path]
) -> Tuple[Set[Path], Set[Path]]: ...
def write_cache(cache: Cache, sources: Iterable[Path], mode: Mode) -> None: ...
