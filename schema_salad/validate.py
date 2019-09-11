from __future__ import absolute_import

import logging
import pprint
from typing import (  # noqa: F401
    Any,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Union,
)

import six
from six.moves import range, urllib
from typing_extensions import Text  # pylint: disable=unused-import

from . import avro
from .exceptions import ClassValidationException, ValidationException
from .avro import schema  # noqa: F401
from .avro.schema import (  # pylint: disable=unused-import, no-name-in-module, import-error
    Schema,
)
from .sourceline import SourceLine, bullets, indent, strip_dup_lineno

# move to a regular typing import when Python 3.3-3.6 is no longer supported


_logger = logging.getLogger("salad")


def validate(
    expected_schema,  # type: Schema
    datum,  # type: Any
    identifiers=None,  # type: Optional[List[Text]]
    strict=False,  # type: bool
    foreign_properties=None,  # type: Optional[Set[Text]]
):
    # type: (...) -> bool
    if not identifiers:
        identifiers = []
    if not foreign_properties:
        foreign_properties = set()
    return validate_ex(
        expected_schema,
        datum,
        identifiers,
        strict=strict,
        foreign_properties=foreign_properties,
        raise_ex=False,
    )


INT_MIN_VALUE = -(1 << 31)
INT_MAX_VALUE = (1 << 31) - 1
LONG_MIN_VALUE = -(1 << 63)
LONG_MAX_VALUE = (1 << 63) - 1


def friendly(v):  # type: (Any) -> Any
    if isinstance(v, avro.schema.NamedSchema):
        return v.name
    if isinstance(v, avro.schema.ArraySchema):
        return "array of <{}>".format(friendly(v.items))
    elif isinstance(v, avro.schema.PrimitiveSchema):
        return v.type
    elif isinstance(v, avro.schema.UnionSchema):
        return " or ".join([friendly(s) for s in v.schemas])
    else:
        return v


def vpformat(datum):  # type: (Any) -> str
    a = pprint.pformat(datum)
    if len(a) > 160:
        a = a[0:160] + "[...]"
    return a


