"""C++17 code generator for a given schema salad definition."""
import os
import shutil
import string
from io import StringIO
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Union,
)
from schema_salad.utils import (
    CacheType,
    ResolveType,
    add_dictlist,
    aslist,
    convert_to_dict,
    flatten,
    json_dumps,
    yaml_no_ts,
)
from . import _logger, jsonld_context, ref_resolver, validate

import pkg_resources
import re
from .utils import aslist
import copy

from . import _logger, schema
from .codegen_base import CodeGenBase, TypeDef
from .exceptions import SchemaException
from .schema import shortname, deepcopy_strip, replace_type

class Object:
    pass

def replaceKeywords(s: str) -> str:
    if s in ("class", "enum"):
        s = s + "_"
    return s

def safename(name: str) -> str:
    classname = re.sub("[^a-zA-Z0-9]", "_", name)
    return replaceKeywords(classname)


def safename2(name: str) -> str:
    return safename(name.namespace) + "::" + safename(name.classname)

class ClassDefinition:
    def __init__(self, name):
        self.fullName    = name
        self.extends = []
        self.fields  = []
        self.abstract = False
        (self.namespace, self.classname) = split_name(name)
        self.namespace = safename(self.namespace)
        self.classname = safename(self.classname)


    def writeFwdDeclaration(self, target, fullInd, ind):
        target.write(f"{fullInd}namespace {self.namespace} {{ struct {self.classname}; }}\n")

    def writeDefinition(self, target, fullInd, ind):
        target.write(f"{fullInd}namespace {self.namespace} {{\n")
        target.write(f"{fullInd}struct {self.classname}")
        extends = list(map(safename2, self.extends))
        override = ""
        virtual = "virtual "
        if len(self.extends) > 0:
            target.write(f"\n{fullInd}{ind}: ")
            target.write(f"\n{fullInd}{ind}, ".join(extends))
            override = " override"
            virtual  = ""
        target.write(f" {{\n")

        for field in self.fields:
            field.writeDefinition(target, fullInd + ind, ind)


        if self.abstract:
            target.write(f"{fullInd}{ind}virtual ~{self.classname}() = 0;\n")
        target.write(f"{fullInd}{ind}{virtual}auto toYaml() const -> YAML::Node{override};\n")
        target.write(f"{fullInd}}};\n")
        target.write(f"{fullInd}}}\n\n")

    def writeImplDefinition(self, target, fullInd, ind):
        extends = list(map(safename2, self.extends))

        if self.abstract:
            target.write(f"{fullInd}inline {self.namespace}::{self.classname}::~{self.classname}() = default;\n")

        target.write(f"""{fullInd}inline auto {self.namespace}::{self.classname}::toYaml() const -> YAML::Node {{
{fullInd}{ind}using ::toYaml;
{fullInd}{ind}auto n = YAML::Node{{}};
""")
        for e in extends:
            target.write(f"{fullInd}{ind}n = mergeYaml(n, {e}::toYaml());\n")

        for field in self.fields:
            fieldname = safename(field.name)
            target.write(f"{fullInd}{ind}n[\"{field.name}\"] = toYaml(*{fieldname});\n")
        target.write(f"{fullInd}{ind}return n;\n{fullInd}}}\n")

class FieldDefinition:
    def __init__(self, name, typeStr, optional):
        self.name = name
        self.typeStr = typeStr
        self.optional = optional

    def writeDefinition(self, target, fullInd, ind):
        name    = safename(self.name)
        target.write(f"{fullInd}std::unique_ptr<{self.typeStr}> {name};\n")


