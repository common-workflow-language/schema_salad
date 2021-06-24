from schema_salad.schema import load_schema

from .util import get_data


def test_avro_loading() -> None:
    path = get_data("tests/test_schema/avro_naming.yml")
    assert path
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(path)
