import logging
import pprint
from typing import Any, List, Mapping, MutableMapping, MutableSequence, Optional, Set
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
    vocab: Optional[Mapping[str, str]] = None,
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
        vocab=vocab,
    )


INT_MIN_VALUE = -(1 << 31)
INT_MAX_VALUE = (1 << 31) - 1
LONG_MIN_VALUE = -(1 << 63)
LONG_MAX_VALUE = (1 << 63) - 1


def avro_shortname(name: str) -> str:
    """Produce an avro friendly short name."""
    return name.split(".")[-1]


saladp = "https://w3id.org/cwl/salad#"
primitives = {
    "http://www.w3.org/2001/XMLSchema#string": "string",
    "http://www.w3.org/2001/XMLSchema#boolean": "boolean",
    "http://www.w3.org/2001/XMLSchema#int": "int",
    "http://www.w3.org/2001/XMLSchema#long": "long",
    "http://www.w3.org/2001/XMLSchema#float": "float",
    "http://www.w3.org/2001/XMLSchema#double": "double",
    saladp + "null": "null",
    saladp + "enum": "enum",
    saladp + "array": "array",
    saladp + "record": "record",
}


def avro_type_name(url: str) -> str:
    """
    Turn a URL into an Avro-safe name.

    If the URL has no fragment, return this plain URL.

    Extract either the last part of the URL fragment past the slash, otherwise
    the whole fragment.
    """
    global primitives

    if url in primitives:
        return primitives[url]

    u = urlsplit(url)
    joined = filter(
        lambda x: x,
        list(reversed(u.netloc.split("."))) + u.path.split("/") + u.fragment.split("/"),
    )
    return ".".join(joined)


def friendly(v):  # type: (Any) -> Any
    if isinstance(v, avro.schema.NamedSchema):
        return avro_shortname(v.name)
    if isinstance(v, avro.schema.ArraySchema):
        return f"array of <{friendly(v.items)}>"
    elif isinstance(v, avro.schema.PrimitiveSchema):
        return v.type
    elif isinstance(v, avro.schema.UnionSchema):
        return " or ".join([friendly(s) for s in v.schemas])
    else:
        return avro_shortname(v)


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
    vocab=None,  # type: Optional[Mapping[str, str]]
):
    # type: (...) -> bool
    """Determine if a python datum is an instance of a schema."""

    debug = _logger.isEnabledFor(logging.DEBUG)
    if not identifiers:
        identifiers = []

    if not foreign_properties:
        foreign_properties = set()

    if vocab is None:
        raise Exception("vocab must be provided")

    schema_type = expected_schema.type

    if schema_type == "null":
        if datum is None:
            return True
        if raise_ex:
            raise ValidationException("the value is not null")
        return False
    elif schema_type == "boolean":
        if isinstance(datum, bool):
            return True
        if raise_ex:
            raise ValidationException("the value is not boolean")
        return False
    elif schema_type == "string":
        if isinstance(datum, str):
            return True
        if isinstance(datum, bytes):
            return True
        if raise_ex:
            raise ValidationException("the value is not string")
        return False
    elif schema_type == "int":
        if isinstance(datum, int) and INT_MIN_VALUE <= datum <= INT_MAX_VALUE:
            return True
        if raise_ex:
            raise ValidationException(f"`{vpformat(datum)}` is not int")
        return False
    elif schema_type == "long":
        if (isinstance(datum, int)) and LONG_MIN_VALUE <= datum <= LONG_MAX_VALUE:
            return True
        if raise_ex:
            raise ValidationException(f"the value `{vpformat(datum)}` is not long")
        return False
    elif schema_type in ["float", "double"]:
        if isinstance(datum, int) or isinstance(datum, float):
            return True
        if raise_ex:
            raise ValidationException(
                f"the value `{vpformat(datum)}` is not float or double"
            )
        return False
    elif isinstance(expected_schema, avro.schema.EnumSchema):
        if expected_schema.name in ("org.w3id.cwl.salad.Any", "Any"):
            if datum is not None:
                return True
            if raise_ex:
                raise ValidationException("'Any' type must be non-null")
            return False
        if not isinstance(datum, str):
            if raise_ex:
                raise ValidationException(
                    f"value is a {type(datum).__name__} but expected a string"
                )
            return False
        if expected_schema.name == "org.w3id.cwl.cwl.Expression":
            if "$(" in datum or "${" in datum:
                return True
            if raise_ex:
                raise ValidationException(
                    "value `{}` does not contain an expression in the form $() or ${{}}".format(
                        datum
                    )
                )
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
                        vocab=vocab,
                    ):
                        return False
                except ValidationException as v:
                    if raise_ex:
                        source = v if debug else None
                        raise ValidationException(
                            "item is invalid because", sl, [v]
                        ) from source
                    return False
            return True
        else:
            if raise_ex:
                raise ValidationException(
                    "the value {} is not a list, expected list of {}".format(
                        vpformat(datum), friendly(expected_schema.items)
                    )
                )
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
                vocab=vocab,
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
                    vocab=vocab,
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
                    ValidationException(f"tried {friendly(check)} but", None, [err])
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
                        raise ValidationException(f"Missing '{f.name}' field")
                    else:
                        return False
                avroname = None
                if d in vocab:
                    avroname = avro_type_name(vocab[d])
                if expected_schema.name != d and expected_schema.name != avroname:
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
                    vocab=vocab,
                ):
                    return False
            except ValidationException as v:
                if f.name not in datum:
                    errors.append(
                        ValidationException(f"missing required field `{f.name}`")
                    )
                else:
                    errors.append(
                        ValidationException(
                            f"the `{f.name}` field is not valid because",
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
                                    f"'{fn.name}'" for fn in expected_schema.fields
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
        raise ValidationException(f"Unrecognized schema_type {schema_type}")
    else:
        return False
