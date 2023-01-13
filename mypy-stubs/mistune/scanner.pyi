from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterable,
    Iterator,
    List,
    Match,
    Pattern,
    Tuple,
    Type,
    Union,
)

from mistune._types import State
from typing_extensions import TypeAlias

MethodFunc: TypeAlias = Callable[["ScannerParser", Match, State], Any]
RuleMethod = Tuple[Pattern[str], MethodFunc]
Lexicon = List[Tuple[Pattern[str], Tuple[str, RuleMethod]]]
TextParser = Callable[[str, State], str]

class SREScanner:  # real type unknown
    def __init__(self, lexicon: Lexicon) -> None: ...
    def scanner(self, string: str) -> Pattern[str]: ...

class Scanner(object):
    scanner: ClassVar[SREScanner]
    lexicon: Lexicon

    def iter(
        self,
        string: str,
        state: State,
        parse_text: TextParser,
    ) -> Iterator[str]: ...

class Matcher:
    PARAGRAPH_END: ClassVar[Pattern[str]]
    lexicon: Lexicon

    def __init__(self, lexicon: Lexicon) -> None: ...
    def search_pos(self, string: str, pos: int) -> int: ...
    def iter(
        self, string: str, state: State, parse_text: TextParser
    ) -> Iterator[str]: ...

class ScannerParser:
    RULE_NAMES: ClassVar[Tuple[str, ...]]
    scanner_cls: ClassVar[Union[Type[SREScanner], Type[Matcher]]]
    rules: List[str]
    rule_methods: Dict[str, RuleMethod]
    _cached_sc: Dict[str, Scanner]

    def __init__(self) -> None: ...
    def register_rule(
        self, name: str, patter: Pattern[str], method: RuleMethod
    ) -> None: ...
    def get_rule_pattern(self, name: str) -> Pattern[str]: ...
    def get_rule_method(self, name: str) -> RuleMethod: ...
    def parse_text(
        self, text: str, state: State
    ) -> Any: ...  # abstract method, return specialized by implementation
    def _scan(self, s: str, state: State, rules: Iterable[str]) -> Iterator[str]: ...
    def _create_scanner(self, rules: Iterable[str]) -> Scanner: ...
