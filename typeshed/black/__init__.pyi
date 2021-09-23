import asyncio
from concurrent.futures import Executor
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Iterator,
    List,
    MutableMapping,
    Optional,
    Pattern,
    Set,
    Sized,
    Tuple,
    Union,
)

import click
from black.cache import Cache as Cache
from black.cache import filter_cached as filter_cached
from black.cache import get_cache_info as get_cache_info
from black.cache import read_cache as read_cache
from black.cache import write_cache as write_cache
from black.comments import normalize_fmt_off as normalize_fmt_off
from black.concurrency import cancel as cancel
from black.concurrency import maybe_install_uvloop as maybe_install_uvloop
from black.concurrency import shutdown as shutdown
from black.const import DEFAULT_EXCLUDES as DEFAULT_EXCLUDES
from black.const import DEFAULT_INCLUDES as DEFAULT_INCLUDES
from black.const import DEFAULT_LINE_LENGTH as DEFAULT_LINE_LENGTH
from black.const import STDIN_PLACEHOLDER as STDIN_PLACEHOLDER
from black.files import find_project_root as find_project_root
from black.files import find_pyproject_toml as find_pyproject_toml
from black.files import gen_python_files as gen_python_files
from black.files import get_gitignore as get_gitignore
from black.files import normalize_path_maybe_ignore as normalize_path_maybe_ignore
from black.files import parse_pyproject_toml as parse_pyproject_toml
from black.files import wrap_stream_for_windows as wrap_stream_for_windows
from black.handle_ipynb_magics import TRANSFORMED_MAGICS as TRANSFORMED_MAGICS
from black.handle_ipynb_magics import (
    jupyter_dependencies_are_installed as jupyter_dependencies_are_installed,
)
from black.handle_ipynb_magics import mask_cell as mask_cell
from black.handle_ipynb_magics import (
    put_trailing_semicolon_back as put_trailing_semicolon_back,
)
from black.handle_ipynb_magics import (
    remove_trailing_semicolon as remove_trailing_semicolon,
)
from black.handle_ipynb_magics import unmask_cell as unmask_cell
from black.linegen import LN as LN
from black.linegen import LineGenerator as LineGenerator
from black.linegen import transform_line as transform_line
from black.lines import EmptyLineTracker as EmptyLineTracker
from black.lines import Line as Line
from black.mode import VERSION_TO_FEATURES as VERSION_TO_FEATURES
from black.mode import Feature as Feature
from black.mode import Mode as Mode
from black.mode import TargetVersion as TargetVersion
from black.mode import supports_feature as supports_feature
from black.nodes import STARS as STARS
from black.nodes import is_simple_decorator_expression as is_simple_decorator_expression
from black.nodes import syms as syms
from black.output import color_diff as color_diff
from black.output import diff as diff
from black.output import dump_to_file as dump_to_file
from black.output import err as err
from black.output import ipynb_diff as ipynb_diff
from black.output import out as out
from black.parsing import InvalidInput as InvalidInput
from black.parsing import lib2to3_parse as lib2to3_parse
from black.parsing import parse_ast as parse_ast
from black.parsing import stringify_ast as stringify_ast
from black.report import Changed as Changed
from black.report import NothingChanged as NothingChanged
from black.report import Report as Report

FileContent = str
Encoding = str
NewLine = str

class WriteBack(Enum):
    NO: int
    YES: int
    DIFF: int
    CHECK: int
    COLOR_DIFF: int
    @classmethod
    def from_configuration(
        cls, check: bool, diff: bool, *, color: bool = ...
    ) -> WriteBack: ...

FileMode = Mode

def read_pyproject_toml(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]: ...
def target_version_option_callback(
    c: click.Context, p: Union[click.Option, click.Parameter], v: Tuple[str, ...]
) -> List[TargetVersion]: ...
def re_compile_maybe_verbose(regex: str) -> Pattern[str]: ...
def validate_regex(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Pattern]: ...
def main(
    ctx: click.Context,
    code: Optional[str],
    line_length: int,
    target_version: List[TargetVersion],
    check: bool,
    diff: bool,
    color: bool,
    fast: bool,
    pyi: bool,
    ipynb: bool,
    skip_string_normalization: bool,
    skip_magic_trailing_comma: bool,
    experimental_string_processing: bool,
    quiet: bool,
    verbose: bool,
    required_version: str,
    include: Pattern,
    exclude: Optional[Pattern],
    extend_exclude: Optional[Pattern],
    force_exclude: Optional[Pattern],
    stdin_filename: Optional[str],
    src: Tuple[str, ...],
    config: Optional[str],
) -> None: ...
def get_sources(
    ctx: click.Context,
    src: Tuple[str, ...],
    quiet: bool,
    verbose: bool,
    include: Pattern[str],
    exclude: Optional[Pattern[str]],
    extend_exclude: Optional[Pattern[str]],
    force_exclude: Optional[Pattern[str]],
    report: Report,
    stdin_filename: Optional[str],
) -> Set[Path]: ...
def path_empty(
    src: Sized, msg: str, quiet: bool, verbose: bool, ctx: click.Context
) -> None: ...
def reformat_code(
    content: str, fast: bool, write_back: WriteBack, mode: Mode, report: Report
) -> None: ...
def reformat_one(
    src: Path, fast: bool, write_back: WriteBack, mode: Mode, report: Report
) -> None: ...
def reformat_many(
    sources: Set[Path], fast: bool, write_back: WriteBack, mode: Mode, report: Report
) -> None: ...
async def schedule_formatting(
    sources: Set[Path],
    fast: bool,
    write_back: WriteBack,
    mode: Mode,
    report: Report,
    loop: asyncio.AbstractEventLoop,
    executor: Executor,
) -> None: ...
def format_file_in_place(
    src: Path, fast: bool, mode: Mode, write_back: WriteBack = ..., lock: Any = ...
) -> bool: ...
def format_stdin_to_stdout(
    fast: bool, *, content: Optional[str] = ..., write_back: WriteBack = ..., mode: Mode
) -> bool: ...
def check_stability_and_equivalence(
    src_contents: str, dst_contents: str, mode: Mode
) -> None: ...
def format_file_contents(src_contents: str, fast: bool, mode: Mode) -> FileContent: ...
def validate_cell(src: str) -> None: ...
def format_cell(src: str, fast: bool, mode: Mode) -> str: ...
def validate_metadata(nb: MutableMapping[str, Any]) -> None: ...
def format_ipynb_string(src_contents: str, fast: bool, mode: Mode) -> FileContent: ...
def format_str(src_contents: str, mode: Mode) -> FileContent: ...
def decode_bytes(src: bytes) -> Tuple[FileContent, Encoding, NewLine]: ...
def assert_equivalent(src: str, dst: str, *, pass_num: int = ...) -> None: ...
def assert_stable(src: str, dst: str, mode: Mode) -> None: ...
def nullcontext() -> Iterator[None]: ...
def patch_click() -> None: ...
def patched_main() -> None: ...
