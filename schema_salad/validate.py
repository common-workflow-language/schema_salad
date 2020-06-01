import logging
import pprint
from typing import Any, List, MutableMapping, MutableSequence, Optional, Set
from urllib.parse import urlsplit

from . import avro
from .avro.schema import Schema  # pylint: disable=no-name-in-module, import-error
from .exceptions import (
    ClassValidationException,
    SchemaSaladException,
    ValidationException,
)
from .sourceline import SourceLine

_logger = logging.getLogger("salad")


def validate(
    expected_schema: Schema,
    datum: Any,
    identifiers: Optional[List[str]] = None,
    strict: bool = False,
    foreign_properties: Optional[Set[str]] = None,
) -> bool:
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
    expected_schema: Schema,
    datum,  # type: Any
    identifiers=None,  # type: Optional[List[str]]
    strict=False,  # type: bool
    foreign_properties=None,  # type: Optional[Set[str]]
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
                raise ValidationException("the value is not null")
            else:
                return False
    elif schema_type == "boolean":
        if isinstance(datum, bool):
            return True
        else:
            if raise_ex:
                raise ValidationException("the value is not boolean")
            else:
                return False
    elif schema_type == "string":
        if isinstance(datum, str):
            return True
        elif isinstance(datum, bytes):
            return True
        else:
            if raise_ex:
                raise ValidationException("the value is not string")
            else:
                return False
    elif schema_type == "int":
        if isinstance(datum, int) and INT_MIN_VALUE <= datum <= INT_MAX_VALUE:
            return True
        else:
            if raise_ex:
                raise ValidationException("`{}` is not int".format(vpformat(datum)))
            else:
                return False
    elif schema_type == "long":
        if (isinstance(datum, int)) and LONG_MIN_VALUE <= datum <= LONG_MAX_VALUE:
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    "the value `{}` is not long".format(vpformat(datum))
                )
            else:
                return False
    elif schema_type in ["float", "double"]:
        if isinstance(datum, int) or isinstance(datum, float):
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    "the value `{}` is not float or double".format(vpformat(datum))
                )
            else:
                return False
    elif isinstance(expected_schema, avro.schema.EnumSchema):
        if expected_schema.name == "Any":
            if datum is not None:
                return True
            else:
                if raise_ex:
                    raise ValidationException("'Any' type must be non-null")
                else:
                    return False
        if not isinstance(datum, str):
            if raise_ex:
                raise ValidationException(
                    "value is a {} but expected a string".format((type(datum).__name__))
                )
            else:
                return False
        if expected_schema.name == "Expression":
            if "$(" in datum or "${" in datum:
                return True
            if raise_ex:
                raise ValidationException(
                    "value `%s` does not contain an expression in the form $() or ${}"
                    % datum
                )
            else:
                return False
        if datum in expected_schema.symbols:
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    "the value {} is not a valid {}, expected {}{}".format(
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
                        raise ValidationException("item is invalid because", sl, [v])
                    else:
                        return False
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    "the value {} is not a list, expected list of {}".format(
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

        errors = []  # type: List[SchemaSaladException]
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
            elif isinstance(datum, (bool, int, float, str)) and isinstance(
                s, (avro.schema.ArraySchema, avro.schema.RecordSchema)
            ):
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
                errors.append(e)
        if bool(errors):
            raise ValidationException(
                "",
                None,
                [
                    ValidationException(
                        "tried {} but".format(friendly(check)), None, [err]
                    )
                    for (check, err) in zip(checked, errors)
                ],
                "-",
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
                raise ValidationException("is not a dict")
            else:
                return False

        classmatch = None
        for f in expected_schema.fields:
            if f.name in ("class",):
                d = datum.get(f.name)
                if not d:
                    if raise_ex:
                        raise ValidationException("Missing '{}' field".format(f.name))
                    else:
                        return False
                if expected_schema.name != d:
                    if raise_ex:
                        raise ValidationException(
                            "Expected class '{}' but this is '{}'".format(
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
                sl = SourceLine(datum, f.name, str)
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
                    errors.append(
                        ValidationException(
                            "missing required field `{}`".format(f.name)
                        )
                    )
                else:
                    errors.append(
                        ValidationException(
                            "the `{}` field is not valid because".format(f.name),
                            sl,
                            [v],
                        )
                    )

        for d in datum:
            found = False
            for f in expected_schema.fields:
                if d == f.name:
                    found = True
            if not found:
                sl = SourceLine(datum, d, str)
                if d is None:
                    err = ValidationException("mapping with implicit null key", sl)
                    if strict:
                        errors.append(err)
                    else:
                        logger.warning(err.as_warning())
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
                    split = urlsplit(d)
                    if split.scheme:
                        if not skip_foreign_properties:
                            err = ValidationException(
                                "unrecognized extension field `{}`{}.{}".format(
                                    d,
                                    " and strict_foreign_properties checking is enabled"
                                    if strict_foreign_properties
                                    else "",
                                    "\nForeign properties from $schemas:\n  {}".format(
                                        "\n  ".join(sorted(foreign_properties))
                                    )
                                    if len(foreign_properties) > 0
                                    else "",
                                ),
                                sl,
                            )
                            if strict_foreign_properties:
                                errors.append(err)
                            elif len(foreign_properties) > 0:
                                logger.warning(err.as_warning())
                    else:
                        err = ValidationException(
                            "invalid field `{}`, expected one of: {}".format(
                                d,
                                ", ".join(
                                    "'{}'".format(fn.name)
                                    for fn in expected_schema.fields
                                ),
                            ),
                            sl,
                        )
                        if strict:
                            errors.append(err)
                        else:
                            logger.warning(err.as_warning())

        if bool(errors):
            if raise_ex:
                if classmatch:
                    raise ClassValidationException("", None, errors, "*")
                else:
                    raise ValidationException("", None, errors, "*")
            else:
                return False
        else:
            return True
    if raise_ex:
        raise ValidationException("Unrecognized schema_type {}".format(schema_type))
    else:
        return False
