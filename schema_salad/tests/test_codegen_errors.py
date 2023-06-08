"""Tests of helpful error messages."""

from pathlib import Path
from typing import Any, MutableSequence, Optional, Union, cast
from urllib.parse import unquote_plus, urlparse

import pytest

import schema_salad.tests.cwl_v1_0 as cwl_v1_0
from schema_salad.exceptions import ValidationException
from schema_salad.utils import yaml_no_ts

from .util import get_data


def test_error_message1() -> None:
    t = "test_schema/test1.cwl"
    match = r"""^.*test1\.cwl:2:1:\s+Object\s+`.*test1\.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
\s+\*\s+missing\s+required\s+field\s+`inputs`
\s+\*\s+missing\s+required\s+field\s+`outputs`
\s+\*\s+missing\s+required\s+field\s+`steps`"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message2() -> None:
    t = "test_schema/test2.cwl"
    match = r"""^.*test2\.cwl:2:1:\s+Field\s+`class`\s+contains\s+undefined\s+reference\s+to
\s+`file://.+/schema_salad/tests/test_schema/xWorkflow`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message4() -> None:
    t = "test_schema/test4.cwl"
    match = r"""^.*test4.cwl:2:1:\s+Object\s+`.*test4.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
.*test4\.cwl:6:1:\s+the\s+`outputs`\s+field\s+is\s+not\s+valid\s+because:
.*test4\.cwl:7:3:\s+checking\s+object\s+`.*test4\.cwl#bar`
\s+tried\s+`WorkflowOutputParameter`\s+but
\s+the\s+`type`\s+field\s+is\s+not\s+valid\s+because:
\s+Expected\s+one\s+of\s+\(list|dict|str,list|dict|str,list|dict|str\)\s+was
\s+<class\s+'int'>"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message5() -> None:
    t = "test_schema/test5.cwl"
    match = r"""^.*test5\.cwl:2:1:\s+Object\s+`.*test5\.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
.+test5\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`array<WorkflowStep>`\s+but
\s+-\s+tried\s+`array<WorkflowStep>`\s+but
\s+Expected\s+a\s+list,\s+was\s+<class\s+'int'>
\s+-\s+tried\s+`WorkflowStep`\s+but
\s+Expected\s+a\s+dict,\s+was\s+<class\s+'int'>"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message6() -> None:
    t = "test_schema/test6.cwl"
    match = r"""-\s+tried\s+`CommandLineTool`\s+but
\s+Missing\s+'class'\s+field
+-\s+tried\s+`ExpressionTool`\s+but
\s+Missing\s+'class'\s+field
+-\s+tried\s+`Workflow`\s+but
\s+Missing\s+'class'\s+field"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message7() -> None:
    t = "test_schema/test7.cwl"
    match = r"""^.*test7\.cwl:2:1:\s+Object\s+`.*test7\.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
