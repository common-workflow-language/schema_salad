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


class Schema(object):
    """Base class for all Schema classes."""

    def __init__(self, atype, other_props=None):
        # type: (str, Optional[Dict[str, Any]]) -> None
        # Ensure valid ctor args
        if not isinstance(atype, str):
            raise SchemaParseException(
                "Schema type '{}' must be a string, was '{}.".format(atype, type(atype))
            )
        elif atype not in VALID_TYPES:
            fail_msg = "%s is not a valid type." % atype
            raise SchemaParseException(fail_msg)

        # add members
        if not hasattr(self, "_props"):
            self._props = {}  # type: Dict[str, Any]
        self.set_prop("type", atype)
        self.type = atype
        self._props.update(other_props or {})

    # Read-only properties dict. Printing schemas
    # creates JSON properties directly from this dict.
    props = property(lambda self: self._props)

    # utility functions to manipulate properties dict
    def get_prop(self, key):  # type: (str) -> Any
        return self._props.get(key)

    def set_prop(self, key, value):  # type: (str, Any) -> None
        self._props[key] = value


class Name(object):
    """Class to describe Avro name."""

    def __init__(self, name_attr, space_attr, default_space):
        # type: (str, Optional[str], Optional[str]) -> None
        """
        Formulate full name according to the specification.

        @arg name_attr: name value read in schema or None.
        @arg space_attr: namespace value read in schema or None.
        @ard default_space: the current default space or None.
        """
        # Ensure valid ctor args
        if not (isinstance(name_attr, str) or (name_attr is None)):
            fail_msg = "Name must be non-empty string or None."
            raise SchemaParseException(fail_msg)
        elif name_attr == "":
            fail_msg = "Name must be non-empty string or None."
            raise SchemaParseException(fail_msg)

        if not (isinstance(space_attr, str) or (space_attr is None)):
            fail_msg = "Space must be non-empty string or None."
            raise SchemaParseException(fail_msg)
        elif name_attr == "":
            fail_msg = "Space must be non-empty string or None."
            raise SchemaParseException(fail_msg)

        if not (isinstance(default_space, str) or (default_space is None)):
            fail_msg = "Default space must be non-empty string or None."
            raise SchemaParseException(fail_msg)
        elif name_attr == "":
            fail_msg = "Default must be non-empty string or None."
            raise SchemaParseException(fail_msg)

        self._full = None  # type: Optional[str]

        if name_attr is None or name_attr == "":
            return

        if name_attr.find(".") < 0:
            if (space_attr is not None) and (space_attr != ""):
                self._full = "%s.%s" % (space_attr, name_attr)
            else:
                if (default_space is not None) and (default_space != ""):
                    self._full = "%s.%s" % (default_space, name_attr)
                else:
                    self._full = name_attr
        else:
            self._full = name_attr

    fullname = property(lambda self: self._full)

    def get_space(self):
        # type: () -> Optional[str]
        """Back out a namespace from full name."""
        if self._full is None:
            return None

        if self._full.find(".") > 0:
            return self._full.rsplit(".", 1)[0]
        else:
            return ""


class Names(object):
    """Track name set and default namespace during parsing."""

    def __init__(self, default_namespace=None):
        # type: (Optional[str]) -> None
        self.names = {}  # type: Dict[str, NamedSchema]
        self.default_namespace = default_namespace

    def has_name(self, name_attr, space_attr):
        # type: (str, Optional[str]) -> bool
        test = Name(name_attr, space_attr, self.default_namespace).fullname
        return test in self.names

    def get_name(self, name_attr, space_attr):
        # type: (str, Optional[str]) -> Optional[NamedSchema]
        test = Name(name_attr, space_attr, self.default_namespace).fullname
        if test not in self.names:
            return None
        return self.names[test]

    def add_name(self, name_attr, space_attr, new_schema):
        # type: (str, Optional[str], NamedSchema) -> Name
        """
        Add a new schema object to the name set.

          @arg name_attr: name value read in schema
          @arg space_attr: namespace value read in schema.

          @return: the Name that was just added.
        """
        to_add = Name(name_attr, space_attr, self.default_namespace)

        if to_add.fullname in VALID_TYPES:
            fail_msg = "%s is a reserved type name." % to_add.fullname
            raise SchemaParseException(fail_msg)
        elif to_add.fullname in self.names:
            fail_msg = 'The name "%s" is already in use.' % to_add.fullname
            raise SchemaParseException(fail_msg)

        self.names[to_add.fullname] = new_schema
        return to_add


class NamedSchema(Schema):
    """Named Schemas specified in NAMED_TYPES."""

    def __init__(
        self,
        atype,  # type: str
        name,  # type: str
        namespace=None,  # type: Optional[str]
        names=None,  # type: Optional[Names]
        other_props=None,  # type: Optional[Dict[str, str]]
    ):  # type: (...) -> None
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
    name = property(lambda self: self.get_prop("name"))


