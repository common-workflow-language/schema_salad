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

def safename(name: str) -> str:
    return re.sub("[^a-zA-Z0-9]", "_", name)

class NamespaceDefinition:
    def __init__(self, name):
        self.name = name;
        self.classDefinitions = {}

    def write(self, target, ind):
        name = safename(self.name)
        target.write(f"namespace {name} {{\n")
        for key in self.classDefinitions:
            self.classDefinitions[key].write(target, ind, ind)
        target.write(f"}}\n")


class ClassDefinition:
    def __init__(self, name):
        self.name    = name
        self.extends = []
        self.fields  = []
        self.abstract = False

    def write(self, target, fullInd, ind):
        name = safename(self.name)
        target.write(f"{ind}struct {name}")
        extends = list(map(safename, self.extends))
        override = ""
        virtual = "virtual "
        if len(self.extends) > 0:
            target.write(f"\n{fullInd}{ind}: ")
            target.write(f"\n{fullInd}{ind}, ".join(extends))
            override = "override "
            virtual  = ""
        target.write(f" {{\n")

        for field in self.fields:
            field.write(target, fullInd + ind, ind)

        target.write(f"\n")
        if self.abstract:
            target.write(f"{fullInd}{ind}virtual ~{name}() = 0;\n")
        target.write(f"{fullInd}{ind}{virtual}auto toYaml() const -> YAML::Node {override}{{\n")
        target.write(f"{fullInd}{ind}{ind}using ::toYaml;\n")
        target.write(f"{fullInd}{ind}{ind}auto n = YAML::Node{{}};\n")
        for e in extends:
            target.write(f"{fullInd}{ind}{ind}n = mergeYaml(n, {e}::toYaml());\n")

        for field in self.fields:
            fieldname = safename(field.name)
            target.write(f"{fullInd}{ind}{ind}n[\"{field.name}\"] = toYaml({fieldname});\n")
        target.write(f"{fullInd}{ind}{ind}return n;\n{fullInd}{ind}}}\n")

        target.write(f"{fullInd}}};\n")
        if self.abstract:
            target.write(f"{fullInd}inline {name}::~{name}() = default;\n")

        target.write("\n")

class FieldDefinition:
    def __init__(self, name, typeStr):
        self.name = name
        self.typeStr = typeStr
    def write(self, target, fullInd, ind):
        name    = safename(self.name)
        target.write(f"{fullInd}{self.typeStr} {name};\n")

class EnumDefinition:
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def write(self, target, ind):
        name = safename(self.name)
        target.write(f"enum class {name} : unsigned int {{\n{ind}");
        target.write(f",\n{ind}".join(self.values))
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
            target.write(f"{ind}{ind}{{\"{v}\", {name}::{v}}},\n")
        target.write(f"{ind}}};\n{ind}out = m.find(v)->second;\n}}\n")


        target.write(f"inline auto toYaml({name} v) {{\n")
        target.write(f"{ind}return YAML::Node{{std::string{{to_string(v)}}}};\n}}\n")

        target.write(f"inline auto fromYaml(YAML::Node n, {name}& out) {{\n")
        target.write(f"{ind}to_enum(n.as<std::string>(), out);\n}}\n")

def getType(s: str) -> str:
    return s.split('#')[1]

def split_name(s: str) -> (str, str):
    t = s.split('#')
    assert(len(t) == 2)
    return (t[0], t[1])
