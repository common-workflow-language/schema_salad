from __future__ import absolute_import, print_function

import unittest

import six
import schema_salad
from schema_salad.avro.schema import Names
from schema_salad.schema import load_and_validate, load_schema
from schema_salad.validate import ValidationException

from .util import get_data


class TestErrors(unittest.TestCase):
    def test_errors(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        for t in ("test_schema/test1.cwl",
                  "test_schema/test2.cwl",
                  "test_schema/test3.cwl",
                  "test_schema/test4.cwl",
                  "test_schema/test5.cwl",
                  "test_schema/test6.cwl",
                  "test_schema/test7.cwl",
                  "test_schema/test8.cwl",
                  "test_schema/test9.cwl",
                  "test_schema/test10.cwl",
                  "test_schema/test11.cwl",
                  "test_schema/test15.cwl"):
            with self.assertRaises(ValidationException):
                try:
                    load_and_validate(document_loader, avsc_names,
                            six.text_type(get_data("tests/"+t)), True)
                except ValidationException as e:
                    print("\n", e)
                    raise

    def test_error_message1(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test1.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertRegex(str(e.exception), r'''
^.+test1\.cwl:2:1: Object `.+test1\.cwl` is
                                              not valid because
                                                tried `Workflow` but
                                                  \* missing required field `inputs`
                                                  \* missing required field `outputs`
                                                  \* missing required field `steps`'''[1:])

    @unittest.skip("See https://github.com/common-workflow-language/common-workflow-language/issues/734")
    def test_errors_previously_defined_dict_key(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        for t in ("test_schema/test12.cwl",
                  "test_schema/test13.cwl",
                  "test_schema/test14.cwl"):
            with self.assertRaises(ValidationException):
                try:
                    load_and_validate(document_loader, avsc_names,
                            six.text_type(get_data("tests/"+t)), True)
                except ValidationException as e:
                    print("\n", e)
                    raise

    def test_bad_schema(self):
        self.assertEqual(1, schema_salad.main.main(
            argsl=[get_data("tests/bad_schema.yml")]))
        self.assertEqual(1, schema_salad.main.main(
            argsl=["--print-avro", get_data("tests/bad_schema.yml")]))

    def test_bad_schema2(self):
        self.assertEqual(1, schema_salad.main.main(
            argsl=[get_data("tests/bad_schema2.yml")]))
