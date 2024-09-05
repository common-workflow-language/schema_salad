"""Tests of helpful error messages."""

import importlib
from pathlib import Path
from typing import Any, Dict, List, MutableSequence, Optional, Union, cast
from urllib.parse import urlparse

import pytest

from schema_salad import codegen
from schema_salad.avro.schema import Names
from schema_salad.exceptions import ValidationException
from schema_salad.schema import load_schema
from schema_salad.utils import yaml_no_ts

from .util import cwl_file_uri, get_data


def test_error_message1(tmp_path: Path) -> None:
    t = "test_schema/test1.cwl"
    match = r"""^.*test1\.cwl:2:1:\s+Object\s+`.*test1\.cwl`\s+is\s+not\s+valid\s+because:
\s+\*\s+missing\s+required\s+field\s+`inputs`
\s+\*\s+missing\s+required\s+field\s+`outputs`
\s+\*\s+missing\s+required\s+field\s+`steps`"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message2(tmp_path: Path) -> None:
    t = "test_schema/test2.cwl"
    match = r"""^.*test2\.cwl:2:1:\s+Field\s+`class`\s+contains\s+undefined\s+reference\s+to\s+`file://.+/schema_salad/tests/test_schema/xWorkflow`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message4(tmp_path: Path) -> None:
    t = "test_schema/test4.cwl"
    match = r"""^.*test4.cwl:2:1:\s+Object\s+`.*test4.cwl`\s+is\s+not\s+valid\s+because:
.*test4\.cwl:6:1:\s+the\s+`outputs`\s+field\s+is\s+not\s+valid\s+because:
\s+array\s+item\s+is\s+invalid\s+because
.*test4\.cwl:7:3:\s+checking\s+object\s+`.*test4\.cwl#bar`
\s+the\s+`type`\s+field\s+is\s+not\s+valid\s+because:
\s+Value\s+is\s+a\s+int,\s+but\s+valid\s+types\s+for\s+this\s+field\s+are\s+\((str|object),\s+(str|object)\)"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message5(tmp_path: Path) -> None:
    t = "test_schema/test5.cwl"
    match = r"""^.*test5\.cwl:2:1:\s+Object\s+`.*test5\.cwl`\s+is\s+not\s+valid\s+because:
.+test5\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
.+test5\.cwl:8:9:\s+array\s+item\s+is\s+invalid\s+because
\s+Value\s+is\s+a\s+int,\s+but\s+valid\s+type\s+for\s+this\s+field\s+is\s+an\s+object"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message6(tmp_path: Path) -> None:
    t = "test_schema/test6.cwl"
    match = r"""\*\s+tried\s+`CommandLineTool`\s+but
\s+Missing\s+'class'\s+field
+\*\s+tried\s+`ExpressionTool`\s+but
\s+Missing\s+'class'\s+field
+\*\s+tried\s+`Workflow`\s+but
\s+Missing\s+'class'\s+field"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message7(tmp_path: Path) -> None:
    t = "test_schema/test7.cwl"
    match = r"""^.*test7\.cwl:2:1:\s+Object\s+`.*test7\.cwl`\s+is\s+not\s+valid\s+because:
.*test7\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+array\s+item\s+is\s+invalid\s+because
.*test7\.cwl:9:3:\s+checking\s+object\s+`.*test7.cwl#step1`
\s+\*\s+missing\s+required\s+field\s+`run`
.*test7\.cwl:10:5:\s+\*\s+invalid\s+field\s+`scatter_method`,\s+expected\s+one\s+of:\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message8(tmp_path: Path) -> None:
    t = "test_schema/test8.cwl"
    match = r"""^.*test8.cwl:2:1:\s+Object\s+`.*test8.cwl`\s+is\s+not\s+valid\s+because:
.*test8\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+array\s+item\s+is\s+invalid\s+because
.*test8\.cwl:9:3:\s+checking\s+object\s+`.*test8\.cwl#step1`
\s+\*\s+missing\s+required\s+field\s+`run`
.*test8\.cwl:10:5:\s+\*\s+the\s+`scatterMethod`\s+field\s+is\s+not\s+valid\s+because:
\s+contains\s+undefined\s+reference\s+to\s+`file:///.*/tests/test_schema/abc`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message9(tmp_path: Path) -> None:
    t = "test_schema/test9.cwl"
    match = r"""^.*test9.cwl:2:1:\s+Object\s+`.*test9.cwl`\s+is\s+not\s+valid\s+because:
