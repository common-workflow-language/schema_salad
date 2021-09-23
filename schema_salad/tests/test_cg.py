import json
import os
from typing import Any

import pytest

import schema_salad.metaschema as cg_metaschema
from schema_salad.exceptions import ValidationException
from schema_salad.ref_resolver import file_uri
from schema_salad.utils import yaml_no_ts

from .matcher import JsonDiffMatcher
from .util import get_data


def test_load() -> None:
    doc = {
        "type": "record",
        "fields": [{"name": "hello", "doc": "Hello test case", "type": "string"}],
    }
    rs = cg_metaschema.RecordSchema.fromDoc(
        doc, "http://example.com/", cg_metaschema.LoadingOptions()
    )
    assert "record" == rs.type
    assert rs.fields and "http://example.com/#hello" == rs.fields[0].name
    assert "Hello test case" == rs.fields[0].doc
    assert "string" == rs.fields[0].type
    assert {
        "type": "record",
        "fields": [
            {
                "name": "http://example.com/#hello",
                "doc": "Hello test case",
                "type": "string",
            }
        ],
    } == rs.save()


def test_err() -> None:
    doc = {"doc": "Hello test case", "type": "string"}
    with pytest.raises(ValidationException):
        cg_metaschema.RecordField.fromDoc(doc, "", cg_metaschema.LoadingOptions())


def test_include() -> None:
    doc = {"name": "hello", "doc": [{"$include": "hello.txt"}], "type": "documentation"}
    path = get_data("tests/_")
    assert path
    rf = cg_metaschema.Documentation.fromDoc(
        doc,
        "http://example.com/",
        cg_metaschema.LoadingOptions(fileuri=file_uri(path)),
    )
    assert "http://example.com/#hello" == rf.name
    assert ["hello world!\n"] == rf.doc
    assert "documentation" == rf.type
    assert {
        "name": "http://example.com/#hello",
        "doc": ["hello world!\n"],
        "type": "documentation",
    } == rf.save()


def test_import() -> None:
    doc = {"type": "record", "fields": [{"$import": "hellofield.yml"}]}
    tests_path = get_data("tests")
    assert tests_path
    lead = file_uri(os.path.normpath(tests_path))
    rs = cg_metaschema.RecordSchema.fromDoc(
        doc, "http://example.com/", cg_metaschema.LoadingOptions(fileuri=lead + "/_")
    )
    assert "record" == rs.type
    assert rs.fields and lead + "/hellofield.yml#hello" == rs.fields[0].name
    assert "hello world!\n" == rs.fields[0].doc
    assert "string" == rs.fields[0].type
    assert {
        "type": "record",
        "fields": [
            {
                "name": lead + "/hellofield.yml#hello",
                "doc": "hello world!\n",
                "type": "string",
            }
        ],
    } == rs.save()


maxDiff = None


def test_import2() -> None:
    path = get_data("tests/docimp/d1.yml")
    assert path
    rs = cg_metaschema.load_document(file_uri(path), "", cg_metaschema.LoadingOptions())
    path2 = get_data("tests/docimp/d1.yml")
    assert path2
    assert [
        {
            "doc": [
                "*Hello*",
                "hello 2",
                "*dee dee dee five*",
                "hello 3",
                "hello 4",
                "*dee dee dee five*",
                "hello 5",
            ],
            "type": "documentation",
            "name": file_uri(path2) + "#Semantic_Annotations_for_Linked_Avro_Data",
        }
    ] == [r.save() for r in rs]


def test_err2() -> None:
    doc = {
        "type": "rucord",
        "fields": [{"name": "hello", "doc": "Hello test case", "type": "string"}],
    }
    with pytest.raises(ValidationException):
        cg_metaschema.RecordSchema.fromDoc(doc, "", cg_metaschema.LoadingOptions())


def test_idmap() -> None:
    doc = {
        "type": "record",
        "fields": {"hello": {"doc": "Hello test case", "type": "string"}},
    }
    rs = cg_metaschema.RecordSchema.fromDoc(
        doc, "http://example.com/", cg_metaschema.LoadingOptions()
    )
    assert "record" == rs.type
    assert rs.fields and "http://example.com/#hello" == rs.fields[0].name
    assert "Hello test case" == rs.fields[0].doc
    assert "string" == rs.fields[0].type
    assert {
        "type": "record",
        "fields": [
            {
                "name": "http://example.com/#hello",
                "doc": "Hello test case",
                "type": "string",
            }
        ],
    } == rs.save()


def test_idmap2() -> None:
    doc = {"type": "record", "fields": {"hello": "string"}}
    rs = cg_metaschema.RecordSchema.fromDoc(
        doc, "http://example.com/", cg_metaschema.LoadingOptions()
    )
    assert "record" == rs.type
    assert rs.fields and "http://example.com/#hello" == rs.fields[0].name
    assert rs.fields[0].doc is None
    assert "string" == rs.fields[0].type
    assert {
        "type": "record",
        "fields": [{"name": "http://example.com/#hello", "type": "string"}],
    } == rs.save()


def test_load_pt() -> None:
    path = get_data("tests/pt.yml")
    assert path
    doc = cg_metaschema.load_document(
        file_uri(path), "", cg_metaschema.LoadingOptions()
    )
    assert [
        "https://w3id.org/cwl/salad#null",
        "http://www.w3.org/2001/XMLSchema#boolean",
        "http://www.w3.org/2001/XMLSchema#int",
        "http://www.w3.org/2001/XMLSchema#long",
        "http://www.w3.org/2001/XMLSchema#float",
        "http://www.w3.org/2001/XMLSchema#double",
        "http://www.w3.org/2001/XMLSchema#string",
    ] == doc.symbols


@pytest.fixture
def metaschema_pre() -> Any:
    """Prep-parsed schema for testing."""
    path2 = get_data("tests/metaschema-pre.yml")
    assert path2
    with open(path2) as f:
        pre = json.load(f)
    return pre


def test_load_metaschema(metaschema_pre: Any) -> None:
    path = get_data("metaschema/metaschema.yml")
    assert path
    doc = cg_metaschema.load_document(
        file_uri(path),
        "",
        None,
    )
    saved = [d.save(relative_uris=False) for d in doc]
    assert saved == JsonDiffMatcher(metaschema_pre)


def test_load_by_yaml_metaschema(metaschema_pre: Any) -> None:
    path = get_data("metaschema/metaschema.yml")
    assert path
    with open(path) as path_handle:
        yaml = yaml_no_ts()
        yaml_doc = yaml.load(path_handle)
    doc = cg_metaschema.load_document_by_yaml(
        yaml_doc,
        file_uri(path),
        None,
    )
    saved = [d.save(relative_uris=False) for d in doc]
    assert saved == JsonDiffMatcher(metaschema_pre)


def test_load_cwlschema() -> None:
    path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    assert path
    doc = cg_metaschema.load_document(
        file_uri(path),
        "",
        cg_metaschema.LoadingOptions(),
    )
    path2 = get_data("tests/cwl-pre.yml")
    assert path2
    with open(path2) as f:
        pre = json.load(f)
    saved = [d.save(relative_uris=False) for d in doc]
    assert saved == JsonDiffMatcher(pre)
