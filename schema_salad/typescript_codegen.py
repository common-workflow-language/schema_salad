"""TypeScript code generator for a given schema salad definition."""
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

from . import schema, _logger
from .codegen_base import CodeGenBase, TypeDef
from .exceptions import SchemaException
from .schema import shortname
from .java_codegen import _ensure_directory_and_write, _safe_makedirs

_string_type_def = TypeDef(
    name="strtype",
    init="new _PrimitiveLoader(TypeGuards.String)",
    instance_type="string",
)

_int_type_def = TypeDef(
    name="inttype", init="new _PrimitiveLoader(TypeGuards.Int)", instance_type="number"
)

_float_type_def = TypeDef(
    name="floattype",
    init="new _PrimitiveLoader(TypeGuards.Float)",
    instance_type="number",
)
_bool_type_def = TypeDef(
    name="booltype",
    init="new _PrimitiveLoader(TypeGuards.Bool)",
    instance_type="boolean",
)

_null_type_def = TypeDef(
    name="undefinedtype",
    init="new _PrimitiveLoader(TypeGuards.Undefined)",
    instance_type="undefined",
)

_any_type_def = TypeDef(name="anyType", init="new _AnyLoader()", instance_type="any")

prims = {
    "http://www.w3.org/2001/XMLSchema#string": _string_type_def,
    "http://www.w3.org/2001/XMLSchema#int": _int_type_def,
    "http://www.w3.org/2001/XMLSchema#long": _int_type_def,
    "http://www.w3.org/2001/XMLSchema#float": _float_type_def,
    "http://www.w3.org/2001/XMLSchema#double": _float_type_def,
    "http://www.w3.org/2001/XMLSchema#boolean": _bool_type_def,
    "https://w3id.org/cwl/salad#null": _null_type_def,
    "https://w3id.org/cwl/salad#Any": _any_type_def,
    "string": _string_type_def,
    "int": _int_type_def,
    "long": _int_type_def,
    "float": _float_type_def,
    "double": _float_type_def,
    "boolean": _bool_type_def,
    "null": _null_type_def,
    "Any": _any_type_def,
}