.*test9\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+array\s+item\s+is\s+invalid\s+because
.*test9\.cwl:9:3:\s+checking\s+object\s+`.*test9\.cwl#step1`
\s+\*\s+missing\s+required\s+field\s+`run`
.*test9\.cwl:10:5:\s+\*\s+the\s+`scatterMethod`\s+field\s+is\s+not\s+valid\s+because:
\s+Value\s+is\s+a\s+int,\s+but\s+valid\s+values\s+for\s+this\s+field\s+are\s+\("(dotproduct|nested_crossproduct|flat_crossproduct)",\s+"(dotproduct|nested_crossproduct|flat_crossproduct)",\s+"(dotproduct|nested_crossproduct|flat_crossproduct)"\)"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message10(tmp_path: Path) -> None:
    t = "test_schema/test10.cwl"
    match = r"""^.*test10\.cwl:2:1:\s+Object\s+`.*test10\.cwl`\s+is\s+not\s+valid\s+because:
.*test10\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+array\s+item\s+is\s+invalid\s+because
.*test10\.cwl:9:3:\s+checking\s+object\s+`.*test10.cwl#step1`
\s+\*\s+missing\s+required\s+field\s+`run`
.*test10\.cwl:10:5:\s+\*\s+the\s+`scatterMethod`\s+field\s+is\s+not\s+valid\s+because:
\s+Value\s+is\s+a\s+array,\s+but\s+valid\s+types\s+for\s+this\s+field\s+are\s+\("dotproduct|nested_crossproduct|flat_crossproduct",\s+"dotproduct|nested_crossproduct|flat_crossproduct",\s+"dotproduct|nested_crossproduct|flat_crossproduct"\)"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def test_error_message11(tmp_path: Path) -> None:
    t = "test_schema/test11.cwl"
    match = r"""^.*test11\.cwl:2:1:\s+Object\s+`.*test11.cwl`\s+is\s+not\s+valid\s+because:
.*test11\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+array\s+item\s+is\s+invalid\s+because
.*test11\.cwl:9:3:\s+checking\s+object\s+`.*test11\.cwl#step1`
.*test11\.cwl:10:5:\s+the\s+`run`\s+field\s+is\s+not\s+valid\s+because:\s+contains\s+undefined\s+reference\s+to\s+`file:///.*/tests/test_schema/blub\.cwl`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


# `loadContents`,\s+`position`,\s+`prefix`,\s+`separate`,\s+`itemSeparator`,\s+`valueFrom`,\s+`shellQuote`
def test_error_message15(tmp_path: Path) -> None:
    t = "test_schema/test15.cwl"
    match = r"""^.*test15\.cwl:3:1:\s+Object\s+`.*test15\.cwl`\s+is\s+not\s+valid\s+because:
.*test15\.cwl:6:1:\s+the\s+`inputs`\s+field\s+is\s+not\s+valid\s+because:
\s+array\s+item\s+is\s+invalid\s+because
.*test15\.cwl:7:3:\s+checking\s+object\s+`.*test15\.cwl#message`
.*test15\.cwl:9:5:\s+the\s+`inputBinding`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`CommandLineBinding`\s+but
.*test15\.cwl:11:7:\s+\*\s+invalid\s+field\s+`invalid_field`,\s+expected\s+one\s+of:\s+`loadContents`,\s+`position`,\s+`prefix`,\s+`separate`,\s+`itemSeparator`,\s+`valueFrom`,\s+`shellQuote`
.*test15\.cwl:12:7:\s+\*\s+invalid\s+field\s+`another_invalid_field`,\s+expected one\s+of:\s+`loadContents`,\s+`position`,\s+`prefix`,\s+`separate`,\s+`itemSeparator`,\s+`valueFrom`,\s+`shellQuote`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(tmp_path, path)


def load_document_by_uri(tmp_path: Path, path: Union[str, Path]) -> Any:
    src_target = tmp_path / "cwl_v1_0.py"
    python_codegen(cwl_file_uri, src_target)
    spec = importlib.util.spec_from_file_location("cwl_v1_0", src_target)
    assert isinstance(spec, importlib.machinery.ModuleSpec)
    assert isinstance(spec.loader, importlib.abc.Loader)
    temp_cwl_v1_0 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(temp_cwl_v1_0)
    cwl_v1_0: Any = temp_cwl_v1_0

    if isinstance(path, str):
        uri = urlparse(path)
        if not uri.scheme or uri.scheme == "file":
            real_path = Path(uri.path).resolve().as_uri()
        else:
            real_path = path
    else:
        real_path = path.resolve().as_uri()

    baseuri = str(real_path)

    loadingOptions = cwl_v1_0.LoadingOptions(fileuri=baseuri)

    with open(path) as file:
        doc = file.read()
    # doc = loadingOptions.fetcher.fetch_text(urllib.parse.unquote(str(real_path)))
    yaml = yaml_no_ts()
    doc = yaml.load(doc)

    result = cwl_v1_0.load_document_by_yaml(
        doc, baseuri, cast(Optional[cwl_v1_0.LoadingOptions], loadingOptions)
    )

    if isinstance(result, MutableSequence):
        lst = []
        for r in result:
            lst.append(r)
        return lst
    return result


def python_codegen(
    file_uri: str,
    target: Path,
    parser_info: Optional[str] = None,
    package: Optional[str] = None,
) -> None:
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(file_uri)
    assert isinstance(avsc_names, Names)
    schema_raw_doc = metaschema_loader.fetch(file_uri)
    schema_doc, schema_metadata = metaschema_loader.resolve_all(schema_raw_doc, file_uri)
    codegen.codegen(
        "python",
        cast(List[Dict[str, Any]], schema_doc),
        schema_metadata,
        document_loader,
        target=str(target),
        parser_info=parser_info,
        package=package,
    )
