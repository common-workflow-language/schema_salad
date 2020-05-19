""" test different sets of command line arguments"""

import sys  # for capturing print() output
from contextlib import contextmanager
from io import StringIO
from typing import Iterator, List, Tuple

import schema_salad.main as cli_parser


@contextmanager
def captured_output() -> Iterator[Tuple[StringIO, StringIO]]:
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def test_version() -> None:
    args = [["--version"], ["-v"]]  # type: List[List[str]]
    for arg in args:
        with captured_output() as (out, err):
            cli_parser.main(arg)

        response = out.getvalue().strip()  # capture output and strip newline
        assert "Current version" in response


def test_empty_input() -> None:
    # running schema_salad tool wihtout any args
    args = []  # type: List[str]
    with captured_output() as (out, err):
        cli_parser.main(args)

    response = out.getvalue().strip()
    assert "error: too few arguments" in response
