import re
import unittest
from os.path import normpath

import six

from schema_salad.main import (reformat_yaml_exception_message,
                               to_one_line_messages)
from schema_salad.schema import load_and_validate, load_schema
from schema_salad.sourceline import strip_dup_lineno
from schema_salad.validate import ValidationException

from .util import get_data


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
                msgs = to_one_line_messages(str(e)).splitlines()
                self.assertEqual(len(msgs), 2)
                m = re.match(r'^(.+:\d+:\d+:)(.+)$', msgs[0])
                self.assertTrue(msgs[0].endswith(src+":11:7: invalid field `invalid_field`, expected one of: 'loadContents', 'position', 'prefix', 'separate', 'itemSeparator', 'valueFrom', 'shellQuote'"))
                self.assertTrue(msgs[1].endswith(src+":12:7: invalid field `another_invalid_field`, expected one of: 'loadContents', 'position', 'prefix', 'separate', 'itemSeparator', 'valueFrom', 'shellQuote'"))
                print("\n", e)
                raise

    def test_print_oneline_for_invalid_yaml(self):
        # Issue #137
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        src = "test16.cwl"
        with self.assertRaises(RuntimeError):
            try:
                load_and_validate(document_loader, avsc_names,
                                  six.text_type(get_data("tests/test_schema/"+src)), True)
            except RuntimeError as e:
                msg = reformat_yaml_exception_message(strip_dup_lineno(six.text_type(e)))
                msg = to_one_line_messages(msg)
                self.assertTrue(msg.endswith(src+":11:1: could not find expected \':\'"))
                print("\n", e)
                raise

    def test_print_oneline_for_errors_in_the_same_line(self):
        # Issue #136
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        src = "test17.cwl"
        with self.assertRaises(ValidationException):
            try:
                load_and_validate(document_loader, avsc_names,
                                  six.text_type(get_data("tests/test_schema/"+src)), True)
            except ValidationException as e:
                msgs = to_one_line_messages(str(e)).splitlines()
                assert len(msgs) == 2, msgs
                self.assertTrue(msgs[0].endswith(src+":14:5: missing required field `id`"))
                self.assertTrue(msgs[1].endswith(src+":14:5: invalid field `aa`, expected one of: 'label', 'secondaryFiles', 'format', 'streamable', 'doc', 'id', 'outputBinding', 'type'"))
                print("\n", e)
                raise

    def test_print_oneline_for_errors_in_resolve_ref(self):
        # Issue #141
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        src = "test18.cwl"
        fullpath = normpath(get_data("tests/test_schema/"+src))
        with self.assertRaises(ValidationException):
            try:
                load_and_validate(document_loader, avsc_names,
                                  six.text_type(fullpath), True)
            except ValidationException as e:
                msgs = to_one_line_messages(str(strip_dup_lineno(six.text_type(e)))).splitlines()
                # convert Windows path to Posix path
                if '\\' in fullpath:
                    fullpath = '/'+fullpath.lower().replace('\\', '/')
                self.assertEqual(len(msgs), 2)
                print("\n", e)
                assert msgs[0].endswith(
                    src + ':9:1: checking field `outputs`')
                assert msgs[1].endswith(
                    src + ':14:5: Field `type` references unknown identifier '
                    '`Filea`, tried file://%s#Filea' % (fullpath))
                raise

    def test_for_invalid_yaml1(self):
        # Issue 143
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        src = "test16.cwl"
        with self.assertRaises(RuntimeError):
            try:
                load_and_validate(document_loader, avsc_names,
                                  six.text_type(get_data("tests/test_schema/"+src)), True)
            except RuntimeError as e:
                msg = reformat_yaml_exception_message(strip_dup_lineno(six.text_type(e)))
                msgs = msg.splitlines()
                self.assertEqual(len(msgs), 2)
                self.assertTrue(msgs[0].endswith(src+":10:7: while scanning a simple key"))
                self.assertTrue(msgs[1].endswith(src+":11:1:   could not find expected ':'"))
                print("\n", e)
                raise

    def test_for_invalid_yaml2(self):
        # Issue 143
        document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
            get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

        src = "test19.cwl"
        try:
            load_and_validate(document_loader, avsc_names,
                              six.text_type(get_data("tests/test_schema/"+src)), True)
        except RuntimeError as e:
            msg = reformat_yaml_exception_message(strip_dup_lineno(six.text_type(e)))
            self.assertTrue(msg.endswith(src+":2:1: expected <block end>, but found ':'")
                            or msg.endswith(src+":2:1: expected <block end>, but found u':'"))
            return
        except ValidationException as e:
            msgs = str(strip_dup_lineno(six.text_type(e)))
            print(msgs)
            # weird splits due to differing path length on MS Windows & during the release tests
            assert "{}:2:1: Object".format(src) in msgs
            assert "is not valid because" in msgs
            assert "`CommandLineTool`" in msgs
            assert "mapping with" in msgs
            assert "implicit" in msgs
            assert "null key" in msgs
            return
        assert False, "Missing RuntimeError or ValidationException"
