from __future__ import absolute_import, print_function

import unittest
import re

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
        self.assertTrue(re.match(r'''
^.+test1\.cwl:2:1: Object\s+`.+test1\.cwl`\s+is\s+not valid because\s+tried `Workflow`\s+but
\s+\* missing\s+required\s+field\s+`inputs`
\s+\* missing\s+required\s+field\s+`outputs`
\s+\* missing\s+required\s+field\s+`steps`$'''[1:],
                                 str(e.exception)))

    def test_error_message2(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test2.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test2\.cwl:2:1: Field `class`\s+contains\s+undefined\s+reference to
\s+`file://.+/schema_salad/tests/test_schema/xWorkflow`$'''[1:],
                                 str(e.exception)),
                        str(e.exception) + ' is not matched.')

    def test_error_message3(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test3.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test3\.cwl:5:1: checking field\s+`outputs`
.+test3\.cwl:6:3:   checking object\s+`.+test3\.cwl#bar`
\s+Field `type`\s+references\s+unknown\s+identifier\s+`xstring`,\s+tried
\s+file://.+/tests/test_schema/test3\.cwl#xstring$'''[1:],
                                 str(e.exception)),
                        str(e.exception) + ' is not matched.')

    def test_error_message4(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test4.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test4\.cwl:5:1: checking field\s+`outputs`
.+test4\.cwl:6:3:   checking object\s+`.+test4\.cwl#bar`
\s+`type` field is\s+int,\s+expected\s+string,\s+list, or\s+a\s+dict.$'''[1:],
                                 str(e.exception)),
                        str(e.exception) + ' is not matched.')

    def test_error_message5(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test5.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test5\.cwl:2:1: Object\s+`.+test5\.cwl`\s+is\s+not valid because
\s+tried `Workflow`\s+but
.+test5\.cwl:7:1:     the `steps`\s+field\s+is\s+not valid\s+because
\s+tried array\s+of\s+<WorkflowStep>\s+but
.+test5\.cwl:7:9:         item is\s+invalid because
\s+is not a\s+dict$'''[1:], str(e.exception)), str(e.exception) + ' is not matched.')

    def test_error_message7(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test7.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test7\.cwl:2:1: Object\s+`.+test7\.cwl`\s+is\s+not valid because
\s+tried `Workflow`\s+but
.+test7\.cwl:7:1:     the `steps`\s+field\s+is\s+not valid\s+because
\s+tried array\s+of\s+<WorkflowStep>\s+but
.+test7\.cwl:8:3:         item is\s+invalid because
\s+\* missing\s+required\s+field `run`
.+test7\.cwl:9:5:           \* invalid\s+field\s+`scatter_method`,\s+expected one of:\s+'id', 'in', 'out',\s+'requirements',\s+'hints', 'label',\s+'doc',\s+'run',\s+'scatter',\s+'scatterMethod'$'''[1:], str(e.exception)), str(e.exception) + ' is not matched.')

    def test_error_message8(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test8.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test8\.cwl:7:1: checking field\s+`steps`
.+test8\.cwl:8:3:   checking object\s+`.+test8\.cwl#step1`
.+test8\.cwl:9:5:     Field\s+`scatterMethod`\s+contains\s+undefined\s+reference to
\s+`file:///.+/tests/test_schema/abc`$'''[1:],
                                 str(e.exception)), str(e.exception) + ' is not matched.')

    def test_error_message9(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test9.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test9\.cwl:7:1: checking field\s+`steps`
.+test9\.cwl:8:3:   checking object\s+`.+test9\.cwl#step1`
.+test9\.cwl:9:5:     `scatterMethod`\s+field\s+is int,\s+expected\s+string,\s+list, or a dict.$'''[1:],
                                 str(e.exception)), str(e.exception) + ' is not matched.')

    def test_error_message10(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test10.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test10\.cwl:2:1: Object\s+`.+test10\.cwl`\s+is not valid because
\s+tried `Workflow`\s+but
.+test10\.cwl:7:1:     the `steps`\s+field is\s+not valid\s+because
\s+tried array\s+of\s+<WorkflowStep>\s+but
.+test10\.cwl:8:3:         item is\s+invalid because
\s+\* missing\s+required\s+field `run`
.+test10\.cwl:9:5:           \* the\s+`scatterMethod`\s+field is\s+not valid\s+because
\s+value\s+is a\s+CommentedSeq,\s+expected\s+null\s+or\s+ScatterMethod$'''[1:],
                                 str(e.exception)), str(e.exception) + ' is not matched.')

    def test_error_message11(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test11.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test11\.cwl:7:1: checking field\s+`steps`
.+test11\.cwl:8:3:   checking object\s+`.+test11\.cwl#step1`
.+test11\.cwl:9:5:     Field `run`\s+contains\s+undefined\s+reference to
\s+`file://.+/tests/test_schema/blub\.cwl`$'''[1:],
                                 str(e.exception)), str(e.exception) + ' is not matched.')

    def test_error_message15(self):
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        t = "test_schema/test15.cwl"
        with self.assertRaises(ValidationException) as e:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/"+t)), True)
        self.assertTrue(re.match(r'''
^.+test15\.cwl:3:1:\s+Object\s+`.+test15\.cwl`\s+is not valid because
\s+tried\s+`CommandLineTool`\s+but
.+test15\.cwl:6:1:\s+the `inputs`\s+field\s+is not valid\s+because
.+test15\.cwl:7:3:\s+item is\s+invalid\s+because
.+test15\.cwl:9:5:\s+the\s+`inputBinding`\s+field is not\s+valid\s+because
.+tried\s+CommandLineBinding\s+but
.+test15\.cwl:11:7:             \*\s+invalid field\s+`invalid_field`,\s+expected one\s+of:\s+'loadContents',\s+'position',\s+'prefix',\s+'separate',\s+'itemSeparator',\s+'valueFrom',\s+'shellQuote'
.+test15\.cwl:12:7:             \*\s+invalid field\s+`another_invalid_field`,\s+expected one\s+of:\s+'loadContents',\s+'position',\s+'prefix',\s+'separate',\s+'itemSeparator',\s+'valueFrom',\s+'shellQuote'$'''[1:],
                                 str(e.exception)), str(e.exception) + ' is not matched.')

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
