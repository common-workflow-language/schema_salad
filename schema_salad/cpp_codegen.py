"""C++17 code generator for a given schema salad definition."""
import copy
import os
import re
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

import pkg_resources

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

from . import _logger, jsonld_context, ref_resolver, schema, validate
from .codegen_base import CodeGenBase, TypeDef
from .exceptions import SchemaException
from .schema import deepcopy_strip, replace_type, shortname
from .utils import aslist


# replace reserved keywords in C++
def replaceKeywords(s: str) -> str:
    if s in ("class", "enum", "int", "long", "float", "double", "default"):
        s = s + "_"
    return s


# create a safe name
def safename(name: str) -> str:
    classname = re.sub("[^a-zA-Z0-9]", "_", name)
    return replaceKeywords(classname)


# create a safe name (todo: this should be somehow not really exists)
def safename2(name: str) -> str:
    return safename(name["namespace"]) + "::" + safename(name["classname"])


# Splits names like https://xyz.xyz/blub#cwl/class
# into its class path and non class path
def split_name(s: str) -> (str, str):
    t = s.split("#")
    assert len(t) == 2
    return (t[0], t[1])


# similar to split_name but for field names
def split_field(s: str) -> (str, str, str):
    (namespace, field) = split_name(s)
    t = field.split("/")
    assert len(t) == 2
    return (namespace, t[0], t[1])


# Prototype of a class
class ClassDefinition:
    def __init__(self, name):
        self.fullName = name
        self.extends = []
        self.fields = []
        self.abstract = False
        (self.namespace, self.classname) = split_name(name)
        self.namespace = safename(self.namespace)
        self.classname = safename(self.classname)

    def writeFwdDeclaration(self, target, fullInd, ind):
        target.write(
            f"{fullInd}namespace {self.namespace} {{ struct {self.classname}; }}\n"
        )

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
            virtual = ""
        target.write(" {\n")

        for field in self.fields:
            field.writeDefinition(target, fullInd + ind, ind, self.namespace)

        if self.abstract:
            target.write(f"{fullInd}{ind}virtual ~{self.classname}() = 0;\n")
        target.write(
            f"{fullInd}{ind}{virtual}auto toYaml() const -> YAML::Node{override};\n"
        )
        target.write(f"{fullInd}}};\n")
        target.write(f"{fullInd}}}\n\n")

    def writeImplDefinition(self, target, fullInd, ind):
        extends = list(map(safename2, self.extends))

        if self.abstract:
            target.write(
                f"{fullInd}inline {self.namespace}::{self.classname}::~{self.classname}() = default;\n"
            )

        target.write(
            f"""{fullInd}inline auto {self.namespace}::{self.classname}::toYaml() const -> YAML::Node {{
{fullInd}{ind}using ::toYaml;
{fullInd}{ind}auto n = YAML::Node{{}};
"""
        )
        for e in extends:
            target.write(f"{fullInd}{ind}n = mergeYaml(n, {e}::toYaml());\n")

        for field in self.fields:
            fieldname = safename(field.name)
            target.write(
                f'{fullInd}{ind}addYamlField(n, "{field.name}", toYaml(*{fieldname}));\n'
            )
            # target.write(f"{fullInd}{ind}addYamlIfNotEmpty(n, \"{field.name}\", toYaml(*{fieldname}));\n")

        target.write(f"{fullInd}{ind}return n;\n{fullInd}}}\n")


# Prototype of a single field of a class
class FieldDefinition:
    def __init__(self, name, typeStr, optional):
        self.name = name
        self.typeStr = typeStr
        self.optional = optional

    def writeDefinition(self, target, fullInd, ind, namespace):
        name = safename(self.name)
        # target.write(f"{fullInd}std::unique_ptr<{self.typeStr}> {name} = std::make_unique<{self.typeStr}>();\n")
        typeStr = self.typeStr.replace(namespace + "::", "")
        target.write(f"{fullInd}heap_object<{typeStr}> {name};\n")


