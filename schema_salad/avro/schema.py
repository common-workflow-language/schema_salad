# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Modifications copyright (C) 2017-2018 Common Workflow Language.
"""
Contains the Schema classes.

A schema may be one of:
  A record, mapping field names to field value data;
  An enum, containing one of a small set of symbols;
  An array of values, all of the same schema;
  A union of other schemas;
  A unicode string;
  A 32-bit signed int;
  A 64-bit signed long;
  A 32-bit floating-point float;
  A 64-bit floating-point double;
  A boolean; or
  Null.
"""
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from schema_salad.exceptions import SchemaException

#
# Constants
#

PRIMITIVE_TYPES = ("null", "boolean", "string", "int", "long", "float", "double")

NAMED_TYPES = ("enum", "record")

VALID_TYPES = PRIMITIVE_TYPES + NAMED_TYPES + ("array", "union")

SCHEMA_RESERVED_PROPS = (
    "type",
    "name",
    "namespace",
    "fields",  # Record
    "items",  # Array
    "symbols",  # Enum
    "doc",
)

# need recursion support in mypy/mypyc for a comprehensive JSON type
# MappingDataType = Dict[str, Union[PropType, List[PropsType]]]
# was: Union[str, MappingDataType, List[MappingDataType]]
JsonDataType = Any
AtomicPropType = Union[None, str, int, float, bool, "Schema", List[str], List["Field"]]
PropType = Union[
    AtomicPropType,
    Dict[str, AtomicPropType],
    List[Dict[str, AtomicPropType]],
]
PropsType = Dict[str, PropType]

FIELD_RESERVED_PROPS = ("default", "name", "doc", "order", "type")

VALID_FIELD_SORT_ORDERS = ("ascending", "descending", "ignore")

#
# Exceptions
#


class AvroException(SchemaException):
    pass


class SchemaParseException(AvroException):
    pass


#
# Base Classes
#


class Schema:
    """Base class for all Schema classes."""

    def __init__(self, atype: str, other_props: Optional[PropsType] = None) -> None:
        # Ensure valid ctor args
        if not isinstance(atype, str):
            raise SchemaParseException(
                f"Schema type '{atype}' must be a string, was '{type(atype)}."
            )
        elif atype not in VALID_TYPES:
            fail_msg = f"{atype} is not a valid type."
            raise SchemaParseException(fail_msg)

        # add members
        if not hasattr(self, "_props"):
            self._props = {}  # type: PropsType
        self.set_prop("type", atype)
        self.type = atype
        self._props.update(other_props or {})

    # Read-only properties dict. Printing schemas
    # creates JSON properties directly from this dict.
    @property
    def props(self) -> PropsType:
        return self._props

    # utility functions to manipulate properties dict
    def get_prop(self, key: str) -> Optional[PropType]:
        return self._props.get(key)

    def set_prop(self, key: str, value: Optional[PropType]) -> None:
        self._props[key] = value


class Name:
    """Class to describe Avro name."""

    def __init__(
        self,
        name_attr: Optional[str] = None,
        space_attr: Optional[str] = None,
        default_space: Optional[str] = None,
    ) -> None:
        """
        Formulate full name according to the specification.

        @arg name_attr: name value read in schema or None.
        @arg space_attr: namespace value read in schema or None.
        @ard default_space: the current default space or None.
        """
        # Ensure valid ctor args

        def validate(val: Optional[str], name: str) -> None:
            if (isinstance(val, str) and val != "") or val is None:
                # OK
                return
            fail_msg = f"{name} must be non-empty string or None."
            raise SchemaParseException(fail_msg)

        validate(name_attr, "Name")
        validate(space_attr, "Space")
        validate(default_space, "Default space")

        self._full = name_attr  # type: Optional[str]

        if name_attr is None or name_attr == "":
            return

        if name_attr.find(".") < 0:
            if (space_attr is not None) and (space_attr != ""):
                self._full = f"{space_attr}.{name_attr}"
            else:
                if (default_space is not None) and (default_space != ""):
                    self._full = f"{default_space}.{name_attr}"

    @property
    def fullname(self) -> Optional[str]:
        return self._full

    def get_space(self) -> Optional[str]:
        """Back out a namespace from full name."""
        if self._full is None:
            return None

        if self._full.find(".") > 0:
            return self._full.rsplit(".", 1)[0]
        else:
            return None


