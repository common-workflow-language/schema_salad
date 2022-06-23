"""Confirm subtypes."""
import pytest

from schema_salad.avro import schema
from schema_salad.avro.schema import Names, SchemaParseException
from schema_salad.schema import load_schema

from .util import get_data

types = [
    (["int", "float", "double"], "int", True),
    (["int", "float", "double"], ["int"], True),
    (["int", "float", "double"], ["int", "float"], True),
    (["int", "float", "double"], ["int", "float", "File"], False),
    ({"type": "array", "items": ["int", "float", "double"]}, ["int", "float"], False),
    (
        {"type": "array", "items": ["int", "float", "double"]},
        {"type": "array", "items": ["int", "float"]},
        True,
    ),
    ("Any", "int", True),
    ("Any", ["int", "null"], False),
    ("Any", ["int"], True),
    ("Any", None, False),
    ("Any", ["null"], False),
    ("Any", "null", False),
    (
        "Any",
        {"type": "record", "fields": [{"name": "species", "type": "string"}]},
        True,
    ),
    ("Any", {"type": "enum", "symbols": ["homo_sapiens"]}, True),
    (
        {"type": "enum", "symbols": ["homo_sapiens", "mus_musculus"]},
        {"type": "enum", "symbols": ["homo_sapiens"]},
        True,
    ),
    (
        {"type": "enum", "symbols": ["homo_sapiens", "mus_musculus"]},
        {"type": "enum", "symbols": ["homo_sapiens", "drosophila_melanogaster"]},
        False,
    ),
    (
        {"type": "record", "fields": [{"name": "species", "type": "string"}]},
        {"type": "enum", "symbols": ["homo_sapiens"]},
        False,
    ),
    (
        {
            "type": "record",
            "fields": [
                {"name": "species", "type": "string"},
                {"name": "id", "type": "int"},
            ],
        },
        {"type": "record", "fields": [{"name": "species", "type": "string"}]},
        True,
    ),
    (
        {
            "type": "record",
            "fields": [
                {"name": "species", "type": "string"},
                {"name": "id", "type": "int"},
            ],
        },
        {"type": "record", "fields": [{"name": "species", "type": "int"}]},
        False,
    ),
    (
        {"type": "record", "fields": [{"name": "species", "type": "string"}]},
        {
            "type": "record",
            "fields": [
                {"name": "species", "type": "string"},
                {"name": "id", "type": "int"},
            ],
        },
        False,
    ),
]


@pytest.mark.parametrize("old,new,result", types)
def test_subtypes(old: schema.PropType, new: schema.PropType, result: bool) -> None:
    """Test is_subtype() function."""
    assert schema.is_subtype(old, new) == result


def test_avro_loading_subtype() -> None:
    """Confirm conversion of SALAD style names to avro when overriding."""
    path = get_data("tests/test_schema/avro_subtype.yml")
    assert path
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(path)
    assert isinstance(avsc_names, Names)
    assert avsc_names.get_name("com.example.derived_schema.ExtendedThing", None)


def test_avro_loading_subtype_bad() -> None:
    """Confirm subtype error when overriding incorrectly."""
    path = get_data("tests/test_schema/avro_subtype_bad.yml")
    assert path
    target_error = (
        r"Field name .*\/override_me already in use with incompatible type. "
        r"Any vs \['string', 'int'\]\."
    )
    with pytest.raises(SchemaParseException, match=target_error):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            path
        )
