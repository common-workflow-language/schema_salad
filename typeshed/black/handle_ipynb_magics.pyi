import ast
from typing import Any, Dict, List, Optional, Tuple

from black.output import out as out
from black.report import NothingChanged as NothingChanged
from typing_extensions import TypeGuard as TypeGuard

TRANSFORMED_MAGICS: Any
TOKENS_TO_IGNORE: Any
NON_PYTHON_CELL_MAGICS: Any

class Replacement:
    mask: str
    src: str

def jupyter_dependencies_are_installed(verbose: bool, quiet: bool) -> bool: ...
def remove_trailing_semicolon(src: str) -> Tuple[str, bool]: ...
def put_trailing_semicolon_back(src: str, has_trailing_semicolon: bool) -> str: ...
def mask_cell(src: str) -> Tuple[str, List[Replacement]]: ...
def get_token(src: str, magic: str) -> str: ...
def replace_cell_magics(src: str) -> Tuple[str, List[Replacement]]: ...
def replace_magics(src: str) -> Tuple[str, List[Replacement]]: ...
def unmask_cell(src: str, replacements: List[Replacement]) -> str: ...

class CellMagic:
    header: str
    body: str

class CellMagicFinder(ast.NodeVisitor):
    cell_magic: Optional[CellMagic]
    def visit_Expr(self, node: ast.Expr) -> None: ...

class OffsetAndMagic:
    col_offset: int
    magic: str

class MagicFinder(ast.NodeVisitor):
    magics: Dict[int, List[OffsetAndMagic]]
    def visit_Assign(self, node: ast.Assign) -> None: ...
    def visit_Expr(self, node: ast.Expr) -> None: ...