def validate_ex(
    expected_schema,  # type: Schema
    datum,  # type: Any
    identifiers=None,  # type: Optional[List[Text]]
    strict=False,  # type: bool
    foreign_properties=None,  # type: Optional[Set[Text]]
    raise_ex=True,  # type: bool
    strict_foreign_properties=False,  # type: bool
    logger=_logger,  # type: logging.Logger
    skip_foreign_properties=False,  # type: bool
):
    # type: (...) -> bool
    """Determine if a python datum is an instance of a schema."""

    if not identifiers:
        identifiers = []

    if not foreign_properties:
        foreign_properties = set()

    schema_type = expected_schema.type

    if schema_type == "null":
        if datum is None:
            return True
        else:
            if raise_ex:
                raise ValidationException(u"the value is not null")
            else:
                return False
    elif schema_type == "boolean":
        if isinstance(datum, bool):
            return True
        else:
            if raise_ex:
                raise ValidationException(u"the value is not boolean")
            else:
                return False
    elif schema_type == "string":
        if isinstance(datum, six.string_types):
            return True
        elif isinstance(datum, bytes):
            datum = datum.decode(u"utf-8")
            return True
        else:
            if raise_ex:
                raise ValidationException(u"the value is not string")
            else:
                return False
    elif schema_type == "int":
        if (
            isinstance(datum, six.integer_types)
            and INT_MIN_VALUE <= datum <= INT_MAX_VALUE
        ):
            return True
        else:
            if raise_ex:
                raise ValidationException(u"`{}` is not int".format(vpformat(datum)))
            else:
                return False
    elif schema_type == "long":
        if (
            isinstance(datum, six.integer_types)
        ) and LONG_MIN_VALUE <= datum <= LONG_MAX_VALUE:
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    u"the value `{}` is not long".format(vpformat(datum))
                )
            else:
                return False
    elif schema_type in ["float", "double"]:
        if isinstance(datum, six.integer_types) or isinstance(datum, float):
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    u"the value `{}` is not float or double".format(vpformat(datum))
                )
            else:
                return False
    elif isinstance(expected_schema, avro.schema.EnumSchema):
        if expected_schema.name == "Any":
            if datum is not None:
                return True
            else:
                if raise_ex:
                    raise ValidationException(u"'Any' type must be non-null")
                else:
                    return False
        if not isinstance(datum, six.string_types):
            if raise_ex:
                raise ValidationException(
                    u"value is a {} but expected a string".format(
                        (type(datum).__name__)
                    )
                )
            else:
                return False
        if expected_schema.name == "Expression":
            if "$(" in datum or "${" in datum:
                return True
            if raise_ex:
                raise ValidationException(
                    u"value `%s` does not contain an expression in the form $() or ${}"
                    % datum
                )
            else:
                return False
        if datum in expected_schema.symbols:
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    u"the value {} is not a valid {}, expected {}{}".format(
                        vpformat(datum),
                        expected_schema.name,
                        "one of " if len(expected_schema.symbols) > 1 else "",
                        "'" + "', '".join(expected_schema.symbols) + "'",
                    )
                )
            else:
                return False
    elif isinstance(expected_schema, avro.schema.ArraySchema):
        if isinstance(datum, MutableSequence):
            for i, d in enumerate(datum):
                try:
                    sl = SourceLine(datum, i, ValidationException)
                    if not validate_ex(
                        expected_schema.items,
                        d,
                        identifiers,
                        strict=strict,
                        foreign_properties=foreign_properties,
                        raise_ex=raise_ex,
                        strict_foreign_properties=strict_foreign_properties,
                        logger=logger,
                        skip_foreign_properties=skip_foreign_properties,
                    ):
                        return False
                except ValidationException as v:
                    if raise_ex:
                        raise sl.makeError(
                            six.text_type(
                                "item is invalid because\n{}".format(indent(str(v)))
                            )
                        )
                    else:
                        return False
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    u"the value {} is not a list, expected list of {}".format(
                        vpformat(datum), friendly(expected_schema.items)
                    )
                )
            else:
                return False
    elif isinstance(expected_schema, avro.schema.UnionSchema):
        for s in expected_schema.schemas:
            if validate_ex(
                s,
                datum,
                identifiers,
                strict=strict,
                raise_ex=False,
                strict_foreign_properties=strict_foreign_properties,
                logger=logger,
                skip_foreign_properties=skip_foreign_properties,
            ):
                return True

        if not raise_ex:
            return False

        errors = []  # type: List[Text]
        checked = []
        for s in expected_schema.schemas:
            if isinstance(datum, MutableSequence) and not isinstance(
                s, avro.schema.ArraySchema
            ):
                continue
            elif isinstance(datum, MutableMapping) and not isinstance(
                s, avro.schema.RecordSchema
            ):
                continue
            elif isinstance(
                datum, (bool, six.integer_types, float, six.string_types)
            ) and isinstance(s, (avro.schema.ArraySchema, avro.schema.RecordSchema)):
                continue
            elif datum is not None and s.type == "null":
                continue

            checked.append(s)
            try:
                validate_ex(
                    s,
                    datum,
                    identifiers,
                    strict=strict,
                    foreign_properties=foreign_properties,
                    raise_ex=True,
                    strict_foreign_properties=strict_foreign_properties,
                    logger=logger,
                    skip_foreign_properties=skip_foreign_properties,
                )
            except ClassValidationException:
                raise
            except ValidationException as e:
                errors.append(six.text_type(e))
        if bool(errors):
            raise ValidationException(
                bullets(
                    [
                        "tried {} but\n{}".format(
                            friendly(checked[i]), indent(errors[i])
                        )
                        for i in range(0, len(errors))
                    ],
                    "- ",
                )
            )
        else:
            raise ValidationException(
                "value is a {}, expected {}".format(
                    type(datum).__name__, friendly(expected_schema)
                )
            )

    elif isinstance(expected_schema, avro.schema.RecordSchema):
        if not isinstance(datum, MutableMapping):
            if raise_ex:
                raise ValidationException(u"is not a dict")
            else:
                return False

        classmatch = None
        for f in expected_schema.fields:
            if f.name in ("class",):
                d = datum.get(f.name)
                if not d:
                    if raise_ex:
                        raise ValidationException(u"Missing '{}' field".format(f.name))
                    else:
                        return False
                if expected_schema.name != d:
                    if raise_ex:
                        raise ValidationException(
                            u"Expected class '{}' but this is '{}'".format(
                                expected_schema.name, d
                            )
                        )
                    else:
                        return False
                classmatch = d
                break

        errors = []
        for f in expected_schema.fields:
            if f.name in ("class",):
                continue

            if f.name in datum:
                fieldval = datum[f.name]
            else:
                try:
                    fieldval = f.default
                except KeyError:
                    fieldval = None

            try:
                sl = SourceLine(datum, f.name, six.text_type)
                if not validate_ex(
                    f.type,
                    fieldval,
                    identifiers,
                    strict=strict,
                    foreign_properties=foreign_properties,
                    raise_ex=raise_ex,
                    strict_foreign_properties=strict_foreign_properties,
                    logger=logger,
                    skip_foreign_properties=skip_foreign_properties,
                ):
                    return False
            except ValidationException as v:
                if f.name not in datum:
                    errors.append(u"missing required field `{}`".format(f.name))
                else:
                    errors.append(
                        sl.makeError(
                            u"the `{}` field is not valid because\n{}".format(
                                f.name, indent(str(v))
                            )
                        )
                    )

        for d in datum:
            found = False
            for f in expected_schema.fields:
                if d == f.name:
                    found = True
            if not found:
                sl = SourceLine(datum, d, six.text_type)
                if d is None:
                    err = sl.makeError(u"mapping with implicit null key")
                    if strict:
                        errors.append(err)
                    else:
                        logger.warning(err)
                    continue
                if (
                    d not in identifiers
                    and d not in foreign_properties
                    and d[0] not in ("@", "$")
                ):
                    if (
                        (d not in identifiers and strict)
                        and (
                            d not in foreign_properties
                            and strict_foreign_properties
                            and not skip_foreign_properties
                        )
                        and not raise_ex
                    ):
                        return False
                    split = urllib.parse.urlsplit(d)
                    if split.scheme:
                        if not skip_foreign_properties:
                            err = sl.makeError(
                                u"unrecognized extension field `{}`{}.{}".format(
                                    d,
                                    " and strict_foreign_properties checking is enabled"
                                    if strict_foreign_properties
                                    else "",
                                    "\nForeign properties from $schemas:\n  {}".format(
                                        "\n  ".join(sorted(foreign_properties))
                                    )
                                    if len(foreign_properties) > 0
                                    else "",
                                )
                            )
                            if strict_foreign_properties:
                                errors.append(err)
                            elif len(foreign_properties) > 0:
                                logger.warning(strip_dup_lineno(err))
                    else:
                        err = sl.makeError(
                            u"invalid field `{}`, expected one of: {}".format(
                                d,
                                ", ".join(
                                    "'{}'".format(fn.name)
                                    for fn in expected_schema.fields
                                ),
                            )
                        )
                        if strict:
                            errors.append(err)
                        else:
                            logger.warning(err)

        if bool(errors):
            if raise_ex:
                if classmatch:
                    raise ClassValidationException(bullets(errors, "* "))
                else:
                    raise ValidationException(bullets(errors, "* "))
            else:
                return False
        else:
            return True
    if raise_ex:
        raise ValidationException(u"Unrecognized schema_type {}".format(schema_type))
    else:
        return False
