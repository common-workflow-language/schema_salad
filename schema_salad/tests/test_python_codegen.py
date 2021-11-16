import inspect
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import schema_salad.metaschema as cg_metaschema
from schema_salad import codegen
from schema_salad.avro.schema import Names
from schema_salad.schema import load_schema

from .test_java_codegen import cwl_file_uri, metaschema_file_uri


def test_cwl_gen(tmp_path: Path) -> None:
    src_target = tmp_path / "src.py"
    python_codegen(cwl_file_uri, src_target)
    assert os.path.exists(src_target)
    with open(src_target) as f:
        assert "class Workflow(Process)" in f.read()


def test_meta_schema_gen(tmp_path: Path) -> None:
    src_target = tmp_path / "src.py"
    python_codegen(metaschema_file_uri, src_target)
    assert os.path.exists(src_target)
    with open(src_target) as f:
        assert "class RecordSchema(Savable):" in f.read()


def test_meta_schema_gen_up_to_date(tmp_path: Path) -> None:
    src_target = tmp_path / "src.py"
    python_codegen(metaschema_file_uri, src_target)
    assert os.path.exists(src_target)
    with open(src_target) as f:
        assert f.read() == inspect.getsource(cg_metaschema)


def python_codegen(
    file_uri: str,
    target: Path,
    parser_info: Optional[str] = None,
    package: Optional[str] = None,
) -> None:
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        file_uri
    )
    assert isinstance(avsc_names, Names)
    schema_raw_doc = metaschema_loader.fetch(file_uri)
    schema_doc, schema_metadata = metaschema_loader.resolve_all(
        schema_raw_doc, file_uri
    )
    codegen.codegen(
        "python",
        cast(List[Dict[str, Any]], schema_doc),
        schema_metadata,
        document_loader,
        target=str(target),
        parser_info=parser_info,
        package=package,
    )


def test_default_parser_info(tmp_path: Path) -> None:
    src_target = tmp_path / "src.py"
    python_codegen(metaschema_file_uri, src_target)
    assert os.path.exists(src_target)
    with open(src_target) as f:
        assert 'def parser_info() -> str:\n    return "org.w3id.cwl.salad"' in f.read()


def test_parser_info(tmp_path: Path) -> None:
    src_target = tmp_path / "src.py"
    python_codegen(metaschema_file_uri, src_target, parser_info="cwl")
    assert os.path.exists(src_target)
    with open(src_target) as f:
        assert 'def parser_info() -> str:\n    return "cwl"' in f.read()


def test_use_of_package_for_parser_info(tmp_path: Path) -> None:
    src_target = tmp_path / "src.py"
    python_codegen(metaschema_file_uri, src_target, package="cwl")
    assert os.path.exists(src_target)
    with open(src_target) as f:
        assert 'def parser_info() -> str:\n    return "cwl"' in f.read()