class EnumDefinition:
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def writeDefinition(self, target, ind):
        name = safename(self.name)
        target.write(f"enum class {name} : unsigned int {{\n{ind}");
        target.write(f",\n{ind}".join(map(safename, self.values)))
        target.write(f"\n}};\n");
        target.write(f"inline auto to_string({name} v) {{\n")
        target.write(f"{ind}static auto m = std::vector<std::string_view> {{\n")
        target.write(f"{ind}    \"")
        target.write(f"\",\n{ind}    \"".join(self.values))
        target.write(f"\"\n{ind}}};\n")
        target.write(f"{ind}using U = std::underlying_type_t<{name}>;\n")
        target.write(f"{ind}return m.at(static_cast<U>(v));\n}}\n")

        target.write(f"inline void to_enum(std::string_view v, {name}& out) {{\n")
        target.write(f"{ind}static auto m = std::map<std::string, {name}, std::less<>> {{\n")
        for v in self.values:
            target.write(f"{ind}{ind}{{\"{v}\", {name}::{safename(v)}}},\n")
        target.write(f"{ind}}};\n{ind}out = m.find(v)->second;\n}}\n")


        target.write(f"inline auto toYaml({name} v) {{\n")
        target.write(f"{ind}return YAML::Node{{std::string{{to_string(v)}}}};\n}}\n")

        target.write(f"inline auto fromYaml(YAML::Node n, {name}& out) {{\n")
        target.write(f"{ind}to_enum(n.as<std::string>(), out);\n}}\n")

def split_name(s: str) -> (str, str):
    t = s.split('#')
    assert(len(t) == 2)
    return (t[0], t[1])

def split_field(s: str) -> (str, str, str):
    (namespace, field) = split_name(s)
    t = field.split("/")
    assert(len(t) == 2)
    return (namespace, t[0], t[1])

def isPrimitiveType(v):
    if not isinstance(v, str):
        return False
    return v in ["null", "boolean", "int", "long", "float", "double", "string"];

def hasFieldValue(e, f, v):
    if not isinstance(e, dict):
        return False
    if not f in e:
        return False
    return e[f] == v;

def isRecordSchema(v):
    return hasFieldValue(v, "type", "record")

def isEnumSchema(v):
    if not hasFieldValue(v, "type", "enum"):
        return False
    if not "symbols" in v:
        return False
    if not isinstance(v["symbols"], list):
        return False
    return True

def isArray(v, pred):
    if not isinstance(v, list):
        return False
    for i in v:
        if not pred(i):
            return False
    return True

def isArraySchema(v):
    if not hasFieldValue(v, "type", "array"):
        return False
    if not "items" in v:
        return False
    if not isinstance(v["items"], list):
        return False
    def pred(i):
         return (isPrimitiveType(i) or
                isRecordSchema(i) or
                isEnumSchema(i) or
                isArraySchema(i) or
                isinstance(i, str))

    for i in items:
        if not (pred(i) or isArray(i, pred)):
            return False
    return True

