import abc
from abc import ABCMeta, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Match,
    Optional,
    Tuple,
    Type,
    Union,
)

from ..block_parser import BlockParser as BlockParser
from ..core import BlockState as BlockState
from ..markdown import Markdown as Markdown

class DirectiveParser(ABCMeta, metaclass=abc.ABCMeta):
    name: str
    @staticmethod
    @abstractmethod
    def parse_type(m: Match[str]) -> str: ...
    @staticmethod
    @abstractmethod
    def parse_title(m: Match[str]) -> str: ...
    @staticmethod
    @abstractmethod
    def parse_content(m: Match[str]) -> str: ...
    @classmethod
    def parse_tokens(
        cls, block: BlockParser, text: str, state: BlockState
    ) -> Iterable[Dict[str, Any]]: ...
    @staticmethod
    def parse_options(m: Match[str]) -> List[Tuple[str, str]]: ...

class BaseDirective(metaclass=ABCMeta):
    parser: Type[DirectiveParser]
    directive_pattern: Optional[str]
    def __init__(self, plugins: List["DirectivePlugin"]) -> None: ...
    def register(
        self,
        name: str,
        fn: Callable[
            [BlockParser, Match[str], BlockState], Union[Dict[str, Any], List[Dict[str, Any]]]
        ],
    ) -> None: ...
    def parse_method(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]: ...
    @abstractmethod
    def parse_directive(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Optional[int]: ...
    def register_block_parser(self, md: Markdown, before: Optional[str] = None) -> None: ...
    def __call__(self, markdown: Markdown) -> None: ...

class DirectivePlugin:
    parser: Type[DirectiveParser]
    def __init__(self) -> None: ...
    def parse_options(self, m: Match[str]) -> List[Tuple[str, str]]: ...
    def parse_type(self, m: Match[str]) -> str: ...
    def parse_title(self, m: Match[str]) -> str: ...
    def parse_content(self, m: Match[str]) -> str: ...
    def parse_tokens(
        self, block: BlockParser, text: str, state: BlockState
    ) -> Iterable[Dict[str, Any]]: ...
    def parse(
        self, block: BlockParser, m: Match[str], state: BlockState
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]: ...
    def __call__(self, directive: BaseDirective, md: Markdown) -> None: ...
