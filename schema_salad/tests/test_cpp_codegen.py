"""Test C++ code generation."""

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


def cpp_codegen(
    file_uri: str,
    target: Path,
) -> None:
    """Help using the C++ code generation function."""
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        file_uri
    )
    assert isinstance(avsc_names, Names)
    schema_raw_doc = metaschema_loader.fetch(file_uri)
    schema_doc, schema_metadata = metaschema_loader.resolve_all(
        schema_raw_doc, file_uri
    )
    codegen.codegen(
        "cpp",
        cast(List[Dict[str, Any]], schema_doc),
        schema_metadata,
        document_loader,
        target=str(target),
    )
