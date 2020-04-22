import re
from os.path import normpath

import pytest

from schema_salad.exceptions import ValidationException, to_one_line_messages
from schema_salad.schema import load_and_validate, load_schema

from .util import get_data


def test_print_oneline():
    # Issue #135
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    )

    src = "test15.cwl"
    with pytest.raises(ValidationException):
        try:
            load_and_validate(
                document_loader,
                avsc_names,
                str(get_data("tests/test_schema/" + src)),
                True,
            )
        except ValidationException as e:
            msgs = to_one_line_messages(e).splitlines()
            assert len(msgs) == 2
            assert msgs[0].endswith(
                src + ":11:7: invalid field `invalid_field`, expected one of: "
                "'loadContents', 'position', 'prefix', 'separate', "
                "'itemSeparator', 'valueFrom', 'shellQuote'"
            )
            assert msgs[1].endswith(
                src + ":12:7: invalid field `another_invalid_field`, expected one of: "
                "'loadContents', 'position', 'prefix', 'separate', 'itemSeparator', "
                "'valueFrom', 'shellQuote'"
            )
            print("\n", e)
            raise


def test_print_oneline_for_invalid_yaml():
    # Issue #137
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    )

    src = "test16.cwl"
    with pytest.raises(ValidationException):
        try:
            load_and_validate(
                document_loader,
                avsc_names,
                str(get_data("tests/test_schema/" + src)),
                True,
            )
        except ValidationException as e:
            msg = to_one_line_messages(e)
            assert msg.endswith(src + ":11:1: could not find expected ':'")
            print("\n", e)
            raise


def test_print_oneline_for_errors_in_the_same_line():
    # Issue #136
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    )

    src = "test17.cwl"
    with pytest.raises(ValidationException):
        try:
            load_and_validate(
                document_loader,
                avsc_names,
                str(get_data("tests/test_schema/" + src)),
                True,
            )
        except ValidationException as e:
            msgs = to_one_line_messages(e).splitlines()
            assert len(msgs) == 2, msgs
            assert msgs[0].endswith(src + ":14:5: missing required field `id`")
            assert msgs[1].endswith(
                src + ":14:5: invalid field `aa`, expected one of: 'label', "
                "'secondaryFiles', 'format', 'streamable', 'doc', 'id', "
                "'outputBinding', 'type'"
            )
            print("\n", e)
            raise


def test_print_oneline_for_errors_in_resolve_ref():
    # Issue #141
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    )

    src = "test18.cwl"
    fullpath = normpath(get_data("tests/test_schema/" + src))
    with pytest.raises(ValidationException):
        try:
            load_and_validate(document_loader, avsc_names, str(fullpath), True)
        except ValidationException as e:
            msg = to_one_line_messages(e)
            # convert Windows path to Posix path
            if "\\" in fullpath:
                fullpath = "/" + fullpath.lower().replace("\\", "/")
            print("\n", e)
            assert msg.endswith(
                src + ":14:5: Field `type` references unknown identifier "
                "`Filea`, tried file://%s#Filea" % (fullpath)
            )
            raise


def test_for_invalid_yaml1():
    # Issue 143
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    )

    src = "test16.cwl"
    with pytest.raises(ValidationException):
        try:
            load_and_validate(
                document_loader,
                avsc_names,
                str(get_data("tests/test_schema/" + src)),
                True,
            )
        except ValidationException as e:
            msg = str(e)
            assert re.search(src + r":10:7: while scanning a\s+simple\s+key", msg, re.M)
            assert re.search(
                src + r":11:1:   could not\s+find\s+expected ':'$", msg, re.M
            )
            print("\n", e)
            raise


def test_for_invalid_yaml2():
    # Issue 143
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    )

    src = "test19.cwl"
    with pytest.raises(ValidationException):
        try:
            load_and_validate(
                document_loader,
                avsc_names,
                str(get_data("tests/test_schema/" + src)),
                True,
            )
        except ValidationException as e:
            msg = str(e)
            assert (
                msg.endswith("expected <block end>, but found ':'")
                or msg.endswith("expected <block end>, but found u':'")
                or re.search(r"mapping with\s+implicit\s+null key$", msg, re.M)
            )
            print("\n", e)
            raise