class Names:
    """Track name set and default namespace during parsing."""

    def __init__(self, default_namespace: Optional[str] = None) -> None:
        self.names = {}  # type: Dict[str, NamedSchema]
        self.default_namespace = default_namespace

    def has_name(self, name_attr: str, space_attr: Optional[str]) -> bool:
        test = Name(name_attr, space_attr, self.default_namespace).fullname
        return test in self.names

    def get_name(
        self, name_attr: str, space_attr: Optional[str]
    ) -> Optional["NamedSchema"]:
        test = Name(name_attr, space_attr, self.default_namespace).fullname
        if test not in self.names:
            return None
        return self.names[test]

    def add_name(
        self, name_attr: str, space_attr: Optional[str], new_schema: "NamedSchema"
    ) -> Name:
        """
        Add a new schema object to the name set.

          @arg name_attr: name value read in schema
          @arg space_attr: namespace value read in schema.

          @return: the Name that was just added.
        """
        to_add = Name(name_attr, space_attr, self.default_namespace)

        if to_add.fullname in VALID_TYPES:
            fail_msg = f"{to_add.fullname} is a reserved type name."
            raise SchemaParseException(fail_msg)
        elif to_add.fullname in self.names:
            fail_msg = f'The name "{to_add.fullname}" is already in use.'
            raise SchemaParseException(fail_msg)
        elif to_add.fullname is None:
            fail_msg = f"{to_add.fullname} is missing, but this is impossible."
            raise SchemaParseException(fail_msg)

        self.names[to_add.fullname] = new_schema
        return to_add


class NamedSchema(Schema):
    """Named Schemas specified in NAMED_TYPES."""

    def __init__(
        self,
        atype: str,
        name: str,
        namespace: Optional[str] = None,
        names: Optional[Names] = None,
        other_props: Optional[PropsType] = None,
    ) -> None:
        # Ensure valid ctor args
        if not name:
            fail_msg = "Named Schemas must have a non-empty name."
            raise SchemaParseException(fail_msg)
        elif not isinstance(name, str):
            fail_msg = "The name property must be a string."
            raise SchemaParseException(fail_msg)
        elif namespace is not None and not isinstance(namespace, str):
            fail_msg = "The namespace property must be a string."
            raise SchemaParseException(fail_msg)
        if names is None:
            raise SchemaParseException("Must provide Names.")

        # Call parent ctor
        Schema.__init__(self, atype, other_props)

        # Add class members
        new_name = names.add_name(name, namespace, self)

        # Store name and namespace as they were read in origin schema
        self.set_prop("name", name)
        if namespace is not None:
            self.set_prop("namespace", new_name.get_space())

        # Store full name as calculated from name, namespace
        self._fullname = new_name.fullname

    # read-only properties
    @property
    def name(self) -> str:
        return cast(str, self.get_prop("name"))


