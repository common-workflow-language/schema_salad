"""Test C++ code generation."""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, cast

from schema_salad import codegen
from schema_salad.avro.schema import Names
from schema_salad.schema import load_schema
from schema_salad.sourceline import cmap
from schema_salad.utils import yaml_no_ts

from .util import cwl_file_uri, get_data


def test_cwl_cpp_gen(tmp_path: Path) -> None:
    """End to end test of C++ generator using the CWL v1.0 schema."""
    src_target = tmp_path / "cwl_v1_0.h"
    exe_target = tmp_path / "cwl_v1_0_test"
    cpp_codegen(cwl_file_uri, src_target)
    source = get_data("tests/codegen/cwl.cpp")
    assert source
    assert os.path.exists(src_target)
    compiler = os.environ["CXX"] if "CXX" in os.environ else "g++"
    compiler_flags = (
        os.environ["CXXFLAGS"] if "CXXFLAGS" in os.environ else "-std=c++20"
    )
    compile_result = subprocess.run(
        [
            compiler,
            f"-I{str(src_target.parent)}",
            compiler_flags,
            source,
            "-lyaml-cpp",
            "-o",
            str(exe_target),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    exe_result = subprocess.run(
        [str(exe_target)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    assert exe_result.returncode == 0, exe_result.stderr
    yaml = yaml_no_ts()
    exe_yaml = yaml.load(exe_result.stdout)
    target = cmap(
        {
            "id": "Some id",
            "inputs": [
                {
                    "id": "first",
                    "type": [
                        {
                            "type": "record",
                            "fields": [
                                {
                                    "name": "species",
                                    "type": [
                                        {
                                            "type": "enum",
                                            "symbols": ["homo_sapiens", "mus_musculus"],
                                        },
                                        "null",
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
            "outputs": [],
            "label": "some label",
            "doc": "documentation that is brief",
            "cwlVersion": "v1.0",
            "class": "",  # "CommandLineTool",
        }
    )
    assert exe_yaml == target


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
