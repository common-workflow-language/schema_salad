from dataclasses import dataclass
from enum import Enum
from typing import Dict, Set

from black.const import DEFAULT_LINE_LENGTH as DEFAULT_LINE_LENGTH

class TargetVersion(Enum):
    PY27: int
    PY33: int
    PY34: int
    PY35: int
    PY36: int
    PY37: int
    PY38: int
    PY39: int
    def is_python2(self) -> bool: ...

class Feature(Enum):
    UNICODE_LITERALS: int
    F_STRINGS: int
    NUMERIC_UNDERSCORES: int
    TRAILING_COMMA_IN_CALL: int
    TRAILING_COMMA_IN_DEF: int
    ASYNC_IDENTIFIERS: int
    ASYNC_KEYWORDS: int
    ASSIGNMENT_EXPRESSIONS: int
    POS_ONLY_ARGUMENTS: int
    RELAXED_DECORATORS: int
    FORCE_OPTIONAL_PARENTHESES: int

VERSION_TO_FEATURES: Dict[TargetVersion, Set[Feature]]

def supports_feature(target_versions: Set[TargetVersion], feature: Feature) -> bool: ...
@dataclass
class Mode:
    target_versions: Set[TargetVersion]
    line_length: int = 88
    string_normalization: bool = True
    is_pyi: bool = False
    is_ipynb: bool = False
    magic_trailing_comma: bool = True
    experimental_string_processing: bool = False
    def get_cache_key(self) -> str: ...
