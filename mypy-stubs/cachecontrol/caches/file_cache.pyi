from cachecontrol.cache import SeparateBodyBaseCache
from datetime import datetime
from filelock import BaseFileLock
from pathlib import Path
from typing import IO, ContextManager

class _LockClass:
    path: str

_lock_class = ContextManager[_LockClass]

class _FileCacheMixin:
    directory: str
    forever: bool
    filemode: int
    dirmode: int
    lock_class: _lock_class | None = None
    def __init__(
        self,
        directory: str | Path,
        forever: bool = False,
        filemode: int = 384,
        dirmode: int = 448,
        lock_class: type[BaseFileLock] | None = None,
    ) -> None: ...
    @staticmethod
    def encode(x: str) -> str: ...
    def get(self, key: str) -> bytes | None: ...
    def set(self, key: str, value: bytes, expires: int | datetime | None = None) -> None: ...

class SeparateBodyFileCache(_FileCacheMixin, SeparateBodyBaseCache):
    def get_body(self, key: str) -> IO[bytes] | None: ...
    def set_body(self, key: str, body: bytes) -> None: ...
    def delete(self, key: str) -> None: ...