class TypeScriptCodeGen(CodeGenBase):
    """Generation of TypeScript code for a given Schema Salad definition."""

    def __init__(self, base: str, target: Optional[str], package: str) -> None:
        """Initialize the TypeScript codegen."""
        super().__init__()
        self.target_dir = Path(target or ".").resolve()
        self.main_src_dir = self.target_dir / "src"
        self.package = package
        self.base_uri = base
        self.record_types: List[str] = []

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
        classname = self.safe_name(classname)
        self.current_class = classname
        self.current_class_is_abstract = abstract
        self.record_types.append(classname)
        self.current_constructor_signature = StringIO()
        self.current_constructor_body = StringIO()
        self.current_loader = StringIO()
        self.current_fieldtypes: Dict[str, TypeDef] = {}
        target_file = self.main_src_dir / f"{classname[0].lower() + classname[1:]}.ts"

        if self.current_class_is_abstract:
            with open(target_file, "w") as f:
                _logger.info("Writing file: %s", target_file)
                if extends:
                    ext = " extends Internal." + ", Internal.".join(
                        self.safe_name(e) for e in extends
                    )
                else:
                    ext = ""
                f.write(
                    """
import * as Internal from './util/internal'

export interface {cls} {ext} {{ }}
                    """.format(
                        cls=classname,
                        ext=ext,
                    )
                )
            return

        with open(target_file, "w") as f:
            _logger.info("Writing file: %s", target_file)
            if extends:
                ext = "extends Saveable implements Internal." + ", Internal.".join(
                    self.safe_name(e) for e in extends
                )
            else:
                ext = "extends Saveable"
            f.write(
                """
import {{
  Dictionary,
  expandUrl,
  loadField,
  LoaderInstances,
  LoadingOptions,
  Saveable,
  ValidationException,
}} from './util/internal'
import {{ v4 as uuidv4 }} from 'uuid'
import * as Internal from './util/internal'

export class {cls} {ext} {{
  loadingOptions: LoadingOptions
  extensionFields?: Dictionary<any>
""".format(
                    cls=classname,
                    ext=ext,
                )
            )
        self.current_constructor_signature.write(
            "\n" + "\n" + "  constructor ({extensionFields, loadingOptions"
        )
        self.current_constructor_body.write(
            """
    super()
    this.extensionFields = extensionFields ?? {}
    this.loadingOptions = loadingOptions ?? new LoadingOptions({})
"""
        )
        self.current_loader.write(
            """
  static override async fromDoc (__doc: any, baseuri: string, loadingOptions: LoadingOptions,
    docRoot?: string): Promise<Saveable> {
    const _doc = Object.assign({}, __doc)
    const errors: ValidationException[] = []
            """
        )

    def end_class(self, classname: str, field_names: List[str]) -> None:
        """Signal that we are done with this class."""
        if self.current_class_is_abstract:
            return

        self.current_constructor_signature.write(
            "} : {extensionFields?: Dictionary<any>, loadingOptions?: LoadingOptions, "
        )
        for field_name in field_names:
            safe_field_name = self.safe_name(field_name)
            fieldtype = self.current_fieldtypes.get(safe_field_name)
            if fieldtype is None:
                raise SchemaException(f"{safe_field_name} has no valid fieldtype")
            self.current_constructor_signature.write(
                """ {safename}: {type},""".format(
                    safename=safe_field_name, type=fieldtype.instance_type
                )
            )
        self.current_constructor_signature.write("}) {")
        self.current_constructor_body.write("  }\n")
        self.current_loader.write(
            """
    const extensionFields: Dictionary<any> = {{}}
    for (const [key, value] of _doc) {{
      if (!this.attr.has(key)) {{
        if ((key as string).includes(':')) {{
          const ex = expandUrl(key, '', loadingOptions, false, false)
          extensionFields[ex] = value
        }} else {{
          errors.push(
            new ValidationException(`invalid field ${{key as string}}, \\
            expected one of: {fields}`)
          )
          break
        }}
      }}
    }}

    if (errors.length > 0) {{
      throw new ValidationException("Trying '{classname}'", errors)
    }}

    const schema = new {classname}({{
      extensionFields: extensionFields,
      loadingOptions: loadingOptions,
      """.format(
                classname=self.current_class,
                fields=",".join(["\\`" + f + "\\`" for f in field_names]),
            )
        )
        self.current_loader.write(
            ",\n      ".join(
                self.safe_name(f) + ": " + self.safe_name(f) for f in field_names
            )
            + "\n    })"
        )
        self.current_loader.write(
            """
    return schema
  }
        """
        )
        target_file = (
            self.main_src_dir
            / f"{self.current_class[0].lower() + self.current_class[1:]}.ts"
        )

        with open(
            target_file,
            "a",
        ) as f:
            f.write(self.current_constructor_signature.getvalue())
            f.write(self.current_constructor_body.getvalue())
            f.write(self.current_loader.getvalue())
            f.write(
                "\n"
                + "  static attr: Set<string> = new Set(["
                + ",".join(["'" + shortname(f) + "'" for f in field_names])
                + "])"
            )
            f.write(
                """
}
"""
            )

    def type_loader(
        self, type_declaration: Union[List[Any], Dict[str, Any], str]
    ) -> TypeDef:
        """Parse the given type declaration and declare its components."""
        if isinstance(type_declaration, MutableSequence):
            sub_types = [self.type_loader(i) for i in type_declaration]
            sub_names: List[str] = list(dict.fromkeys([i.name for i in sub_types]))
            sub_instance_types: List[str] = list(
                dict.fromkeys(
                    [i.instance_type for i in sub_types if i.instance_type is not None]
                )
            )
            return self.declare_type(
                TypeDef(
                    "unionOf{}".format("Or".join(sub_names)),
                    "new _UnionLoader([{}])".format(", ".join(sub_names)),
                    instance_type=" | ".join(sub_instance_types),
                )
            )
        if isinstance(type_declaration, MutableMapping):
            if type_declaration["type"] in (
                "array",
                "https://w3id.org/cwl/salad#array",
            ):
                i = self.type_loader(type_declaration["items"])
                return self.declare_type(
                    TypeDef(
                        f"arrayOf{i.name}",
                        f"new _ArrayLoader([{i.name}])",
                        instance_type=f"Array<{i.instance_type}>",
                    )
                )
            if type_declaration["type"] in ("enum", "https://w3id.org/cwl/salad#enum"):
                for sym in type_declaration["symbols"]:
                    self.add_vocab(shortname(sym), sym)
                return self.declare_type(
                    TypeDef(
                        self.safe_name(type_declaration["name"]) + "Loader",
                        'new _EnumLoader(["{}"])'.format(
                            '", "'.join(
                                self.safe_name(sym)
                                for sym in type_declaration["symbols"]
                            )
                        ),
                        instance_type="string",
                    )
                )

            if type_declaration["type"] in (
                "record",
                "https://w3id.org/cwl/salad#record",
            ):
                return self.declare_type(
                    TypeDef(
                        self.safe_name(type_declaration["name"]) + "Loader",
                        "new _RecordLoader({}.fromDoc)".format(
                            self.safe_name(type_declaration["name"]),
                        ),
                        instance_type="Internal."
                        + self.safe_name(type_declaration["name"]),
                        abstract=type_declaration.get("abstract", False),
                    )
                )
            raise SchemaException("wft {}".format(type_declaration["type"]))

        if type_declaration in prims:
            return prims[type_declaration]

        if type_declaration in ("Expression", "https://w3id.org/cwl/cwl#Expression"):
            return self.declare_type(
                TypeDef(
                    self.safe_name(type_declaration) + "Loader",
                    "new _ExpressionLoader()",
                    instance_type="string",
                )
            )
        return self.collected_types[self.safe_name(type_declaration) + "Loader"]

    def declare_field(
        self,
        name: str,
        fieldtype: TypeDef,
        doc: Optional[str],
        optional: bool,
    ) -> None:
        """Output the code to load the given field."""
        if self.current_class_is_abstract:
            return

        target_file = (
            self.main_src_dir
            / f"{self.current_class[0].lower() + self.current_class[1:]}.ts"
        )
        safename = self.safe_name(name)
        fieldname = shortname(name)
        self.current_fieldtypes[safename] = fieldtype
        with open(target_file, "a") as f:
            f.write(
                "  {safename}: {type}\n".format(
                    safename=safename,
                    type=fieldtype.instance_type,
                )
            )
        self.current_constructor_signature.write(
            ", {safename}".format(
                safename=safename,
            )
        )
        self.current_constructor_body.write(
            "    this.{safeName} = {safeName}\n".format(safeName=safename)
        )

        self.current_loader.write(
            """
    let {safename}""".format(
                safename=safename
            )
        )
        if optional:
            self.current_loader.write(
                """
    if ('{fieldname}' in _doc) {{""".format(
                    fieldname=fieldname
                )
            )
            spc = "  "
        else:
            spc = ""

        self.current_loader.write(
            """
{spc}    try {{
{spc}      {safename} = await loadField(_doc.{fieldname}, LoaderInstances.{fieldtype},
{spc}        baseuri, loadingOptions)
{spc}    }} catch (e) {{
{spc}      if (e instanceof ValidationException) {{
{spc}        errors.push(
{spc}          new ValidationException('the `{fieldname}` field is not valid because: ', [e])
{spc}        )
{spc}      }}
{spc}    }}
""".format(
                safename=safename,
                fieldname=fieldname,
                fieldtype=fieldtype.name,
                spc=spc,
            )
        )
        if optional:
            self.current_loader.write("    }\n")

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
            opt = """{safename} = "_" + uuidv4()""".format(
                safename=self.safe_name(name)
            )
        else:
            opt = """throw new ValidationException("Missing {fieldname}")""".format(
                fieldname=shortname(name)
            )

        if subscope is not None:
            name = name + subscope

        self.current_loader.write(
            """
    const original{safename}IsUndefined = ({safename} === undefined)
    if (original{safename}IsUndefined ) {{
      if (docRoot != null) {{
        {safename} = docRoot
      }} else {{
        {opt}
      }}
    }} else {{
      baseuri = {safename} as string
    }}
            """.format(
                safename=self.safe_name(name), opt=opt
            )
        )

    def to_typescript(self, val: Any) -> Any:
        """Convert a Python keyword to a TypeScript keyword."""
        if val is True:
            return "true"
        elif val is None:
            return "undefined"
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
        instance_type = inner.instance_type or "any"
        return self.declare_type(
            TypeDef(
                f"uri{inner.name}{scoped_id}{vocab_term}{ref_scope}",
                "new _URILoader({}, {}, {}, {})".format(
                    inner.name,
                    self.to_typescript(scoped_id),
                    self.to_typescript(vocab_term),
                    self.to_typescript(ref_scope),
                ),
                is_uri=True,
                scoped_id=scoped_id,
                ref_scope=ref_scope,
                instance_type=instance_type,
            )
        )

    def idmap_loader(
        self, field: str, inner: TypeDef, map_subject: str, map_predicate: Optional[str]
    ) -> TypeDef:
        """Construct the TypeDef for the given mapped ID loader."""
        instance_type = inner.instance_type or "any"
        return self.declare_type(
            TypeDef(
                f"idmap{self.safe_name(field)}{inner.name}",
                "new _IdMapLoader({}, '{}', '{}')".format(
                    inner.name, map_subject, map_predicate
                ),
                instance_type=instance_type,
            )
        )

    def typedsl_loader(self, inner: TypeDef, ref_scope: Optional[int]) -> TypeDef:
        """Construct the TypeDef for the given DSL loader."""
        instance_type = inner.instance_type or "any"
        return self.declare_type(
            TypeDef(
                f"typedsl{self.safe_name(inner.name)}{ref_scope}",
                f"new _TypeDSLLoader({self.safe_name(inner.name)}, {ref_scope})",
                instance_type=instance_type,
            )
        )

    def epilogue(self, root_loader: TypeDef) -> None:
        """Trigger to generate the epilouge code."""
        pd = "This project contains TypeScript objects and utilities "
        pd = pd + ' auto-generated by <a href=\\"https://github.com/'
        pd = pd + 'common-workflow-language/schema_salad\\">Schema Salad</a>'
        pd = pd + " for parsing documents corresponding to the "
        pd = pd + str(self.base_uri) + " schema."

        template_vars: MutableMapping[str, str] = dict(
            project_name=self.package,
            version="0.0.1-SNAPSHOT",
            project_description=pd,
            license_name="Apache License, Version 2.0",
        )

        def template_from_resource(resource: str) -> string.Template:
            template_str = pkg_resources.resource_string(
                __name__, f"typescript/{resource}"
            ).decode("utf-8")
            template = string.Template(template_str)
            return template

        def expand_resource_template_to(resource: str, path: Path) -> None:
            template = template_from_resource(resource)
            src = template.safe_substitute(template_vars)
            _ensure_directory_and_write(path, src)

        expand_resource_template_to("package.json", self.target_dir / "package.json")
        expand_resource_template_to(".gitignore", self.target_dir / ".gitignore")
        expand_resource_template_to("LICENSE", self.target_dir / "LICENSE")
        expand_resource_template_to("tsconfig.json", self.target_dir / "tsconfig.json")

        vocab = ",\n  ".join(
            f"""'{k}': '{self.vocab[k]}'""" for k in sorted(self.vocab.keys())
        )
        rvocab = ",\n  ".join(
            f"""'{self.vocab[k]}': '{k}'""" for k in sorted(self.vocab.keys())
        )

        loader_instances = ""
        for _, collected_type in self.collected_types.items():
            if not collected_type.abstract:
                loader_instances += "export const {} = {};\n".format(
                    collected_type.name, collected_type.init
                )
        generated_class_imports = ",\n  ".join(self.record_types)
        internal_module_exports = "\n".join(
            "export * from '../{}'".format(f[0].lower() + f[1:])
            for f in self.record_types
        )
        template_args: MutableMapping[str, str] = dict(
            internal_module_exports=internal_module_exports,
            loader_instances=loader_instances,
            generated_class_imports=generated_class_imports,
            vocab=vocab,
            rvocab=rvocab,
        )

        util_src_dirs = {
            "util": self.main_src_dir / "util",
            "test": self.main_src_dir / "test",
        }

        def copy_utils_recursive(util_src: str, util_target: Path) -> None:
            for util in pkg_resources.resource_listdir(
                __name__, f"typescript/{util_src}"
            ):
                template_path = os.path.join(util_src, util)
                if pkg_resources.resource_isdir(
                    __name__, f"typescript/{template_path}"
                ):
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
                f"secondaryfilesdsl{inner.name}",
                f"new _SecondaryDSLLoader({inner.name})",
                instance_type=instance_type,
            )
        )