class CppCodeGen(CodeGenBase):
    def __init__(
        self,
        base: str,
        target: Optional[str],
        examples: Optional[str],
        package: str,
        copyright: Optional[str],
    ) -> None:
        super().__init__()
        self.base_uri = base
        self.target   = target
        self.examples = examples
        self.package = package
        self.copyright = copyright

        self.classDefinitions = {}
        self.enumDefinitions  = {}

    def convertTypeToCpp(self, type_declaration: Union[List[Any], Dict[str, Any], str]) -> str:
        if not isinstance(type_declaration, list):
            return self.convertTypeToCpp([type_declaration])

        if len(type_declaration) == 1:
            if type_declaration[0] in ("null", "https://w3id.org/cwl/salad#null"):
                return "std::monostate"
            elif type_declaration[0] in ("string","http://www.w3.org/2001/XMLSchema#string"):
                return "std::string"
            elif type_declaration[0] in ("int", "http://www.w3.org/2001/XMLSchema#int"):
                return "int32_t"
            elif type_declaration[0] in ("long", "http://www.w3.org/2001/XMLSchema#long"):
                return "int64_t"
            elif type_declaration[0] in ("float", "http://www.w3.org/2001/XMLSchema#float"):
                return "float"
            elif type_declaration[0] in ("double", "http://www.w3.org/2001/XMLSchema#double"):
                return "double"
            elif type_declaration[0] in ("boolean", "http://www.w3.org/2001/XMLSchema#boolean"):
                return "bool"
            elif type_declaration[0] == "https://w3id.org/cwl/salad#Any":
                return "unknown"
            elif type_declaration[0] in ("PrimitiveType", "https://w3id.org/cwl/salad#PrimitiveType"):
                return "std::variant<bool, int32_t, int64_t, float, double, std::string>"
            elif isinstance(type_declaration[0], dict):
                if "type" in type_declaration[0] and type_declaration[0]["type"] in ("enum", "https://w3id.org/cwl/salad#enum"):
                    name = type_declaration[0]["name"]
                    print(f"// {type_declaration[0]}")
                    if not name in self.enumDefinitions:
                        self.enumDefinitions[name] = EnumDefinition(
                            type_declaration[0]["name"],
                            list(map(shortname, type_declaration[0]["symbols"]))
                        )
                    return safename(name)
                elif "type" in type_declaration[0] and type_declaration[0]["type"] in ("array", "https://w3id.org/cwl/salad#array"):
                    items = type_declaration[0]["items"]
                    if isinstance(items, list):
                        ts = []
                        for i in items:
                            ts.append(self.convertTypeToCpp(i))
                        name = ", ".join(ts)
                        return f"std::vector<std::variant<{name}>>";
                    else:
                        i=self.convertTypeToCpp(items)
                        return f"std::vector<{i}>"
                elif "type" in type_declaration[0] and type_declaration[0]["type"] == "record":
                    n = type_declaration[0]["name"]
                    (namespace, classname) = split_name(n)
                    return safename(namespace) + "::" + safename(classname)

                n = type_declaration[0]["type"]
                (namespace, classname) = split_name(n)
                return safename(namespace) + "::" + safename(classname)

            if len(type_declaration[0].split('#')) != 2:
                print(f"// something weird2 about {type_declaration[0]}")
                return type_declaration[0]

            (namespace, classname) = split_name(type_declaration[0])
            return safename(namespace) + "::" + safename(classname)

        type_declaration = list(map(self.convertTypeToCpp, type_declaration))

        # make sure that monostate is the first entry
        if "std::monostate" in type_declaration:
            type_declaration.remove("std::monostate")
            if len(type_declaration) == 0:
                raise "must have at least one non 'null' field type"

        type_declaration = ", ".join(type_declaration)
        return f"std::variant<{type_declaration}>"


    def epilogue(self) -> None:
        self.target.write("""#pragma once

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <variant>
#include <vector>
#include <yaml-cpp/yaml.h>

inline auto mergeYaml(YAML::Node n1, YAML::Node n2) {
    for (auto const& key : n1) {
        n2[key.as<std::string>()] = n1[key.as<std::string>()];
    }
    return n2;
}
inline auto toYaml(std::string const& v) {
    return YAML::Node{v};
}
inline auto toYaml(float v) {
    return YAML::Node{v};
}
inline auto toYaml(int v) {
    return YAML::Node{v};
}
template <typename T>
auto toYaml(std::vector<T> v) {
    auto n = YAML::Node{};
    for (auto const& e : v) {
        n.push_back(toYAML(e));
    }
    return n;
}

template <typename T>
auto toYaml(T const& t) {
    return t.toYaml();
}

template <typename ...Args>
auto toYaml(std::variant<Args...> const& t) {
    return std::visit([](auto const& e) {
        return toYaml(e);
    }, t);
}

using Enum = std::string;
""")
        for key in self.classDefinitions:
            self.classDefinitions[key].writeFwdDeclaration(self.target, "", "    ")

        for key in self.enumDefinitions:
            self.enumDefinitions[key].writeDefinition(self.target, "    ");
        for key in self.classDefinitions:
            self.classDefinitions[key].writeDefinition(self.target, "", "    ")
        for key in self.classDefinitions:
            self.classDefinitions[key].writeImplDefinition(self.target, "", "    ")


    def parseRecordField(self, field):
        (namespace, classname, fieldname) = split_field(field["name"])
        if isinstance(field["type"], dict):
            if (field["type"]["type"] == "enum"):
                fieldtype = "Enum"
            else:
                fieldtype = self.convertTypeToCpp(field["type"])

        else:
            fieldtype = field["type"]
            fieldtype = self.convertTypeToCpp(fieldtype)


        return FieldDefinition(name=fieldname, typeStr=fieldtype, optional=False)

    def parseRecordSchema(self, stype):
        cd = ClassDefinition(name=stype["name"])
        cd.abstract = stype.get("abstract", False)
        print(f"//- type {stype['name']}")

        if "extends" in stype:
            for ex in aslist(stype["extends"]):
                (base_namespace, base_classname) = split_name(ex)
                ext = Object()
                ext.namespace = base_namespace
                ext.classname = base_classname
                cd.extends.append(ext)

