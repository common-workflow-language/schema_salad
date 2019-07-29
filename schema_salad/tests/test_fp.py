from __future__ import absolute_import, print_function

import six

from schema_salad.schema import load_and_validate, load_schema
from schema_salad.validate import ValidationException

from .util import get_data
import pytest


def test_fp():
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        get_data(u"tests/test_schema/CommonWorkflowLanguage.yml")
    )

    for t in (
        "foreign/foreign_prop1.cwl",
        "foreign/foreign_prop2.cwl",
        "foreign/foreign_prop3.cwl",
        "foreign/foreign_prop4.cwl",
        "foreign/foreign_prop5.cwl",
        "foreign/foreign_prop6.cwl",
        "foreign/foreign_prop7.cwl",
    ):
        load_and_validate(
            document_loader,
            avsc_names,
            six.text_type(get_data("tests/" + t)),
            True,
            strict_foreign_properties=False,
        )

    for t in (
        "foreign/foreign_prop1.cwl",
        "foreign/foreign_prop2.cwl",
        "foreign/foreign_prop4.cwl",
        "foreign/foreign_prop5.cwl",
    ):
        with pytest.raises(ValidationException):
            try:
                print (t)
                load_and_validate(
                    document_loader,
                    avsc_names,
                    six.text_type(get_data("tests/" + t)),
                    True,
                    strict_foreign_properties=True,
                )
            except ValidationException as e:
                print ("\n", e)
                raise