class Field:
    def __init__(
        self,
        atype: JsonDataType,
        name: str,
        has_default: bool,
        default: Optional[Any] = None,
        order: Optional[str] = None,
        names: Optional[Names] = None,
        doc: Optional[Union[str, List[str]]] = None,
        other_props: Optional[PropsType] = None,
    ) -> None:
        # Ensure valid ctor args
        if not name:
            fail_msg = "Fields must have a non-empty name."
            raise SchemaParseException(fail_msg)
        elif not isinstance(name, str):
            fail_msg = "The name property must be a string."
            raise SchemaParseException(fail_msg)
        elif order is not None and order not in VALID_FIELD_SORT_ORDERS:
            fail_msg = f"The order property {order} is not valid."
            raise SchemaParseException(fail_msg)

        # add members
        self._props = {}  # type: PropsType
        self._has_default = has_default
        self._props.update(other_props or {})

        if isinstance(atype, str) and names is not None and names.has_name(atype, None):
            type_schema = cast(NamedSchema, names.get_name(atype, None))  # type: Schema
        else:
            try:
                type_schema = make_avsc_object(atype, names)
            except Exception as e:
                raise SchemaParseException(
                    f'Type property "{atype}" not a valid Avro schema.'
                ) from e
        self.set_prop("type", type_schema)
        self.set_prop("name", name)
        self.type = type_schema
        self.name = name
        # TODO(hammer): check to ensure default is valid
        if has_default:
            self.set_prop("default", default)
        if order is not None:
            self.set_prop("order", order)
        if doc is not None:
            self.set_prop("doc", doc)

    # read-only properties
    @property
    def default(self) -> Optional[Any]:
        return self.get_prop("default")

    # utility functions to manipulate properties dict
    def get_prop(self, key: str) -> Optional[PropType]:
        return self._props.get(key)

    def set_prop(self, key: str, value: Optional[PropType]) -> None:
        self._props[key] = value


#
# Primitive Types
#
class PrimitiveSchema(Schema):
    """Valid primitive types are in PRIMITIVE_TYPES."""

    def __init__(self, atype: str, other_props: Optional[PropsType] = None) -> None:
        # Ensure valid ctor args
        if atype not in PRIMITIVE_TYPES:
            raise AvroException(f"{atype} is not a valid primitive type.")

        # Call parent ctor
        Schema.__init__(self, atype, other_props=other_props)

        self.fullname = atype


#
# Complex Types (non-recursive)
#


class EnumSchema(NamedSchema):
    def __init__(
        self,
        name: str,
        namespace: Optional[str],
        symbols: List[str],
        names: Optional[Names] = None,
        doc: Optional[Union[str, List[str]]] = None,
        other_props: Optional[PropsType] = None,
    ) -> None:
        # Ensure valid ctor args
        if not isinstance(symbols, list):
            fail_msg = "Enum Schema requires a JSON array for the symbols property."
            raise AvroException(fail_msg)
        elif False in [isinstance(s, str) for s in symbols]:
            fail_msg = "Enum Schema requires all symbols to be JSON strings."
            raise AvroException(fail_msg)
        elif len(set(symbols)) < len(symbols):
            fail_msg = f"Duplicate symbol: {symbols}"
            raise AvroException(fail_msg)

        # Call parent ctor
        NamedSchema.__init__(self, "enum", name, namespace, names, other_props)

        # Add class members
        self.set_prop("symbols", symbols)
        if doc is not None:
            self.set_prop("doc", doc)

    # read-only properties
    @property
    def symbols(self) -> List[str]:
        return cast(List[str], self.get_prop("symbols"))


#
# Complex Types (recursive)
#


class ArraySchema(Schema):
    def __init__(
        self, items: JsonDataType, names: Names, other_props: Optional[PropsType] = None
    ) -> None:
        # Call parent ctor
        Schema.__init__(self, "array", other_props)
        # Add class members

        if names is None:
            raise SchemaParseException("Must provide Names.")
        if isinstance(items, str) and names.has_name(items, None):
            items_schema = cast(Schema, names.get_name(items, None))
        else:
            try:
                items_schema = make_avsc_object(items, names)
            except Exception as err:
                raise SchemaParseException(
                    f"Items schema ({items}) not a valid Avro schema: (known "
                    f"names: {list(names.names.keys())})."
                ) from err

        self.set_prop("items", items_schema)

    # read-only properties
    @property
    def items(self) -> Schema:
        return cast(Schema, self.get_prop("items"))


