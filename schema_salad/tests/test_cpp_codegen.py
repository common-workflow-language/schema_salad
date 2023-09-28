"""Test C++ code generation."""

import filecmp
import os
from pathlib import Path
from typing import Any, Dict, List, cast

from schema_salad import codegen
from schema_salad.avro.schema import Names
from schema_salad.schema import load_schema

from .util import cwl_file_uri, get_data


def test_cwl_cpp_gen(tmp_path: Path) -> None:
    """End to end test of C++ generator using the CWL v1.0 schema."""
    src_target = tmp_path / "cwl_v1_0.h"
    cpp_codegen(cwl_file_uri, src_target)
    source = get_data("tests/codegen/cwl.cpp")
    assert source
    assert os.path.exists(src_target)


def test_cwl_cpp_generations(tmp_path: Path) -> None:
    """End to end test of C++ generator using the CWL v1.0 schema."""

    test_dir = Path(cast(str, get_data("cpp_tests/01_single_record.yml"))).parents[0]

    # iterate through all cpp_tests YAML files
    for file in test_dir.iterdir():
        if file.suffix != ".yaml":
            continue

        # file with generated cpp output
        src_target = tmp_path / "test.h"
        # file with expected cpp output
        expected = test_dir.with_suffix(".h")

        cpp_codegen(os.fspath(file), src_target)

        assert filecmp.cmp(expected, src_target, shallow=False)


def cpp_codegen(
    file_uri: str,
    target: Path,
) -> None:
    """Help using the C++ code generation function."""
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(file_uri)
    assert isinstance(avsc_names, Names)
    schema_raw_doc = metaschema_loader.fetch(file_uri)
    schema_doc, schema_metadata = metaschema_loader.resolve_all(schema_raw_doc, file_uri)
    codegen.codegen(
        "cpp",
        cast(List[Dict[str, Any]], schema_doc),
        schema_metadata,
        document_loader,
        target=str(target),
    )
