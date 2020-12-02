from schema_salad.avro.schema import Names, SchemaParseException
from schema_salad.ref_resolver import Loader
from schema_salad.schema import load_and_validate, load_schema

from .util import get_data

def test_avro_loading():
    path = get_data("tests/test_schema/avro_naming.yml")
    assert path
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(path)
    
