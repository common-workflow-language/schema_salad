"""Confirm subtypes."""
from schema_salad.avro import schema

import pytest

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
]


@pytest.mark.parametrize("old,new,result", types)
def test_subtypes(old: schema.PropType, new: schema.PropType, result: bool) -> None:
    """Test is_subtype() function."""
    assert schema.is_subtype(old, new) == result