# Prototype of an enum definition
class EnumDefinition:
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def writeDefinition(self, target, ind):
        namespace = ""
        if len(self.name.split("#")) == 2:
            (namespace, classname) = split_name(self.name)
            namespace = safename(namespace)
            classname = safename(classname)
            name = namespace + "::" + classname
        else:
            name = safename(self.name)
            classname = name
        if len(namespace) > 0:
            target.write(f"namespace {namespace} {{\n")
        target.write(f"enum class {classname} : unsigned int {{\n{ind}")
        target.write(f",\n{ind}".join(map(safename, self.values)))
        target.write("\n};\n")
        target.write(f"inline auto to_string({classname} v) {{\n")
        target.write(f"{ind}static auto m = std::vector<std::string_view> {{\n")
        target.write(f'{ind}    "')
        target.write(f'",\n{ind}    "'.join(self.values))
        target.write(f'"\n{ind}}};\n')

        target.write(f"{ind}using U = std::underlying_type_t<{name}>;\n")
        target.write(f"{ind}return m.at(static_cast<U>(v));\n}}\n")

        if len(namespace) > 0:
            target.write("}\n")

        target.write(f"inline void to_enum(std::string_view v, {name}& out) {{\n")
        target.write(
            f"{ind}static auto m = std::map<std::string, {name}, std::less<>> {{\n"
        )
        for v in self.values:
            target.write(f'{ind}{ind}{{"{v}", {name}::{safename(v)}}},\n')
        target.write(f"{ind}}};\n{ind}out = m.find(v)->second;\n}}\n")

        target.write(f"inline auto toYaml({name} v) {{\n")
        target.write(f"{ind}return YAML::Node{{std::string{{to_string(v)}}}};\n}}\n")

        target.write(f"inline auto yamlToEnum(YAML::Node n, {name}& out) {{\n")
        target.write(f"{ind}to_enum(n.as<std::string>(), out);\n}}\n")


# !TODO way tot many functions, most of these shouldn't exists
def isPrimitiveType(v):
    if not isinstance(v, str):
        return False
    return v in ["null", "boolean", "int", "long", "float", "double", "string"]


def hasFieldValue(e, f, v):
    if not isinstance(e, dict):
        return False
    if f not in e:
        return False
    return e[f] == v


def isRecordSchema(v):
    return hasFieldValue(v, "type", "record")


def isEnumSchema(v):
    if not hasFieldValue(v, "type", "enum"):
        return False
    if "symbols" not in v:
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
    if "items" not in v:
        return False
    if not isinstance(v["items"], list):
        return False

    def pred(i):
        return (
            isPrimitiveType(i)
            or isRecordSchema(i)
            or isEnumSchema(i)
            or isArraySchema(i)
            or isinstance(i, str)
        )

    for i in items:
        if not (pred(i) or isArray(i, pred)):
            return False
    return True


