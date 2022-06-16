"""DotNet code generator for a given schema salad definition."""
import os
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

from . import _logger, schema
from .codegen_base import CodeGenBase, TypeDef
from .exceptions import SchemaException
from .java_codegen import _ensure_directory_and_write, _safe_makedirs
from .schema import shortname


def doc_to_doc_string(doc: Optional[str], indent_level: int = 0) -> str:
    """Generate a documentation string from a schema salad doc field."""
    lead = "" + "    " * indent_level + "/// "
    if doc:
        doc_str = "\n".join([f"{lead}{line}" for line in doc.split("\n")])
    else:
        doc_str = ""
    return doc_str


_string_type_def = TypeDef(
    instance_type="string",
    init="new PrimitiveLoader<string>()",
    name="StringInstance",
    loader_type="ILoader<string>",
)

_int_type_def = TypeDef(
    instance_type="int",
    init="new PrimitiveLoader<int>()",
    name="IntegerInstance",
    loader_type="ILoader<int>",
)

_long_type_def = TypeDef(
    instance_type="long",
    name="LongInstance",
    loader_type="ILoader<long>",
    init="new PrimitiveLoader<long>()",
)

_float_type_def = TypeDef(
    instance_type="double",
    name="DoubleInstance",
    loader_type="ILoader<double>",
    init="new PrimitiveLoader<double>()",
)

_bool_type_def = TypeDef(
    instance_type="bool",
    name="BooleanInstance",
    loader_type="ILoader<bool>",
    init="new PrimitiveLoader<bool>()",
)

_null_type_def = TypeDef(
    instance_type="object",
    name="NullInstance",
    loader_type="ILoader<object>",
    init="new NullLoader()",
)

_any_type_def = TypeDef(
    instance_type="object",
    name="AnyInstance",
    init="new AnyLoader()",
    loader_type="ILoader<object>",
)

prims = {
    "http://www.w3.org/2001/XMLSchema#string": _string_type_def,
    "http://www.w3.org/2001/XMLSchema#int": _int_type_def,
    "http://www.w3.org/2001/XMLSchema#long": _long_type_def,
    "http://www.w3.org/2001/XMLSchema#float": _float_type_def,
    "http://www.w3.org/2001/XMLSchema#double": _float_type_def,
    "http://www.w3.org/2001/XMLSchema#boolean": _bool_type_def,
    "https://w3id.org/cwl/salad#null": _null_type_def,
    "https://w3id.org/cwl/salad#Any": _any_type_def,
    "string": _string_type_def,
    "int": _int_type_def,
    "long": _long_type_def,
    "float": _float_type_def,
    "double": _float_type_def,
    "boolean": _bool_type_def,
    "null": _null_type_def,
    "Any": _any_type_def,
}