#
        if "fields" in stype:
            for field in stype["fields"]:
                cd.fields.append(self.parseRecordField(field))

        self.classDefinitions[stype["name"]] = cd



    def parse(self, items) -> None:
        types = {i["name"]: i for i in items}  # type: Dict[str, Any]
        results = []

        for stype in items:
            assert("type" in stype)

            def pred(i):
                return (isPrimitiveType(i) or
                    isRecordSchema(i) or
                    isEnumSchema(i) or
                    isArraySchema(i) or
                    isinstance(i, str))


            if not (pred(stype) or isArray(stype, pred)):
                continue
#                raise "not a valid SaladRecordField"

            # parsing a record
            if isRecordSchema(stype):
                self.parseRecordSchema(stype)


            # parsing extends type
            if "extends" in stype:
                specs = {}  # type: Dict[str, str]
                if "specialize" in stype:
                    for spec in aslist(stype["specialize"]):
                        specs[spec["specializeFrom"]] = spec["specializeTo"]

                exfields = []  # type: List[str]
                exsym = []  # type: List[str]
                for ex in aslist(stype["extends"]):
                    if ex not in types:
                        raise ValidationException(
                            "Extends {} in {} refers to invalid base type.".format(
                                stype["extends"], stype["name"]
                            )
                        )

                    basetype = copy.copy(types[ex])

                    if stype["type"] == "record":
#                        if specs:
#                            basetype["fields"] = replace_type(
#                                basetype.get("fields", []), specs, loader, set()
#                            )

                        for field in basetype.get("fields", []):
                            if "inherited_from" not in field:
                                field["inherited_from"] = ex

                        exfields.extend(basetype.get("fields", []))
                    elif stype["type"] == "enum":
                        exsym.extend(basetype.get("symbols", []))

                if stype["type"] == "record":
                    stype = copy.copy(stype)
                    exfields.extend(stype.get("fields", []))
                    stype["fields"] = exfields

                    fieldnames = set()  # type: Set[str]
                    for field in stype["fields"]:
                        if field["name"] in fieldnames:
                            pass
                        else:
                            fieldnames.add(field["name"])
                elif stype["type"] == "enum":
                    stype = copy.copy(stype)
                    exsym.extend(stype.get("symbols", []))
                    stype["symbol"] = exsym

                types[stype["name"]] = stype

            results.append(stype)

        ex_types = {}
        for result in results:
            ex_types[result["name"]] = result

        extended_by = {}  # type: Dict[str, str]
        for result in results:
            if "extends" in result:
                for ex in aslist(result["extends"]):
                    if ex_types[ex].get("abstract"):
                        add_dictlist(extended_by, ex, ex_types[result["name"]])
                        add_dictlist(extended_by, validate.avro_type_name(ex), ex_types[ex])

        for result in results:
            if result.get("abstract") and result["name"] not in extended_by:
                raise ValidationException(
                    "{} is abstract but missing a concrete subtype".format(result["name"])
                )

        for result in results:
            if "fields" in result:
                pass
#                result["fields"] = replace_type(
#                    result["fields"], extended_by, loader, set()
#                )
        self.epilogue()

