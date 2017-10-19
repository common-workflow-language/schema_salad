from .util import get_data
import unittest
from schema_salad.main import to_one_line_messages
from schema_salad.schema import load_schema, load_and_validate
from schema_salad.validate import ValidationException
import six

class TestPrintOneline(unittest.TestCase):
    def test_print_oneline(self):
        # Issue #135
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        src = "test15.cwl"
        with self.assertRaises(ValidationException):
            try:
                load_and_validate(document_loader, avsc_names,
                                  six.text_type(get_data("tests/test_schema/"+src)), True)
            except ValidationException as e:
                msgs = to_one_line_messages(str(e)).split("\n")
                self.assertEqual(len(msgs), 2)
                self.assertTrue(msgs[0].endswith(src+":11:7: invalid field `invalid_field`, expected one of: 'loadContents', 'position', 'prefix', 'separate', 'itemSeparator', 'valueFrom', 'shellQuote'"))
                self.assertTrue(msgs[1].endswith(src+":12:7: invalid field `another_invalid_field`, expected one of: 'loadContents', 'position', 'prefix', 'separate', 'itemSeparator', 'valueFrom', 'shellQuote'"))
                print("\n", e)
                raise