class DotNetCodeGen(CodeGenBase):
    """Generation of TypeScript code for a given Schema Salad definition."""

    def __init__(
        self, base: str, examples: Optional[str], target: Optional[str], package: str
    ) -> None:
        """Initialize the TypeScript codegen."""
        super().__init__()
        self.target_dir = Path(target or ".").resolve()
        self.main_src_dir = self.target_dir / package / "src"
        self.test_src_dir = self.target_dir / "Test"
        self.test_resources_dir = self.test_src_dir / "data"
        self.package = package
        self.base_uri = base
        self.record_types: Set[str] = set()
        self.modules: Set[str] = set()
        self.id_field = ""
        self.examples = examples

    def prologue(self) -> None:
        """Trigger to generate the prolouge code."""
        for src_dir in [self.main_src_dir]:
            _safe_makedirs(src_dir)

        for primitive in prims.values():
            self.declare_type(primitive)

    @staticmethod
    def safe_name(name: str) -> str:
        """Generate a safe version of the given name."""
        avn = schema.avro_field_name(name)
        if avn.startswith("anon."):
            avn = avn[5:]
        if avn in (
            "class",
            "in",
            "extends",
            "abstract",
            "default",
            "package",
            "arguments",
            "out",
        ):
            # reserved words
            avn = avn + "_"

        return avn

    def begin_class(
        self,  # pylint: disable=too-many-arguments
        classname: str,
        extends: MutableSequence[str],
        doc: str,
        abstract: bool,
        field_names: MutableSequence[str],
        idfield: str,
        optional_fields: Set[str],
    ) -> None:
        """Produce the header for the given class."""
        self.current_interface = "I" + self.safe_name(classname)
        cls = self.safe_name(classname)
        self.current_class = cls
        self.current_class_is_abstract = abstract
        interface_module_name = self.current_interface
        self.current_interface_target_file = (
            self.main_src_dir / f"{interface_module_name}.cs"
        )
        class_module_name = self.current_class
        self.current_class_target_file = self.main_src_dir / f"{class_module_name}.cs"
        self.current_constructor_signature = StringIO()
        self.current_constructor_body = StringIO()
        self.current_loader = StringIO()
        self.current_serializer = StringIO()
        self.current_fieldtypes: Dict[str, TypeDef] = {}
        self.idfield = idfield

        doc_string = f"""
/// <summary>
/// Auto-generated interface for {classname}
"""
        if doc:
            doc_string += "///\n"
            doc_string += doc_to_doc_string(doc)
            doc_string += "\n"
        doc_string += "/// </summary>"

        self.record_types.add(f"{self.current_interface}")
        self.modules.add(interface_module_name)
        with open(self.current_interface_target_file, "w") as f:
            _logger.info("Writing file: %s", self.current_interface_target_file)
            if extends:
                ext = ": " + ",".join("I" + self.safe_name(e) for e in extends)
            else:
                ext = ""
            f.write(
                """using LanguageExt;

namespace {package};
{docstring}
public interface {cls} {ext} {{
""".format(
                    docstring=doc_string,
                    cls=f"{self.current_interface}",
                    ext=ext,
                    package=self.package,
                )
            )
        if self.current_class_is_abstract:
            return

        self.record_types.add(cls)
        self.modules.add(class_module_name)
        doc_string = f"""
/// <summary>
/// Auto-generated class implementation for {classname}
"""
        if doc:
            doc_string += "///\n"
            doc_string += doc_to_doc_string(doc)
            doc_string += "\n"
        doc_string += "/// </summary>"
        with open(self.current_class_target_file, "w") as f:
            _logger.info("Writing file: %s", self.current_class_target_file)
            f.write(
                """using System.Collections;
using LanguageExt;

namespace {package};
{docstring}
public class {cls} : {current_interface}, ISavable {{
    readonly LoadingOptions loadingOptions;

    readonly Dictionary<object, object> extensionFields;
""".format(
                    cls=cls,
                    current_interface=self.current_interface,
                    docstring=doc_string,
                    package=self.package,
                )
            )
        self.current_constructor_signature.write(
            "\n"
            + "\n"
            + "    public {cls} (".format(
                cls=cls,
            )
        )
        self.current_constructor_body.write(
            """
        this.loadingOptions = loadingOptions ?? new LoadingOptions();
        this.extensionFields = extensionFields ?? new Dictionary<object, object>();
"""
        )
        self.current_loader.write(
            """
    public static ISavable FromDoc(object doc__, string baseUri, LoadingOptions loadingOptions,
        string? docRoot = null)
    {
        List<ValidationException> errors = new();

        if (doc__ is not IDictionary)
        {
            throw new ValidationException("Document has to be of type Dictionary");
        }

        Dictionary<object, object> doc_ = ((IDictionary)doc__)
            .Cast<dynamic>()
            .ToDictionary(entry => entry.Key, entry => entry.Value);
            """
        )

        self.current_serializer.write(
            """
    public Dictionary<object, object> Save(bool top = false, string baseUrl = "",
        bool relativeUris = true)
    {
        Dictionary<object, object> r = new();
        foreach (KeyValuePair<object, object> ef in extensionFields)
        {
            r[loadingOptions.PrefixUrl((string)ef.Value)] = ef.Value;
        }
"""
        )

    def end_class(self, classname: str, field_names: List[str]) -> None:
        """Signal that we are done with this class."""
        with open(self.current_interface_target_file, "a") as f:
            f.write("}")
        if self.current_class_is_abstract:
            return

        self.current_constructor_signature.write(
            (
                "LoadingOptions? loadingOptions = null, "
                "Dictionary<object, object>? extensionFields = null) {"
            )
        )
        self.current_constructor_body.write("    }\n")
        self.current_loader.write(
            """
        Dictionary<object, object> extensionFields = new();
        foreach (KeyValuePair<object, object> v in doc_)
        {{
            if (!attr.Contains(v.Key))
            {{
                if (((string)v.Key).Contains(':'))
                {{
                    string ex = loadingOptions.ExpandUrl((string)v.Key, "", false, false, null);
                    extensionFields[ex] = v.Value;
                }}
                else
                {{
                    errors.Add(
                        new ValidationException($"invalid field {{v.Key}}," +
                        "expected one of {fields}"));
                    break;
                }}
            }}

        }}

        if (errors.Count > 0)
        {{
            throw new ValidationException("", errors);
        }}

        return new {classname}(
          """.format(
                classname=self.current_class,
                fields=", ".join(["`" + f + "`" for f in field_names]),
            )
        )
        self.current_loader.write(
            ",\n          ".join(
                self.safe_name(f) + ": " + self.safe_name(f) for f in field_names
            )
            + ",\n          "
            + "loadingOptions: loadingOptions"
            + "\n        );"
            + "\n    "
            + "}"
            + "\n"
        )
        self.current_serializer.write(
            """
        if (top)
        {
            if (loadingOptions.namespaces != null)
            {
                r["$namespaces"] = loadingOptions.namespaces;
            }

            if (this.loadingOptions.schemas != null)
            {
                r["$schemas"] = loadingOptions.schemas;
            }
        }

        return r;
    }

            """
        )
        with open(
            self.current_class_target_file,
            "a",
        ) as f:
            f.write(self.current_constructor_signature.getvalue())
            f.write(self.current_constructor_body.getvalue())
            f.write(self.current_loader.getvalue())
            f.write(self.current_serializer.getvalue())
            f.write(
                "\n"
                + "    static readonly System.Collections.Generic.HashSet<string>"
                + "attr = new() { "
                + ", ".join(['"' + shortname(f) + '"' for f in field_names])
                + " };"
            )
            f.write(
                """
}
"""
            )

    def type_loader(
        self, type_declaration: Union[List[Any], Dict[str, Any], str]
    ) -> TypeDef:
        if isinstance(type_declaration, MutableSequence):
            sub = [self.type_loader(i) for i in type_declaration]
            if len(sub) < 2:
                return sub[0]

            if len(sub) == 2:
                type_1 = sub[0]
                type_2 = sub[1]
                type_1_name = type_1.name
                type_2_name = type_2.name
                if type_1_name == "NullInstance" or type_2_name == "NullInstance":
                    non_null_type = type_1 if type_1.name != "NullInstance" else type_2
                    return self.declare_type(
                        TypeDef(
                            instance_type=f"Option<{non_null_type.instance_type}>",
                            name=f"optional_{non_null_type.name}",
                            init=(
                                (
                                    "new OptionalLoader"
                                    f"<{non_null_type.instance_type}>({non_null_type.name})"
                                )
                            ),
                            loader_type=f"ILoader<Option<{non_null_type.instance_type}>>",
                        )
                    )
            return self.declare_type(
                TypeDef(
                    instance_type="object",
                    name="union_of_{}".format("_or_".join(s.name for s in sub)),
                    loader_type="ILoader<object>",
                    init="new UnionLoader(new List<ILoader> {{ {} }})".format(
                        ", ".join(s.name for s in sub)
                    ),
                )
            )
        if isinstance(type_declaration, MutableMapping):
            if type_declaration["type"] in (
                "array",
                "https://w3id.org/cwl/salad#array",
            ):
                i = self.type_loader(type_declaration["items"])
                inner_instance_type = (
                    "string" if i.instance_type == "string" else "object"
                )
                return self.declare_type(
                    TypeDef(
                        instance_type=f"List<{inner_instance_type}>",
                        name=f"array_of_{i.name}",
                        loader_type=f"ILoader<List<{inner_instance_type}>>",
                        init=f"new ArrayLoader<{inner_instance_type}>({i.name})",
                    )
                )
            if type_declaration["type"] in ("enum", "https://w3id.org/cwl/salad#enum"):
                return self.type_loader_enum(type_declaration)
            if type_declaration["type"] in (
                "record",
                "https://w3id.org/cwl/salad#record",
            ):
                return self.declare_type(
                    TypeDef(
                        instance_type=self.safe_name(type_declaration["name"]),
                        name=self.safe_name(type_declaration["name"]) + "Loader",
                        init="new RecordLoader<{}>()".format(
                            self.safe_name(type_declaration["name"]),
                        ),
                        loader_type="ILoader<{}>".format(
                            self.safe_name(type_declaration["name"])
                        ),
                        abstract=type_declaration.get("abstract", False),
                    )
                )
            raise SchemaException("wft {}".format(type_declaration["type"]))
        if type_declaration in prims:
            return prims[type_declaration]
        if type_declaration in ("Expression", "https://w3id.org/cwl/cwl#Expression"):
            return self.declare_type(
                TypeDef(
                    name=self.safe_name(type_declaration) + "Loader",
                    init="new ExpressionLoader()",
                    loader_type="ILoader<string>",
                    instance_type="string",
                )
            )
        return self.collected_types[self.safe_name(type_declaration) + "Loader"]

    def type_loader_enum(self, type_declaration: Dict[str, Any]) -> TypeDef:
        for sym in type_declaration["symbols"]:
            self.add_vocab(shortname(sym), sym)
        enum_name = self.safe_name(type_declaration["name"])
        enum_module_name = enum_name
        enum_path = self.main_src_dir / f"{enum_module_name}.cs"
        self.modules.add(enum_module_name)
        self.record_types.add(enum_name)
        with open(enum_path, "w") as f:
            _logger.info("Writing file: %s", enum_path)
            f.write(
                """namespace {package};

public class {enum_name} : IEnumClass<{enum_name}>
{{
    private string _Name;
    private static readonly List<{enum_name}> members = new();
""".format(
                    enum_name=enum_name, package=self.package
                )
            )
            for sym in type_declaration["symbols"]:
                const = self.safe_name(sym).replace("-", "_").replace(".", "_").upper()
                f.write(
                    """    public static readonly {enum_name} {const} =
                            new("{val}");\n""".format(
                        const=const, val=self.safe_name(sym), enum_name=enum_name
                    )
                )
            f.write(
                """
    public string Name
    {{
        get {{ return _Name; }}
        private set {{ _Name = value; }}
    }}

    public static IList<{enum_name}> Members
    {{
        get {{ return members; }}
    }}

    private {enum_name}(string name)
    {{
        _Name = name;
        members.Add(this);
    }}

    public static {enum_name} Parse(string toParse)
    {{
        foreach ({enum_name} s in Members)
        {{
            if (toParse == s.Name)
                return s;
        }}

        throw new FormatException("Could not parse string.");
    }}

    public static bool Contains(string value)
    {{
        bool contains = false;
        foreach ({enum_name} s in Members)
        {{
            if (value == s.Name)
            {{
                contains = true;
                return contains;
            }}

        }}

        return contains;
    }}

    public static List<string> Symbols()
    {{
        return members.Select(m => m.Name).ToList();
    }}

    public override string ToString()
    {{
        return _Name;
    }}
}}
""".format(
                    enum_name=enum_name
                )
            )
        return self.declare_type(
            TypeDef(
                instance_type=enum_name,
                name=self.safe_name(type_declaration["name"] + "Loader"),
                init=f"new EnumLoader<{enum_name}>()",
                loader_type=f"ILoader<{enum_name}>",
            )
        )

    def declare_field(
        self,
        name: str,
        fieldtype: TypeDef,
        doc: Optional[str],
        optional: bool,
    ) -> None:
        """Output the code to load the given field."""
        safename = self.safe_name(name)
        fieldname = shortname(name)
        self.current_fieldtypes[safename] = fieldtype

        with open(self.current_interface_target_file, "a") as f:
            if doc:
                f.write(
                    """
    /// <summary>
{doc_str}
    /// </summary>
""".format(
                        doc_str=doc_to_doc_string(doc, indent_level=1)
                    )
                )
            if fieldname == "class":
                f.write(
                    "    public new {type} {safename} {{ get; set; }}\n".format(
                        safename=safename,
                        type=fieldtype.instance_type,
                    )
                )
            else:
                f.write(
                    "    public {type} {safename} {{ get; set; }}\n".format(
                        safename=safename,
                        type=fieldtype.instance_type,
                    )
                )
        if self.current_class_is_abstract:
            return

        with open(self.current_class_target_file, "a") as f:
            if doc:
                f.write(
                    """
    /// <summary>
{doc_str}
    /// </summary>
""".format(
                        doc_str=doc_to_doc_string(doc, indent_level=1)
                    )
                )
            f.write(
                "    public {type} {safename} {{ get; set; }}\n".format(
                    safename=safename, type=fieldtype.instance_type
                )
            )
        if fieldname == "class":
            if fieldtype.instance_type == "string":
                self.current_constructor_signature.write(
                    "string {safename},".format(safename=safename)
                )
            else:
                self.current_constructor_signature.write(
                    "{type} {safename},".format(
                        safename=safename, type=fieldtype.instance_type
                    )
                )
        else:
            self.current_constructor_signature.write(
                "{type} {safename},".format(
                    safename=safename,
                    type=fieldtype.instance_type,
                )
            )
        self.current_constructor_body.write(
            "        this.{safeName} = {safeName};\n".format(safeName=safename)
        )

        self.current_loader.write(
            """
        {type} {safename} = default!;""".format(
                safename=safename, type=fieldtype.instance_type
            )
        )
        if optional:
            self.current_loader.write(
                """
        if (doc_.ContainsKey("{fieldname}"))
        {{""".format(
                    fieldname=fieldname
                )
            )
            spc = "        "
        else:
            spc = "    "

        self.current_loader.write(
            """
{spc}    try
{spc}    {{
{spc}        {safename} = ({instancetype})LoaderInstances.{fieldtype}
{spc}           .LoadField(doc_.GetValueOrDefault("{fieldname}", null!), baseUri,
{spc}               loadingOptions);
{spc}    }}
{spc}    catch (ValidationException e)
{spc}    {{
{spc}        errors.Add(
{spc}          new ValidationException("the `{fieldname}` field is not valid because: ", e)
{spc}        );
{spc}    }}
""".format(
                safename=safename,
                fieldname=fieldname,
                fieldtype=fieldtype.name,
                instancetype=fieldtype.instance_type,
                spc=spc,
            )
        )
        if optional:
            self.current_loader.write("        }\n")

        if name == self.idfield or not self.idfield:
            baseurl = "baseUrl"
        else:
            baseurl = f"this.{self.safe_name(self.idfield)}"

        if optional:
            if (
                fieldtype.instance_type is not None
                and fieldtype.instance_type.startswith("Option<")
            ):
                self.current_serializer.write(
                    """
        {safename}.IfSome({safename} =>
        {{""".format(
                        safename=self.safe_name(name)
                    )
                )
            else:
                self.current_serializer.write(
                    """
        if({safename} != null)
        {{""".format(
                        safename=self.safe_name(name)
                    )
                )
        if fieldtype.is_uri:
            self.current_serializer.write(
                """
{spc}    r["{fieldname}"] = ISavable.SaveRelativeUri({safename}, {scoped_id},
{spc}                              relativeUris, {ref_scope}, (string){base_url}!);""".format(
                    safename=self.safe_name(name),
                    fieldname=shortname(name).strip(),
                    base_url=baseurl,
                    scoped_id=self.to_dotnet(fieldtype.scoped_id),
                    ref_scope=self.to_dotnet(fieldtype.ref_scope),
                    spc=spc,
                )
            )
        else:
            self.current_serializer.write(
                """
{spc}    r["{fieldname}"] =
{spc}       ISavable.Save({safename}, false, (string){base_url}!, relativeUris);""".format(
                    safename=self.safe_name(name),
                    fieldname=shortname(name).strip(),
                    base_url=baseurl,
                    spc=spc,
                )
            )

        if optional:
            if (
                fieldtype.instance_type is not None
                and fieldtype.instance_type.startswith("Option<")
            ):
                self.current_serializer.write(
                    """
        });
                    """
                )
            else:
                self.current_serializer.write(
                    """
        }
                    """
                )

    def declare_id_field(
        self,
        name: str,
        fieldtype: TypeDef,
        doc: str,
        optional: bool,
        subscope: Optional[str],
    ) -> None:
        """Output the code to handle the given ID field."""
        self.declare_field(name, fieldtype, doc, True)
        if optional:
            opt = """{safename} = "_" + Guid.NewGuid();""".format(
                safename=self.safe_name(name)
            )
        else:
            opt = """throw new ValidationException("Missing {fieldname}");""".format(
                fieldname=shortname(name)
            )

        if subscope is not None:
            name = name + subscope

        self.current_loader.write(
            """
        if ({safename} == null)
        {{
            if (docRoot != null)
            {{
                {safename} = docRoot;
            }}
            else
            {{
                {opt}
            }}
        }}
        else
        {{
            baseUri = (string){safename};
        }}
            """.format(
                safename=self.safe_name(name), opt=opt
            )
        )

    def to_dotnet(self, val: Any) -> Any:
        """Convert a Python keyword to a DotNet keyword."""
        if val is True:
            return "true"
        elif val is None:
            return "null"
        elif val is False:
            return "false"
        return val

    def uri_loader(
        self,
        inner: TypeDef,
        scoped_id: bool,
        vocab_term: bool,
        ref_scope: Optional[int],
    ) -> TypeDef:
        """Construct the TypeDef for the given URI loader."""
        instance_type = inner.instance_type or "object"
        return self.declare_type(
            TypeDef(
                instance_type=instance_type,
                name=f"uri{inner.name}{scoped_id}{vocab_term}{ref_scope}",
                loader_type="ILoader<{}>".format(instance_type),
                init="new UriLoader<{}>({}, {}, {}, {})".format(
                    instance_type,
                    inner.name,
                    self.to_dotnet(scoped_id),
                    self.to_dotnet(vocab_term),
                    self.to_dotnet(ref_scope),
                ),
                is_uri=True,
                scoped_id=scoped_id,
                ref_scope=ref_scope,
            )
        )

    def idmap_loader(
        self, field: str, inner: TypeDef, map_subject: str, map_predicate: Optional[str]
    ) -> TypeDef:
        """Construct the TypeDef for the given mapped ID loader."""
        instance_type = inner.instance_type or "object"
        return self.declare_type(
            TypeDef(
                instance_type=instance_type,
                name=f"idmap{self.safe_name(field)}{inner.name}",
                loader_type=f"ILoader<{instance_type}>",
                init='new IdMapLoader<{}>({}, "{}", "{}")'.format(
                    instance_type, inner.name, map_subject, map_predicate
                ),
            )
        )

    def typedsl_loader(self, inner: TypeDef, ref_scope: Optional[int]) -> TypeDef:
        """Construct the TypeDef for the given DSL loader."""
        instance_type = inner.instance_type or "object"
        return self.declare_type(
            TypeDef(
                instance_type=instance_type,
                name=f"typedsl{self.safe_name(inner.name)}{ref_scope}",
                loader_type=f"ILoader<{instance_type}>",
                init=(
                    f"new TypeDSLLoader<{instance_type}>"
                    f"({self.safe_name(inner.name)}, {ref_scope})"
                ),
            )
        )

    def epilogue(self, root_loader: TypeDef) -> None:
        """Trigger to generate the epilouge code."""
        pd = "This project contains DotNet objects and utilities "
        pd = pd + ' auto-generated by <a href=\\"https://github.com/'
        pd = pd + 'common-workflow-language/schema_salad\\">Schema Salad</a>'
        pd = pd + " for parsing documents corresponding to the "
        pd = pd + str(self.base_uri) + " schema."

        sorted_record_types = sorted(self.record_types)
        generated_class_imports = ",\n  ".join(sorted_record_types)
        template_vars: MutableMapping[str, str] = dict(
            project_name=self.package,
            version="0.0.1-SNAPSHOT",
            project_description=pd,
            license_name="Apache License, Version 2.0",
            generated_class_imports=generated_class_imports,
        )

        def template_from_resource(resource: str) -> string.Template:
            template_str = pkg_resources.resource_string(
                __name__, f"dotnet/{resource}"
            ).decode("utf-8")
            template = string.Template(template_str)
            return template

        def expand_resource_template_to(resource: str, path: Path) -> None:
            template = template_from_resource(resource)
            src = template.safe_substitute(template_vars)
            _ensure_directory_and_write(path, src)

        expand_resource_template_to(".gitignore", self.target_dir / ".gitignore")
        expand_resource_template_to("LICENSE", self.target_dir / "LICENSE")
        expand_resource_template_to("Solution.sln", self.target_dir / "Solution.sln")
        expand_resource_template_to(
            "Project.csproj",
            self.target_dir / self.package / Path(self.package + ".csproj"),
        )
        expand_resource_template_to(
            "AssemblyInfo.cs",
            self.target_dir / self.package / "Properties" / "AssemblyInfo.cs",
        )
        vocab = ",\n        ".join(
            f"""["{k}"] = "{self.vocab[k]}\"""" for k in sorted(self.vocab.keys())
        )
        rvocab = ",\n        ".join(
            f"""["{self.vocab[k]}"] = "{k}\"""" for k in sorted(self.vocab.keys())
        )

        loader_instances = ""
        for _, collected_type in self.collected_types.items():
            if not collected_type.abstract:
                loader_instances += "public static readonly {} {} = {};\n".format(
                    collected_type.loader_type, collected_type.name, collected_type.init
                )

        example_tests = ""

        #     if self.examples:
        #         _safe_makedirs(self.test_resources_dir)
        #         utils_resources = self.test_resources_dir / "examples"
        #         if os.path.exists(utils_resources):
        #             shutil.rmtree(utils_resources)
        #         shutil.copytree(self.examples, utils_resources)
        #         for example_name in os.listdir(self.examples):
        #             if example_name.startswith("valid"):
        #                 basename = os.path.basename(example_name).rsplit(".", 1)[0]
        #                 example_tests += """
        # it('{basename}', async () => {{
        #     await loadDocument(__dirname + '/data/examples/{example_name}')
        # }})
        # it('{basename} by string', async () => {{
        #     let doc = fs.readFileSync(__dirname + '/data/examples/{example_name}').toString()
        #     await loadDocumentByString(doc, url.pathToFileURL(__dirname +
        #         '/data/examples/').toString())
        # }})""".format(
        #                     basename=basename.replace("-", "_").replace(".", "_"),
        #                     example_name=example_name,
        #                 )

        template_args: MutableMapping[str, str] = dict(
            project_name=self.package,
            loader_instances=loader_instances,
            generated_class_imports=generated_class_imports,
            vocab=vocab,
            rvocab=rvocab,
            root_loader=root_loader.name,
            root_loader_type=root_loader.instance_type or "any",
            tests=example_tests,
        )

        util_src_dirs = {"util": self.main_src_dir / "util", "Test": self.test_src_dir}

        def copy_utils_recursive(util_src: str, util_target: Path) -> None:
            for util in pkg_resources.resource_listdir(__name__, f"dotnet/{util_src}"):
                template_path = os.path.join(util_src, util)
                if pkg_resources.resource_isdir(__name__, f"dotnet/{template_path}"):
                    copy_utils_recursive(
                        os.path.join(util_src, util), util_target / util
                    )
                    continue
                src_path = util_target / util
                src_template = template_from_resource(template_path)
                src = src_template.safe_substitute(template_args)
                _ensure_directory_and_write(src_path, src)

        for (util_src, util_target) in util_src_dirs.items():
            copy_utils_recursive(util_src, util_target)

    def secondaryfilesdsl_loader(self, inner: TypeDef) -> TypeDef:
        """Construct the TypeDef for secondary files."""
        instance_type = inner.instance_type or "any"
        return self.declare_type(
            TypeDef(
                name=f"secondaryfilesdsl{inner.name}",
                init=f"new SecondaryDSLLoader<{instance_type}>({inner.name})",
                loader_type=f"ILoader<{instance_type}>",
                instance_type=instance_type,
            )
        )