class UnionSchema(Schema):
    """
    names is a dictionary of schema objects
    """

    def __init__(
        self,
        schemas: List[JsonDataType],
        names: Names,
    ) -> None:
        # Ensure valid ctor args
        if names is None:
            raise SchemaParseException("Must provide Names.")
        if not isinstance(schemas, list):
            fail_msg = "Union schema requires a list of schemas."
            raise SchemaParseException(fail_msg)

        # Call parent ctor
        Schema.__init__(self, "union")

        # Add class members
        schema_objects = []  # type: List[Schema]
        for schema in schemas:
            if isinstance(schema, str) and names.has_name(schema, None):
                new_schema = cast(Schema, names.get_name(schema, None))
            else:
                try:
                    new_schema = make_avsc_object(schema, names)
                except Exception as err:
                    raise SchemaParseException(
                        f"Union item must be a valid Avro schema: {schema}"
                    ) from err
            # check the new schema
            if (
                new_schema.type in VALID_TYPES
                and new_schema.type not in NAMED_TYPES
                and new_schema.type in [schema.type for schema in schema_objects]
            ):
                raise SchemaParseException(f"{new_schema.type} type already in Union")
            elif new_schema.type == "union":
                raise SchemaParseException("Unions cannot contain other unions.")
            else:
                schema_objects.append(new_schema)
        self._schemas = schema_objects

    # read-only properties
    @property
    def schemas(self) -> List[Schema]:
        return self._schemas


class RecordSchema(NamedSchema):
    @staticmethod
    def make_field_objects(field_data: List[PropsType], names: Names) -> List[Field]:
        """We're going to need to make message parameters too."""
        field_objects = []  # type: List[Field]
        field_names = []  # type: List[str]
        for field in field_data:
            if hasattr(field, "get") and callable(field.get):
                atype = field.get("type")
                name = cast(str, field.get("name"))

                # null values can have a default value of None
                has_default = False
                default = None
                if "default" in field:
                    has_default = True
                    default = field.get("default")
                order = field.get("order")
                if not (order is None or isinstance(order, str)):
                    raise SchemaParseException('"order" must be a string or None')
                doc = field.get("doc")
                if not (doc is None or isinstance(doc, str) or isinstance(doc, list)):
                    raise SchemaParseException(
                        '"doc" must be a string, list of strings, or None'
                    )
                else:
                    doc = cast(Union[str, List[str], None], doc)
                other_props = get_other_props(field, FIELD_RESERVED_PROPS)
                new_field = Field(
                    atype, name, has_default, default, order, names, doc, other_props
                )
                # make sure field name has not been used yet
                if new_field.name in field_names:
                    fail_msg = f"Field name {new_field.name} already in use."
                    raise SchemaParseException(fail_msg)
                field_names.append(new_field.name)
            else:
                raise SchemaParseException(f"Not a valid field: {field}")
            field_objects.append(new_field)
        return field_objects

    def __init__(
        self,
        name: str,
        namespace: Optional[str],
        fields: List[PropsType],
        names: Names,
        schema_type: str = "record",
        doc: Optional[Union[str, List[str]]] = None,
        other_props: Optional[PropsType] = None,
    ) -> None:
        # Ensure valid ctor args
        if fields is None:
            fail_msg = "Record schema requires a non-empty fields property."
            raise SchemaParseException(fail_msg)
        elif not isinstance(fields, list):
            fail_msg = "Fields property must be a list of Avro schemas."
            raise SchemaParseException(fail_msg)

        # Call parent ctor (adds own name to namespace, too)
        NamedSchema.__init__(self, schema_type, name, namespace, names, other_props)

        if schema_type == "record":
            old_default = names.default_namespace
            names.default_namespace = Name(
                name, namespace, names.default_namespace
            ).get_space()

        # Add class members
        field_objects = RecordSchema.make_field_objects(fields, names)
        self.set_prop("fields", field_objects)
        if doc is not None:
            self.set_prop("doc", doc)

        if schema_type == "record":
            names.default_namespace = old_default

    # read-only properties
    @property
    def fields(self) -> List[Field]:
        return cast(List[Field], self.get_prop("fields"))