def split_field(s: str) -> (str, str, str):
    (namespace, field) = split_name(s)
    t = field.split("/")
    assert(len(t) == 2)
    return (namespace, t[0], t[1])

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

        self.namespaces = {}
        self.enumDefinitions = []
        self.currentClass = None

    def convertTypeToCpp(self, type_declaration: Union[List[Any], Dict[str, Any], str]) -> str:
        if not isinstance(type_declaration, list):
            return self.convertTypeToCpp([type_declaration])

        if len(type_declaration) == 1:
            if type_declaration[0] == "null":
                return "std::monostate"
            elif type_declaration[0] == "string":
                return "std::string"
            elif isinstance(type_declaration[0], dict):
                if "type" in type_declaration[0] and type_declaration[0]["type"] == "enum":
                    self.enumDefinitions.append(EnumDefinition(
                        type_declaration[0]["name"],
                        list(map(shortname, type_declaration[0]["symbols"]))
                    ))
                    return safename(self.enumDefinitions[-1].name)
                elif "type" in type_declaration[0] and type_declaration[0]["type"] == "array":
                    ts = []
                    for i in type_declaration[0]["items"]:
                        if isinstance(i, str):
                            n = i.split("#")[1]
                            ts.append(i)
                        else:
                            n = i["name"].split("#")[1]
                            ts.append(n)
                    name = ", ".join(ts)
                    return f"std::vector<std::variant<{name}>>";

                return "dict"
            return type_declaration[0]

        type_declaration = list(map(self.convertTypeToCpp, type_declaration))

        # make sure that monostate is the first entry
        if "std::monostate" in type_declaration:
            type_declaration.remove("std::monostate")
            type_declaration.insert(0, "std::monostate")

        type_declaration = ", ".join(type_declaration)
        return f"std::variant<{type_declaration}>"


    def prologue(self) -> None:
        pass

    def begin_class(
        self,
        classname: str,
        extends: MutableSequence[str],
        doc: str,
        abstract: bool,
        field_names: MutableSequence[str],
        idfield: str,
        optional_fields: Set[str],
    ) -> None:
        assert(self.currentClass == None)
        namespace = classname.split('#')[0]
        classname = classname.split('#')[1]
        cd = ClassDefinition(
            classname
        )
        cd.abstract = abstract
        extends = list(map(getType, extends))
        cd.extends  = extends

        self.currentClass = classname

        if not namespace in self.namespaces:
            self.namespaces[namespace] = NamespaceDefinition(namespace)

        self.namespaces[namespace].classDefinitions[classname] = cd

    def end_class(self, classname: str, field_names: List[str]) -> None:
        assert(self.currentClass != None)
        self.currentClass = None

        pass

    def type_loader(
        self, type_declaration: Union[List[Any], Dict[str, Any], str]
    ) -> TypeDef:
        return self.convertTypeToCpp(type_declaration)

    def type_loader_enum(self, type_declaration: Dict[str, Any]) -> TypeDef:
        pass

    def declare_field(
        self,
        name: str,
        fieldtype: TypeDef,
        doc: Optional[str],
        optional: bool,
    ) -> None:
        namespace = name.split('#')[0]
        classname = name.split('#')[1].split('/')[0]
        fieldname = name.split('#')[1].split('/')[1]

        if self.currentClass != classname:
            return

        namespaceOfType = fieldtype.split('#')[0]
        if namespaceOfType == namespace:
            fieldtype = fieldtype[len(namespaceOfType)+1:]

        self.namespaces[namespace].classDefinitions[classname].fields.append(
            FieldDefinition(fieldname, fieldtype)
        )

    def epilogue(self, root_loader: TypeDef) -> None:
        self.epilogue2()

    def epilogue2(self) -> None:
        self.target.write("#pragma once\n\n")
        self.target.write("#include <cassert>\n")
        self.target.write("#include <map>\n")
        self.target.write("#include <string>\n")
        self.target.write("#include <string_view>\n")
        self.target.write("#include <variant>\n")
        self.target.write("#include <vector>\n")
        self.target.write("#include <yaml-cpp/yaml.h>\n\n")
        self.target.write("""
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
""")
        for e in self.enumDefinitions:
            e.write(self.target, "    ");
        for key in self.namespaces:
            self.namespaces[key].write(self.target, "    ")

    def run(self, items) -> None:
        items2 = deepcopy_strip(items)
        types = {i["name"]: i for i in items2}  # type: Dict[str, Any]
        results = []

        for stype in items2:
            assert("type" in stype)
            if stype["type"] == "record":
                (namespace, classname) = split_name(stype["name"])
                cd = ClassDefinition(
                    classname
                )
                cd.abstract = stype.get("abstract", False)
                if "extends" in stype:
                    for ex in aslist(stype["extends"]):
                        (base_namespace, base_classname) = split_name(ex)
                        name = base_classname
                        if base_namespace != namespace:
                            name = f"{base_namespace}::{name}"
                        cd.extends.append(name)

#
                if not namespace in self.namespaces:
                    self.namespaces[namespace] = NamespaceDefinition(namespace)

                self.namespaces[namespace].classDefinitions[classname] = cd

                if "fields" in stype:
                    for field in stype["fields"]:
                        print(f"{field}")
                        (namespace, classname, fieldname) = split_field(field["name"])
                        if isinstance(field["type"], dict):
                            if (field["type"]["type"] == "enum":
                                fieldtype = field["type"]["type"]
                        else:
                            fieldtype = field["type"]

                        self.namespaces[namespace].classDefinitions[classname].fields.append(
                            FieldDefinition(fieldname, fieldtype)
                        )



            print(stype)
            print(stype["type"])
            if "extends" in stype:
                print("blub?")
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
                        if specs:
                            basetype["fields"] = replace_type(
                                basetype.get("fields", []), specs, loader, set()
                            )

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
                            raise ValidationException(
                                "Field name {} appears twice in {}".format(
                                    field["name"], stype["name"]
                                )
                            )
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
        self.epilogue2()

