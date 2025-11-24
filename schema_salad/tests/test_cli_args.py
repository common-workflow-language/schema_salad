"""test different sets of command line arguments"""

import pytest

import schema_salad.main as cli_parser


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    args: list[list[str]] = [["--version"], ["-v"]]
    for arg in args:
        cli_parser.main(arg)

        response = capsys.readouterr().out
        assert "Current version" in response


def test_empty_input(capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
    """Run schema_salad tool without any args to get the help."""
    args: list[str] = []
    cli_parser.main(args)

    captured = capsys.readouterr()
    out = captured.out
    err = captured.err
    assert "" == out
    assert "Validate Salad schemas or documents" in err
    assert "Error: too few arguments" in caplog.text