.*test7\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`array<WorkflowStep>`\s+but
.*test7\.cwl:9:3:\s+checking object\s+`.*test7.cwl#step1`
\s+tried\s+`WorkflowStep`\s+but
\s+\*\s+missing\s+required\s+field\s+`run`
.*test7\.cwl:10:5:\s+\*\s+invalid\s+field\s+`scatter_method`,\s+expected\s+one of:.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*\s+.*$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message8() -> None:
    t = "test_schema/test8.cwl"
    match = r"""^.*test8.cwl:2:1:\s+Object\s+`.*test8.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
.*test8\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`array<WorkflowStep>`\s+but
.*test8\.cwl:9:3:\s+checking\s+object\s+`.*test8\.cwl#step1`
\s+tried\s+`WorkflowStep`\s+but
\s+\*\s+missing\s+required\s+field\s+`run`
.*test8\.cwl:10:5:\s+the\s+`scatterMethod`\s+field\s+is\s+not\s+valid\s+because:
\s+contains\s+undefined\s+reference\s+to
\s+`file:///.*/tests/test_schema/abc`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message9() -> None:
    t = "test_schema/test9.cwl"
    match = r"""^.*test9.cwl:2:1:\s+Object\s+`.*test9.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
.*test9\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`array<WorkflowStep>`\s+but
.*test9\.cwl:9:3:\s+checking object\s+`.*test9\.cwl#step1`
\s+tried\s+`WorkflowStep`\s+but
\s+\*\s+missing\s+required\s+field\s+`run`
.*test9\.cwl:10:5:\s+the\s+`scatterMethod`\s+field\s+is\s+not\s+valid\s+because:
\s+Expected\s+one\s+of\s+\("dotproduct|nested_crossproduct|flat_crossproduct",\s+"dotproduct|nested_crossproduct|flat_crossproduct",\s+"dotproduct|nested_crossproduct|flat_crossproduct"\) was\s+<class 'int'>"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message10() -> None:
    t = "test_schema/test10.cwl"
    match = r"""^.*test10\.cwl:2:1:\s+Object\s+`.*test10\.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
.*test10\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`array<WorkflowStep>`\s+but
.*test10\.cwl:9:3:\s+checking\s+object\s+`.*test10.cwl#step1`
\s+tried\s+`WorkflowStep`\s+but
\s+\*\s+missing\s+required\s+field\s+`run`
.*test10\.cwl:10:5:\s+the\s+`scatterMethod`\s+field\s+is\s+not\s+valid\s+because:
\s+Expected\s+one\s+of\s+\("dotproduct|nested_crossproduct|flat_crossproduct",\s+"dotproduct|nested_crossproduct|flat_crossproduct",\s+"dotproduct|nested_crossproduct|flat_crossproduct"\)\s+was\s+<class 'ruamel\.yaml\.comments\.CommentedSeq'>"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def test_error_message11() -> None:
    t = "test_schema/test11.cwl"
    match = r"""^.*test11\.cwl:2:1:\s+Object\s+`.*test11.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`Workflow`\s+but
.*test11\.cwl:8:1:\s+the\s+`steps`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`array<WorkflowStep>`\s+but
.*test11\.cwl:9:3:\s+checking\s+object\s+`.*test11\.cwl#step1`
\s+tried\s+`WorkflowStep`\s+but
.*test11\.cwl:10:5:\s+the\s+`run`\s+field\s+is\s+not\s+valid\s+because:
\s+contains\s+undefined\s+reference\s+to
\s+`file:///.*/tests/test_schema/blub\.cwl`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


# `loadContents`,\s+`position`,\s+`prefix`,\s+`separate`,\s+`itemSeparator`,\s+`valueFrom`,\s+`shellQuote`
def test_error_message15() -> None:
    t = "test_schema/test15.cwl"
    match = r"""^.*test15\.cwl:3:1:\s+Object\s+`.*test15\.cwl`\s+is\s+not\s+valid\s+because
\s+tried\s+`CommandLineTool`\s+but
.*test15\.cwl:6:1:\s+the\s+`inputs`\s+field\s+is\s+not\s+valid\s+because:
.*test15\.cwl:7:3:\s+checking\s+object\s+`.*test15\.cwl#message`
\s+tried\s+`CommandInputParameter`\s+but
.*test15\.cwl:9:5:\s+the\s+`inputBinding`\s+field\s+is\s+not\s+valid\s+because:
\s+tried\s+`CommandLineBinding`\s+but
\s+tried\s+`CommandLineBinding`\s+but
.*test15\.cwl:11:7:\s+\*\s+invalid\s+field\s+`invalid_field`,
\s+expected\s+one\s+of:\s+`loadContents`,\s+`position`,\s+`prefix`,\s+`separate`,\s+`itemSeparator`,\s+`valueFrom`,\s+`shellQuote`
.*test15\.cwl:12:7:\s+\*\s+invalid\s+field
\s+`another_invalid_field`,\s+expected one\s+of:\s+`loadContents`,\s+`position`,\s+`prefix`,\s+`separate`,\s+`itemSeparator`,\s+`valueFrom`,\s+`shellQuote`$"""
    path = get_data("tests/" + t)
    assert path
    with pytest.raises(ValidationException, match=match):
        load_document_by_uri(path)


def load_document_by_uri(path: Union[str, Path]) -> Any:
    if isinstance(path, str):
        uri = urlparse(path)
        if not uri.scheme or uri.scheme == "file":
            real_path = Path(unquote_plus(uri.path)).resolve().as_uri()
        else:
            real_path = path
    else:
        real_path = path.resolve().as_uri()

    baseuri = str(real_path)

    loadingOptions = cwl_v1_0.LoadingOptions(fileuri=baseuri)

    doc = loadingOptions.fetcher.fetch_text(real_path)

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