class Field(object):
    def __init__(
        self,
        atype,  # type: Union[str, Dict[str, str]]
        name,  # type: str
        has_default,  # type: bool
        default=None,  # type: Optional[str]
        order=None,  # type: Optional[str]
        names=None,  # type: Optional[Names]
        doc=None,  # type: Optional[str]
        other_props=None,  # type: Optional[Dict[str, str]]
    ):  # type: (...) -> None
        # Ensure valid ctor args
        if not name:
            fail_msg = "Fields must have a non-empty name."
            raise SchemaParseException(fail_msg)
        elif not isinstance(name, str):
            fail_msg = "The name property must be a string."
            raise SchemaParseException(fail_msg)
        elif order is not None and order not in VALID_FIELD_SORT_ORDERS:
            fail_msg = "The order property %s is not valid." % order
            raise SchemaParseException(fail_msg)

        # add members
        self._props = {}  # type: Dict[str, Union[Schema, str, None]]
        self._has_default = has_default
        self._props.update(other_props or {})

        if isinstance(atype, str) and names is not None and names.has_name(atype, None):
            type_schema = cast(NamedSchema, names.get_name(atype, None))  # type: Schema
        else:
            try:
                type_schema = make_avsc_object(cast(Dict[str, str], atype), names)
            except Exception as e:
                raise SchemaParseException(
                    'Type property "%s" not a valid Avro schema: %s' % (atype, e)
                )
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
    default = property(lambda self: self.get_prop("default"))

    # utility functions to manipulate properties dict
    def get_prop(self, key):  # type: (str) -> Union[Schema, str, None]
        return self._props.get(key)

    def set_prop(self, key, value):
        # type: (str, Union[Schema, str, None]) -> None
        self._props[key] = value


#
# Primitive Types
#
class PrimitiveSchema(Schema):
    """Valid primitive types are in PRIMITIVE_TYPES."""

    def __init__(self, atype, other_props=None):
        # type: (str, Optional[Dict[str, str]]) -> None
        # Ensure valid ctor args
        if atype not in PRIMITIVE_TYPES:
            raise AvroException("%s is not a valid primitive type." % atype)

        # Call parent ctor
        Schema.__init__(self, atype, other_props=other_props)

        self.fullname = atype


#
# Complex Types (non-recursive)
#


class EnumSchema(NamedSchema):
    def __init__(
        self,
        name,  # type: str
        namespace,  # type: str
        symbols,  # type: List[str]
        names=None,  # type: Optional[Names]
        doc=None,  # type: Optional[str]
        other_props=None,  # type: Optional[Dict[str, str]]
    ):  # type: (...) -> None
        # Ensure valid ctor args
        if not isinstance(symbols, list):
            fail_msg = "Enum Schema requires a JSON array for the symbols property."
            raise AvroException(fail_msg)
        elif False in [isinstance(s, str) for s in symbols]:
            fail_msg = "Enum Schema requires all symbols to be JSON strings."
            raise AvroException(fail_msg)
        elif len(set(symbols)) < len(symbols):
            fail_msg = "Duplicate symbol: %s" % symbols
            raise AvroException(fail_msg)

        # Call parent ctor
        NamedSchema.__init__(self, "enum", name, namespace, names, other_props)

        # Add class members
        self.set_prop("symbols", symbols)
        if doc is not None:
            self.set_prop("doc", doc)

    # read-only properties
    symbols = property(lambda self: self.get_prop("symbols"))


#
# Complex Types (recursive)
#


class ArraySchema(Schema):
    def __init__(self, items, names=None, other_props=None):
        # type: (List[Any], Optional[Names], Optional[Dict[str, str]]) -> None
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
                    "Items schema (%s) not a valid Avro schema: %s (known "
                    "names: %s)" % (items, err, list(names.names.keys()))
                )

        self.set_prop("items", items_schema)

    # read-only properties
    items = property(lambda self: self.get_prop("items"))


class UnionSchema(Schema):
    """
    names is a dictionary of schema objects
    """

    def __init__(self, schemas, names=None):
        # type: (List[Schema], Optional[Names]) -> None
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
                    new_schema = make_avsc_object(schema, names)  # type: ignore
                except Exception as err:
                    raise SchemaParseException(
                        "Union item must be a valid Avro schema: %s" % str(err)
                    )
            # check the new schema
            if (
                new_schema.type in VALID_TYPES
                and new_schema.type not in NAMED_TYPES
                and new_schema.type in [schema.type for schema in schema_objects]
            ):
                raise SchemaParseException("%s type already in Union" % new_schema.type)
            elif new_schema.type == "union":
                raise SchemaParseException("Unions cannot contain other unions.")
            else:
                schema_objects.append(new_schema)
        self._schemas = schema_objects

    # read-only properties
    schemas = property(lambda self: self._schemas)