#
# Module Methods
#
def get_other_props(
    all_props: PropsType, reserved_props: Tuple[str, ...]
) -> Optional[PropsType]:
    """
    Retrieve the non-reserved properties from a dictionary of properties
    @args reserved_props: The set of reserved properties to exclude
    """
    if hasattr(all_props, "items") and callable(all_props.items):
        return {k: v for (k, v) in all_props.items() if k not in reserved_props}
    return None


def make_avsc_object(json_data: JsonDataType, names: Optional[Names] = None) -> Schema:
    """
    Build Avro Schema from data parsed out of JSON string.

    @arg names: A Name object (tracks seen names and default space)
    """
    if names is None:
        names = Names()

    if (
        isinstance(json_data, Dict)
        and json_data.get("name") == "org.w3id.cwl.salad.Any"
    ):
        del names.names["org.w3id.cwl.salad.Any"]
    elif not names.has_name("org.w3id.cwl.salad.Any", None):
        EnumSchema("org.w3id.cwl.salad.Any", None, ["Any"], names=names)

    # JSON object (non-union)
    if isinstance(json_data, dict):
        atype = json_data.get("type")
        other_props = get_other_props(json_data, SCHEMA_RESERVED_PROPS)
        if atype in PRIMITIVE_TYPES:
            primative_type = cast(str, atype)
            return PrimitiveSchema(primative_type, other_props)
        if atype in NAMED_TYPES:
            name = json_data.get("name")
            namespace = json_data.get("namespace", names.default_namespace)
            doc = json_data.get("doc")
            if not isinstance(name, str):
                raise SchemaParseException(
                    f'"name" for type {atype} must be a string: {json_data}'
                )
            if not (namespace is None or isinstance(namespace, str)):
                raise SchemaParseException(
                    '"namespace" for type {} must be a string or None: {}'.format(
                        atype, json_data
                    )
                )
            if not (doc is None or isinstance(doc, str) or isinstance(doc, list)):
                raise SchemaParseException(
                    '"doc" for type {} must be a string, a list of strings, or None: {}'.format(
                        atype, json_data
                    )
                )
            if atype == "enum":
                symbols = json_data.get("symbols")
                if not isinstance(symbols, list):
                    raise SchemaParseException(
                        '"symbols" for type enum must be a list of strings: {}'.format(
                            json_data
                        )
                    )
                else:
                    symbols = cast(List[str], symbols)
                return EnumSchema(name, namespace, symbols, names, doc, other_props)
            if atype in ["record", "error"]:
                fields = json_data.get("fields")
                if not isinstance(fields, list):
                    raise SchemaParseException(
                        '"fields" for type {} must be a list of mappings: {}'.format(
                            atype, json_data
                        )
                    )
                else:
                    fields = cast(List[PropsType], fields)
                return RecordSchema(
                    name, namespace, fields, names, atype, doc, other_props
                )
            raise SchemaParseException(f"Unknown Named Type: {atype}")
        if atype in VALID_TYPES:
            if atype == "array":
                items = json_data.get("items")
                return ArraySchema(items, names, other_props)
        if atype is None:
            raise SchemaParseException(f'No "type" property: {json_data}')
        raise SchemaParseException(f"Undefined type: {atype}")
    # JSON array (union)
    if isinstance(json_data, list):
        return UnionSchema(json_data, names)
    # JSON string (primitive)
    if json_data in PRIMITIVE_TYPES:
        return PrimitiveSchema(json_data)
    # not for us!
    fail_msg = f"Could not make an Avro Schema object from {json_data}."
    raise SchemaParseException(fail_msg)
