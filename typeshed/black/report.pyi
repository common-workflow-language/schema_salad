from enum import Enum
from pathlib import Path

from black.output import err as err
from black.output import out as out

class Changed(Enum):
    NO: int
    CACHED: int
    YES: int

class NothingChanged(UserWarning): ...

class Report:
    check: bool
    diff: bool
    quiet: bool
    verbose: bool
    change_count: int
    same_count: int
    failure_count: int
    def done(self, src: Path, changed: Changed) -> None: ...
    def failed(self, src: Path, message: str) -> None: ...
    def path_ignored(self, path: Path, message: str) -> None: ...
    @property
    def return_code(self) -> int: ...