class RecordSchema(NamedSchema):
    @staticmethod
    def make_field_objects(field_data, names):
        # type: (List[Dict[str, str]], Names) -> List[Field]
        """We're going to need to make message parameters too."""
        field_objects = []
        field_names = []  # type: List[str]
        for field in field_data:
            if hasattr(field, "get") and callable(field.get):
                atype = cast(str, field.get("type"))
                name = cast(str, field.get("name"))

                # null values can have a default value of None
                has_default = False
                default = None
                if "default" in field:
                    has_default = True
                    default = field.get("default")

                order = field.get("order")
                doc = field.get("doc")
                other_props = get_other_props(field, FIELD_RESERVED_PROPS)
                new_field = Field(
                    atype, name, has_default, default, order, names, doc, other_props
                )
                # make sure field name has not been used yet
                if new_field.name in field_names:
                    fail_msg = "Field name %s already in use." % new_field.name
                    raise SchemaParseException(fail_msg)
                field_names.append(new_field.name)
            else:
                raise SchemaParseException("Not a valid field: %s" % field)
            field_objects.append(new_field)
        return field_objects

    def __init__(
        self,
        name,  # type: str
        namespace,  # type: str
        fields,  # type: List[Dict[str, str]]
        names=None,  # type: Optional[Names]
        schema_type="record",  # type: str
        doc=None,  # type: Optional[str]
        other_props=None,  # type: Optional[Dict[str, str]]
    ):  # type: (...) -> None
        # Ensure valid ctor args
        if fields is None:
            fail_msg = "Record schema requires a non-empty fields property."
            raise SchemaParseException(fail_msg)
        elif not isinstance(fields, list):
            fail_msg = "Fields property must be a list of Avro schemas."
            raise SchemaParseException(fail_msg)
        if names is None:
            raise SchemaParseException("Must provide Names.")

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
    fields = property(lambda self: self.get_prop("fields"))


#
# Module Methods
#
def get_other_props(all_props, reserved_props):
    # type: (Dict[str, str], Tuple[str, ...]) -> Optional[Dict[str, str]]
    """
    Retrieve the non-reserved properties from a dictionary of properties
    @args reserved_props: The set of reserved properties to exclude
    """
    if hasattr(all_props, "items") and callable(all_props.items):
        return dict(
            [(k, v) for (k, v) in list(all_props.items()) if k not in reserved_props]
        )
    return None


def make_avsc_object(json_data, names=None):
    # type: (Union[Dict[str, str], List[Any], str], Optional[Names]) -> Schema
    """
    Build Avro Schema from data parsed out of JSON string.

    @arg names: A Name object (tracks seen names and default space)
    """
    if names is None:
        names = Names()
    assert isinstance(names, Names)

    if isinstance(json_data, Dict) and json_data.get("name") == "Any":
        del names.names["Any"]
    elif not names.has_name("Any", ""):
        EnumSchema("Any", "", ["Any"], names=names)

    # JSON object (non-union)
    if hasattr(json_data, "get") and callable(json_data.get):  # type: ignore
        assert isinstance(json_data, Dict)
        atype = cast(str, json_data.get("type"))
        other_props = get_other_props(json_data, SCHEMA_RESERVED_PROPS)
        if atype in PRIMITIVE_TYPES:
            return PrimitiveSchema(atype, other_props)
        if atype in NAMED_TYPES:
            name = cast(str, json_data.get("name"))
            namespace = cast(str, json_data.get("namespace", names.default_namespace))
            if atype == "enum":
                symbols = cast(List[str], json_data.get("symbols"))
                doc = json_data.get("doc")
                return EnumSchema(name, namespace, symbols, names, doc, other_props)
            if atype in ["record", "error"]:
                fields = cast(List[Dict[str, str]], json_data.get("fields"))
                doc = json_data.get("doc")
                return RecordSchema(
                    name, namespace, fields, names, atype, doc, other_props
                )
            raise SchemaParseException("Unknown Named Type: %s" % atype)
        if atype in VALID_TYPES:
            if atype == "array":
                items = cast(List[str], json_data.get("items"))
                return ArraySchema(items, names, other_props)
        if atype is None:
            raise SchemaParseException('No "type" property: %s' % json_data)
        raise SchemaParseException("Undefined type: %s" % atype)
    # JSON array (union)
    if isinstance(json_data, list):
        return UnionSchema(json_data, names)
    # JSON string (primitive)
    if json_data in PRIMITIVE_TYPES:
        return PrimitiveSchema(cast(str, json_data))
    # not for us!
    fail_msg = "Could not make an Avro Schema object from %s." % json_data
    raise SchemaParseException(fail_msg)
