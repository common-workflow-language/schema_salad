from schema_salad.avro.schema import Names
from schema_salad.schema import load_schema

from .util import get_data


def test_misc() -> None:
    path = get_data("tests/test_schema/no_field_schema.yml")
    assert path
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(path)
    assert isinstance(avsc_names, Names)