# The genererator class that is being called in codegen.py
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
        self.target = target
        self.examples = examples
        self.package = package
        self.copyright = copyright

        self.classDefinitions = {}
        self.enumDefinitions = {}

    def convertTypeToCpp(
        self, type_declaration: Union[List[Any], Dict[str, Any], str]
    ) -> str:
        if not isinstance(type_declaration, list):
            return self.convertTypeToCpp([type_declaration])

        if len(type_declaration) == 1:
            if type_declaration[0] in ("null", "https://w3id.org/cwl/salad#null"):
                return "std::monostate"
            elif type_declaration[0] in (
                "string",
                "http://www.w3.org/2001/XMLSchema#string",
            ):
                return "std::string"
            elif type_declaration[0] in ("int", "http://www.w3.org/2001/XMLSchema#int"):
                return "int32_t"
            elif type_declaration[0] in (
                "long",
                "http://www.w3.org/2001/XMLSchema#long",
            ):
                return "int64_t"
            elif type_declaration[0] in (
                "float",
                "http://www.w3.org/2001/XMLSchema#float",
            ):
                return "float"
            elif type_declaration[0] in (
                "double",
                "http://www.w3.org/2001/XMLSchema#double",
            ):
                return "double"
            elif type_declaration[0] in (
                "boolean",
                "http://www.w3.org/2001/XMLSchema#boolean",
            ):
                return "bool"
            elif type_declaration[0] == "https://w3id.org/cwl/salad#Any":
                return "std::any"
            elif type_declaration[0] in (
                "PrimitiveType",
                "https://w3id.org/cwl/salad#PrimitiveType",
            ):
                return (
                    "std::variant<bool, int32_t, int64_t, float, double, std::string>"
                )
            elif isinstance(type_declaration[0], dict):
                if "type" in type_declaration[0] and type_declaration[0]["type"] in (
                    "enum",
                    "https://w3id.org/cwl/salad#enum",
                ):
                    name = type_declaration[0]["name"]
                    if name not in self.enumDefinitions:
                        self.enumDefinitions[name] = EnumDefinition(
                            type_declaration[0]["name"],
                            list(map(shortname, type_declaration[0]["symbols"])),
                        )
                    if len(name.split("#")) != 2:
                        return safename(name)
                    (namespace, classname) = name.split("#")
                    return safename(namespace) + "::" + safename(classname)
                elif "type" in type_declaration[0] and type_declaration[0]["type"] in (
                    "array",
                    "https://w3id.org/cwl/salad#array",
                ):
                    items = type_declaration[0]["items"]
                    if isinstance(items, list):
                        ts = []
                        for i in items:
                            ts.append(self.convertTypeToCpp(i))
                        name = ", ".join(ts)
                        return f"std::vector<std::variant<{name}>>"
                    else:
                        i = self.convertTypeToCpp(items)
                        return f"std::vector<{i}>"
                elif "type" in type_declaration[0] and type_declaration[0]["type"] in (
                    "record",
                    "https://w3id.org/cwl/salad#record",
                ):
                    n = type_declaration[0]["name"]
                    (namespace, classname) = split_name(n)
                    return safename(namespace) + "::" + safename(classname)

                n = type_declaration[0]["type"]
                (namespace, classname) = split_name(n)
                return safename(namespace) + "::" + safename(classname)

            if len(type_declaration[0].split("#")) != 2:
                print(f"// something weird2 about {type_declaration[0]}")
                return type_declaration[0]

            (namespace, classname) = split_name(type_declaration[0])
            return safename(namespace) + "::" + safename(classname)

        type_declaration = list(map(self.convertTypeToCpp, type_declaration))
        type_declaration = ", ".join(type_declaration)
        return f"std::variant<{type_declaration}>"

    # start of our generated file
    def epilogue(self) -> None:
        self.target.write(
            """#pragma once

// Generated by schema-salad code generator

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <variant>
#include <vector>
#include <yaml-cpp/yaml.h>
#include <any>

inline auto mergeYaml(YAML::Node n1, YAML::Node n2) {
    for (auto const& e : n1) {
        n2[e.first.as<std::string>()] = e.second;
    }
    return n2;
}

// declaring toYaml
inline auto toYaml(bool v) {
    return YAML::Node{v};
}
inline auto toYaml(float v) {
    return YAML::Node{v};
}
inline auto toYaml(double v) {
    return YAML::Node{v};
}
inline auto toYaml(int32_t v) {
    return YAML::Node{v};
}
inline auto toYaml(int64_t v) {
    return YAML::Node{v};
}
inline auto toYaml(std::any const&) {
    return YAML::Node{};
}
inline auto toYaml(std::monostate const&) {
    return YAML::Node(YAML::NodeType::Undefined);
}

inline auto toYaml(std::string const& v) {
    return YAML::Node{v};
}

inline void addYamlField(YAML::Node node, std::string const& key, YAML::Node value) {
    if (value.IsDefined()) {
        node[key] = value;
    }
}

// fwd declaring toYaml
template <typename T>
auto toYaml(std::vector<T> const& v) -> YAML::Node;
template <typename T>
auto toYaml(T const& t) -> YAML::Node;
template <typename ...Args>
auto toYaml(std::variant<Args...> const& t) -> YAML::Node;

template <typename T>
class heap_object {
    std::unique_ptr<T> data = std::make_unique<T>();
public:
    heap_object() = default;
    heap_object(heap_object const& oth) {
        *data = *oth;
    }
    heap_object(heap_object&& oth) {
        *data = *oth;
    }

    template <typename T2>
    heap_object(T2 const& oth) {
        *data = oth;
    }
    template <typename T2>
    heap_object(T2&& oth) {
        *data = oth;
    }

    auto operator=(heap_object const& oth) -> heap_object& {
        *data = *oth;
        return *this;
    }
    auto operator=(heap_object&& oth) -> heap_object& {
        *data = std::move(*oth);
        return *this;
    }

    template <typename T2>
    auto operator=(T2 const& oth) -> heap_object& {
        *data = oth;
        return *this;
    }
    template <typename T2>
    auto operator=(T2&& oth) -> heap_object& {
        *data = std::move(oth);
        return *this;
    }

    auto operator->() -> T* {
        return data.get();
    }
    auto operator->() const -> T const* {
        return data.get();
    }
    auto operator*() -> T& {
        return *data;
    }
    auto operator*() const -> T const& {
        return *data;
    }

};

"""
        )
        # main body, printing fwd declaration, class definitions, and then implementations

        for key in self.classDefinitions:
            self.classDefinitions[key].writeFwdDeclaration(self.target, "", "    ")

        for key in self.enumDefinitions:
            self.enumDefinitions[key].writeDefinition(self.target, "    ")
        for key in self.classDefinitions:
            self.classDefinitions[key].writeDefinition(self.target, "", "    ")
        for key in self.classDefinitions:
            self.classDefinitions[key].writeImplDefinition(self.target, "", "    ")

        self.target.write(
            """
template <typename T>
auto toYaml(std::vector<T> const& v) -> YAML::Node {
    auto n = YAML::Node(YAML::NodeType::Sequence);
    for (auto const& e : v) {
        n.push_back(toYaml(e));
    }
    return n;
}

template <typename T>
auto toYaml(T const& t) -> YAML::Node {
    if constexpr (std::is_enum_v<T>) {
        return toYaml(t);
    } else {
        return t.toYaml();
    }
}

template <typename ...Args>
auto toYaml(std::variant<Args...> const& t) -> YAML::Node {
    return std::visit([](auto const& e) {
        return toYaml(e);
    }, t);
}
"""
        )

    def parseRecordField(self, field):
        (namespace, classname, fieldname) = split_field(field["name"])
        if isinstance(field["type"], dict):
            if field["type"]["type"] == "enum":
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

        if "extends" in stype:
            for ex in aslist(stype["extends"]):
                (base_namespace, base_classname) = split_name(ex)
                ext = {"namespace": base_namespace, "classname": base_classname}
                cd.extends.append(ext)

        #
        if "fields" in stype:
            for field in stype["fields"]:
                cd.fields.append(self.parseRecordField(field))

        self.classDefinitions[stype["name"]] = cd

    def parseEnum(self, stype):
        name = stype["name"]
        if name not in self.enumDefinitions:
            self.enumDefinitions[name] = EnumDefinition(
                name, list(map(shortname, stype["symbols"]))
            )
        return name

    def parse(self, items) -> None:
        types = {i["name"]: i for i in items}  # type: Dict[str, Any]

        for stype in items:
            assert "type" in stype

            if "type" in stype and stype["type"] == "documentation":
                continue

            def pred(i):
                return (
                    isPrimitiveType(i)
                    or isRecordSchema(i)
                    or isEnumSchema(i)
                    or isArraySchema(i)
                    or isinstance(i, str)
                )

            if not (pred(stype) or isArray(stype, pred)):
                raise SchemaException("not a valid SaladRecordField")

            # parsing a record
            if isRecordSchema(stype):
                self.parseRecordSchema(stype)
            elif isEnumSchema(stype):
                self.parseEnum(stype)
            else:
                print(f"not parsed{stype}")

        self.epilogue()


