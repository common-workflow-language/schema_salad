"""test different sets of command line arguments"""

from pathlib import Path

import pytest

import schema_salad.main as cli_parser

from .util import cwl_file_uri


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


def test_python_codegen_parent_bad(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI Python code generator with invalid inheritance."""
    src_target = tmp_path / "src.py"
    with pytest.raises(SystemExit) as exec_info:
        cli_parser.main(
            argsl=[
                "--codegen=python",
                f"--codegen-target={src_target}",
                "--codegen-parent=https://w3id.org/cwl/salad:schema_salad.metaschema",
                cwl_file_uri,
            ]
        )
    assert exec_info.value.code == 2
    captured = capsys.readouterr()
    out = captured.out
    err = captured.err
    assert "" == out
    assert (
        "argument --codegen-parent: Invalid format: "
        r"'https://w3id.org/cwl/salad:schema_salad.metaschema', expected key=value" in err
    )
