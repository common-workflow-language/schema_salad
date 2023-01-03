from typing import Dict, Optional, Union

from rdflib.graph import Graph

from schema_salad.avro.schema import Names
from schema_salad.schema import load_schema

from .util import get_data


def test_misc() -> None:
    path = get_data("tests/test_schema/no_field_schema.yml")
    assert path
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(path)
    assert isinstance(avsc_names, Names)


def test_load_schema_cache() -> None:
    schemaid = "http://commonwl.org/schema_salad/test/schema.yml"

    path1 = get_data("tests/test_schema/misc_schema_v1.yml")
    assert path1

    with open(path1) as f:
        cache1: Optional[Dict[str, Union[str, Graph, bool]]] = {schemaid: f.read()}

    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        schemaid, cache=cache1
    )
    assert isinstance(avsc_names, Names)
    assert "EmptyType" not in document_loader.vocab

    path2 = get_data("tests/test_schema/misc_schema_v2.yml")
    assert path2

    with open(path2) as f:
        cache2: Optional[Dict[str, Union[str, Graph, bool]]] = {schemaid: f.read()}

    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        schemaid, cache=cache2
    )
    assert isinstance(avsc_names, Names)
    assert "EmptyType" in document_loader.vocab