# If you use this generator on CommonWorkflowLanguage.yml
# you can use the generated as done in the following code snippet
#
#
##include "generated_code.h"
##include <iostream>
#
# using namespace https___w3id_org_cwl_cwl;
#
# int main() {
#    auto tool = CommandLineTool{};
#    *tool.cwlVersion = CWLVersion::v1_2;
#    *tool.id         = "Some id";
#    *tool.label      = "some label";
#    *tool.doc        = "documentation that is brief";
#
#
#    {
#        auto input = CommandInputParameter{};
#        *input.id = "first";
#        auto record = CommandInputRecordSchema{};
#
#        auto fieldEntry = CommandInputRecordField{};
#        *fieldEntry.name = "species";
#
#        auto species = CommandInputEnumSchema{};
#        species.symbols->push_back("homo_sapiens");
#        species.symbols->push_back("mus_musculus");
#
#        using ListType = std::vector<std::variant<CWLType, CommandInputRecordSchema, CommandInputEnumSchema, CommandInputArraySchema, std::string>>;
#        *fieldEntry.type = ListType{species, "null"};
#
#        using ListType2 = std::vector<CommandInputRecordField>;
#        *record.fields = ListType2{fieldEntry};
#
#        using ListType3 = std::vector<std::variant<CWLType, CommandInputRecordSchema, CommandInputEnumSchema, CommandInputArraySchema, std::string>>;
#        *input.type = ListType3{record};
#
#        tool.inputs->push_back(input);
#    }
#
#
#    auto y = toYaml(tool);
#
#    YAML::Emitter out;
#    out << y;
#    std::cout << out.c_str() << "\n";
# }
