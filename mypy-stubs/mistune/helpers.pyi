from typing import Any, Dict, Tuple, Union

from _typeshed import Incomplete

from .util import escape_url as escape_url

PREVENT_BACKSLASH: str
PUNCTUATION: Incomplete
LINK_LABEL: str
LINK_BRACKET_START: Incomplete
LINK_BRACKET_RE: Incomplete
LINK_HREF_BLOCK_RE: Incomplete
LINK_HREF_INLINE_RE: Incomplete
LINK_TITLE_RE: Incomplete
PAREN_END_RE: Incomplete
HTML_TAGNAME: str
HTML_ATTRIBUTES: str
BLOCK_TAGS: Incomplete
PRE_TAGS: Incomplete

def unescape_char(text: str) -> str: ...
def parse_link_text(src: str, pos: int) -> Union[Tuple[str, int], Tuple[None, None]]: ...
def parse_link_label(src: str, start_pos: int) -> Union[Tuple[str, int], Tuple[None, None]]: ...
def parse_link_href(
    src: str, start_pos: int, block: bool = False
) -> Union[Tuple[str, int], Tuple[None, None]]: ...
def parse_link_title(
    src: str, start_pos: int, max_pos: int
) -> Union[Tuple[str, int], Tuple[None, None]]: ...
def parse_link(src: str, pos: int) -> Union[Tuple[Dict[str, Any], int], Tuple[None, None]]: ...
