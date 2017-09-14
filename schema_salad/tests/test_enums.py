from __future__ import absolute_import
from __future__ import print_function
from .util import get_data
import unittest
from schema_salad.schema import load_schema, load_and_validate
from schema_salad.validate import ValidationException
from avro.schema import Names
import six

class TestEnums(unittest.TestCase):
    def test_errors(self):        
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/symbols-with-spaces.yml"))
        context = document_loader.ctx
        assert "Metabolite_table" in context
        assert "table type" in context

if __name__ == "__main__":
    unittest.main()
