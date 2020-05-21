"""Java code generator for a given schema salad definition."""
import os
import shutil
import string
from io import StringIO
from io import open as io_open
from typing import (
    Any,
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Union,
    Set,
)
from urllib.parse import urlsplit

import pkg_resources

from . import schema
from .codegen_base import CodeGenBase, TypeDef
from .exceptions import SchemaException
from .schema import shortname

# experiment at providing more typed objects building a optional type that allows
# referencing one or a list of objects. It is useful for improving the RootLoader
# for simple schema with a single root loader - but doesn't help with CWL at all and
# may even confuse things a bit so turning these off be default.
USE_ONE_OR_LIST_OF_TYPES = False


def _ensure_directory_and_write(path: str, contents: str) -> None:
    dirname = os.path.dirname(path)
    _safe_makedirs(dirname)
    with io_open(path, mode="w", encoding="utf-8") as f:
        f.write(contents)


def doc_to_doc_string(doc: Optional[str], indent_level: int = 0) -> str:
    lead = " " + "  " * indent_level + "* " * indent_level
    if doc:
        doc_str = "{}<BLOCKQUOTE>\n".format(lead)
        doc_str += "\n".join(["{}{}".format(lead, line) for line in doc.split("\n")])
        doc_str += "{}</BLOCKQUOTE>".format(lead)
    else:
        doc_str = ""
    return doc_str


def _safe_makedirs(path):
    # type: (str) -> None
    if not os.path.exists(path):
        os.makedirs(path)


prims = {
    "http://www.w3.org/2001/XMLSchema#string": TypeDef(
        instance_type="String",
        init="new PrimitiveLoader<String>(String.class)",
        name="StringInstance",
        loader_type="Loader<String>",
    ),
    "http://www.w3.org/2001/XMLSchema#int": TypeDef(
        instance_type="Integer",
        init="new PrimitiveLoader<Integer>(Integer.class)",
        name="IntegerInstance",
        loader_type="Loader<Integer>",
    ),
    "http://www.w3.org/2001/XMLSchema#long": TypeDef(
        instance_type="Long",
        name="LongInstance",
        loader_type="Loader<Long>",
        init="new PrimitiveLoader<Long>(Long.class)",
    ),
    "http://www.w3.org/2001/XMLSchema#float": TypeDef(
        instance_type="Float",
        name="FloatInstance",
        loader_type="Loader<Float>",
        init="new PrimitiveLoader<Float>(Float.class)",
    ),
    "http://www.w3.org/2001/XMLSchema#double": TypeDef(
        instance_type="Double",
        name="DoubleInstance",
        loader_type="Loader<Double>",
        init="new PrimitiveLoader<Double>(Double.class)",
    ),
    "http://www.w3.org/2001/XMLSchema#boolean": TypeDef(
        instance_type="Boolean",
        name="BooleanInstance",
        loader_type="Loader<Boolean>",
        init="new PrimitiveLoader<Boolean>(Boolean.class)",
    ),
    "https://w3id.org/cwl/salad#null": TypeDef(
        instance_type="Object",
        name="NullInstance",
        loader_type="Loader<Object>",
        init="new NullLoader()",
    ),
    "https://w3id.org/cwl/salad#Any": TypeDef(
        instance_type="Object",
        name="AnyInstance",
        init="new AnyLoader()",
        loader_type="Loader<Object>",
    ),
}


class JavaCodeGen(CodeGenBase):
    def __init__(
        self, base: str, target: Optional[str], examples: Optional[str]
    ) -> None:
        super(JavaCodeGen, self).__init__()
        self.base_uri = base
        sp = urlsplit(base)
        self.examples = examples
        self.package = ".".join(
            list(reversed(sp.netloc.split("."))) + sp.path.strip("/").split("/")
        )
        self.artifact = self.package.split(".")[-1]
        target = target or "."
        self.target_dir = target
        rel_package_dir = self.package.replace(".", "/")
        self.rel_package_dir = rel_package_dir
        self.main_src_dir = os.path.join(
            self.target_dir, "src", "main", "java", rel_package_dir
        )
        self.test_src_dir = os.path.join(
            self.target_dir, "src", "test", "java", rel_package_dir
        )
        self.test_resources_dir = os.path.join(
            self.target_dir, "src", "test", "resources", rel_package_dir
        )

    def prologue(self) -> None:
        for src_dir in [self.main_src_dir, self.test_src_dir]:
            _safe_makedirs(src_dir)

        for primitive in prims.values():
            self.declare_type(primitive)

    @staticmethod
    def property_name(name: str) -> str:
        avn = schema.avro_name(name)
        return avn

    @staticmethod
    def safe_name(name: str) -> str:
        avn = JavaCodeGen.property_name(name)
        if avn in ("class", "extends", "abstract", "default", "package"):
            # reserved words
            avn = avn + "_"
        return avn

    def interface_name(self, n: str) -> str:
        return self.safe_name(n)

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
        cls = self.interface_name(classname)
        self.current_class = cls
        self.current_class_is_abstract = abstract
        self.current_loader = StringIO()
        self.current_fieldtypes = {}  # type: Dict[str, TypeDef]
        self.current_fields = StringIO()
        interface_doc_str = "* Auto-generated interface for <I>%s</I><BR>" % classname
        if not abstract:
            implemented_by = "This interface is implemented by {{@link {}Impl}}<BR>"
            interface_doc_str += implemented_by.format(cls)
        interface_doc_str += doc_to_doc_string(doc)
        class_doc_str = "* Auto-generated class implementation for <I>{}</I><BR>".format(
            classname
        )
        class_doc_str += doc_to_doc_string(doc)
        with open(os.path.join(self.main_src_dir, "{}.java".format(cls)), "w") as f:

            if extends:
                ext = (
                    "extends "
                    + ", ".join(self.interface_name(e) for e in extends)
                    + ", Savable"
                )
            else:
                ext = "extends Savable"
            f.write(
                """package {package};

import {package}.utils.Savable;

/**
{interface_doc_str}
 */
public interface {cls} {ext} {{""".format(
                    package=self.package,
                    cls=cls,
                    ext=ext,
                    interface_doc_str=interface_doc_str,
                )
            )

        if self.current_class_is_abstract:
            return

        with open(os.path.join(self.main_src_dir, "{}Impl.java".format(cls)), "w") as f:
            f.write(
                """package {package};

import {package}.utils.LoaderInstances;
import {package}.utils.LoadingOptions;
import {package}.utils.LoadingOptionsBuilder;
import {package}.utils.SavableImpl;
import {package}.utils.ValidationException;

/**
{class_doc_str}
 */
public class {cls}Impl extends SavableImpl implements {cls} {{
  private LoadingOptions loadingOptions_ = new LoadingOptionsBuilder().build();
  private java.util.Map<String, Object> extensionFields_ =
      new java.util.HashMap<String, Object>();
""".format(
                    package=self.package, cls=cls, class_doc_str=class_doc_str
                )
            )
        self.current_loader.write(
            """
  /**
   * Used by {{@link {package}.utils.RootLoader}} to construct instances of {cls}Impl.
   *
   * @param __doc_            Document fragment to load this record object from (presumably a
                              {{@link java.util.Map}}).
   * @param __baseUri_        Base URI to generate child document IDs against.
   * @param __loadingOptions  Context for loading URIs and populating objects.
   * @param __docRoot_        ID at this position in the document (if available) (maybe?)
   * @throws ValidationException If the document fragment is not a {{@link java.util.Map}}
   *                             or validation of fields fails.
   */
  public {cls}Impl(
      final Object __doc_,
      final String __baseUri_,
      LoadingOptions __loadingOptions,
      final String __docRoot_) {{
    super(__doc_, __baseUri_, __loadingOptions, __docRoot_);
    // Prefix plumbing variables with '__' to reduce likelihood of collision with
    // generated names.
    String __baseUri = __baseUri_;
    String __docRoot = __docRoot_;
    if (!(__doc_ instanceof java.util.Map)) {{
      throw new ValidationException("{cls}Impl called on non-map");
    }}
    final java.util.Map<String, Object> __doc = (java.util.Map<String, Object>) __doc_;
    final java.util.List<ValidationException> __errors =
        new java.util.ArrayList<ValidationException>();
    if (__loadingOptions != null) {{
      this.loadingOptions_ = __loadingOptions;
    }}
""".format(
                cls=cls, package=self.package
            )
        )

    def end_class(self, classname, field_names):
        # type: (str, List[str]) -> None
        with open(
            os.path.join(self.main_src_dir, "{}.java".format(self.current_class)), "a"
        ) as f:
            f.write(
                """
}
"""
            )
        if self.current_class_is_abstract:
            return

        self.current_loader.write(
            """    if (!__errors.isEmpty()) {
      throw new ValidationException("Trying 'RecordField'", __errors);
    }
"""
        )
        for fieldname in field_names:
            fieldtype = self.current_fieldtypes.get(fieldname)
            if fieldtype is None:
                continue
            self.current_loader.write(
                """    this.{safename} = ({type}) {safename};
""".format(
                    safename=self.safe_name(fieldname), type=fieldtype.instance_type
                )
            )

        self.current_loader.write("""  }""")

        with open(
            os.path.join(self.main_src_dir, "{}Impl.java".format(self.current_class)),
            "a",
        ) as f:
            f.write(self.current_fields.getvalue())
            f.write(self.current_loader.getvalue())
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
                            instance_type="java.util.Optional<{}>".format(
                                non_null_type.instance_type
                            ),
                            init="new OptionalLoader({})".format(non_null_type.name),
                            name="optional_{}".format(non_null_type.name),
                            loader_type="Loader<java.util.Optional<{}>>".format(
                                non_null_type.instance_type
                            ),
                        )
                    )
                if (
                    type_1_name == "array_of_{}".format(type_2_name)
                    or type_2_name == "array_of_{}".format(type_1_name)
                ) and USE_ONE_OR_LIST_OF_TYPES:
                    if type_1_name == "array_of_{}".format(type_2_name):
                        single_type = type_2
                        array_type = type_1
                    else:
                        single_type = type_1
                        array_type = type_2
                    fqclass = "{}.{}".format(self.package, single_type.instance_type)
                    return self.declare_type(
                        TypeDef(
                            instance_type="{}.utils.OneOrListOf<{}>".format(
                                self.package, fqclass
                            ),
                            init="new OneOrListOfLoader<{}>({}, {})".format(
                                fqclass, single_type.name, array_type.name
                            ),
                            name="one_or_array_of_{}".format(single_type.name),
                            loader_type="Loader<{}.utils.OneOrListOf<{}>>".format(
                                self.package, fqclass
                            ),
                        )
                    )
            return self.declare_type(
                TypeDef(
                    instance_type="Object",
                    init="new UnionLoader(new Loader[] {{ {} }})".format(
                        ", ".join(s.name for s in sub)
                    ),
                    name="union_of_{}".format("_or_".join(s.name for s in sub)),
                    loader_type="Loader<Object>",
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
                        # special doesn't work out with subclassing, gotta be more clever
                        # instance_type="List<{}>".format(i.instance_type),
                        instance_type="java.util.List<Object>",
                        name="array_of_{}".format(i.name),
                        init="new ArrayLoader({})".format(i.name),
                        loader_type="Loader<java.util.List<{}>>".format(
                            i.instance_type
                        ),
                    )
                )
            if type_declaration["type"] in ("enum", "https://w3id.org/cwl/salad#enum"):
                return self.type_loader_enum(type_declaration)
            if type_declaration["type"] in (
                "record",
                "https://w3id.org/cwl/salad#record",
            ):
                is_abstract = type_declaration.get("abstract", False)
                fqclass = "{}.{}".format(
                    self.package, self.safe_name(type_declaration["name"])
                )
                return self.declare_type(
                    TypeDef(
                        instance_type=self.safe_name(type_declaration["name"]),
                        name=self.safe_name(type_declaration["name"]),
                        init="new RecordLoader<{clazz}>({clazz}{ext}.class)".format(
                            clazz=fqclass, ext="Impl" if not is_abstract else "",
                        ),
                        loader_type="Loader<{}>".format(fqclass),
                    )
                )
            raise SchemaException("wft {}".format(type_declaration["type"]))
        if type_declaration in prims:
            return prims[type_declaration]
        return self.collected_types[self.safe_name(type_declaration)]

    def type_loader_enum(self, type_declaration: Dict[str, Any]) -> TypeDef:
        symbols = [self.property_name(sym) for sym in type_declaration["symbols"]]
        for sym in symbols:
            self.add_vocab(shortname(sym), sym)
        clazz = self.safe_name(type_declaration["name"])
        symbols_decl = 'new String[] {{"{}"}}'.format(
            '", "'.join(sym for sym in symbols)
        )
        enum_path = os.path.join(self.main_src_dir, "{}.java".format(clazz))
        with open(enum_path, "w") as f:
            f.write(
                """package {package};

import {package}.utils.ValidationException;

public enum {clazz} {{
""".format(
                    package=self.package, clazz=clazz
                )
            )
            for i, sym in enumerate(symbols):
                suffix = "," if i < (len(symbols) - 1) else ";"
                const = self.safe_name(sym).replace("-", "_").replace(".", "_").upper()
                f.write(
                    """  {const}("{val}"){suffix}\n""".format(
                        const=const, val=sym, suffix=suffix
                    )
                )
            f.write(
                """
  private static String[] symbols = {symbols_decl};
  private String docVal;

  private {clazz}(final String docVal) {{
    this.docVal = docVal;
  }}

  public static {clazz} fromDocumentVal(final String docVal) {{
    for(final {clazz} val : {clazz}.values()) {{
      if(val.docVal.equals(docVal)) {{
        return val;
      }}
    }}
    throw new ValidationException(String.format("Expected one of %s", {clazz}.symbols, docVal));
  }}
}}
""".format(
                    clazz=clazz, symbols_decl=symbols_decl
                )
            )
        return self.declare_type(
            TypeDef(
                instance_type=clazz,
                name=self.safe_name(type_declaration["name"]),
                loader_type="Loader<{clazz}>".format(clazz=clazz),
                init="new EnumLoader({clazz}.class)".format(clazz=clazz),
            )
        )

    def declare_field(
        self, name: str, fieldtype: TypeDef, doc: Optional[str], optional: bool
    ) -> None:
        fieldname = name
        property_name = self.property_name(fieldname)
        cap_case_property_name = property_name[0].upper() + property_name[1:]
        if cap_case_property_name == "Class":
            cap_case_property_name = "Class_"

        safename = self.safe_name(fieldname)
        self.current_fieldtypes[property_name] = fieldtype
        getter_doc_str = """  /**
   * Getter for property <I>{fieldname}</I><BR>
{field_doc_str}
   */
""".format(
            fieldname=fieldname, field_doc_str=doc_to_doc_string(doc, indent_level=1)
        )
        with open(
            os.path.join(self.main_src_dir, "{}.java".format(self.current_class)), "a"
        ) as f:
            f.write(
                """
{getter_doc_str}
  {type} get{capfieldname}();""".format(
                    getter_doc_str=getter_doc_str,
                    capfieldname=cap_case_property_name,
                    type=fieldtype.instance_type,
                )
            )

        if self.current_class_is_abstract:
            return

        self.current_fields.write(
            """
  private {type} {safename};

{getter_doc_str}
  public {type} get{capfieldname}() {{
    return this.{safename};
  }}
""".format(
                safename=safename,
                capfieldname=cap_case_property_name,
                getter_doc_str=getter_doc_str,
                type=fieldtype.instance_type,
            )
        )

        self.current_loader.write(
            """    {type} {safename};
""".format(
                type=fieldtype.instance_type, safename=safename
            )
        )
        if optional:
            self.current_loader.write(
                """
    if (__doc.containsKey("{fieldname}")) {{
""".format(
                    fieldname=property_name
                )
            )
            spc = "  "
        else:
            spc = ""

        self.current_loader.write(
            """{spc}    try {{
{spc}      {safename} =
{spc}          LoaderInstances
{spc}              .{fieldtype}
{spc}              .loadField(__doc.get("{fieldname}"), __baseUri, __loadingOptions);
{spc}    }} catch (ValidationException e) {{
{spc}      {safename} = null; // won't be used but prevents compiler from complaining.
{spc}      final String __message = "the `{fieldname}` field is not valid because:";
{spc}      __errors.add(new ValidationException(__message, e));
{spc}    }}
""".format(
                fieldtype=fieldtype.name,
                safename=safename,
                fieldname=property_name,
                spc=spc,
            )
        )

        if optional:
            self.current_loader.write(
                """
    }} else {{
      {safename} = null;
    }}
""".format(
                    safename=safename
                )
            )

    def declare_id_field(
        self, name: str, fieldtype: TypeDef, doc: str, optional: bool
    ) -> None:
        if self.current_class_is_abstract:
            return

        self.declare_field(name, fieldtype, doc, True)
        if optional:
            set_uri = """
    if ({safename} == null) {{
      if (__docRoot != null) {{
        {safename} = java.util.Optional.of(__docRoot);
      }} else {{
        {safename} = java.util.Optional.of("_:" + java.util.UUID.randomUUID().toString());
      }}
    }}
    __baseUri = (String) {safename}.orElse(null);
"""
        else:
            set_uri = """
    if ({safename} == null) {{
      if (__docRoot != null) {{
        {safename} = __docRoot;
      }} else {{
        throw new ValidationException("Missing {fieldname}");
      }}
    }}
    __baseUri = (String) {safename};
"""
        self.current_loader.write(
            set_uri.format(safename=self.safe_name(name), fieldname=shortname(name))
        )

    def uri_loader(
        self,
        inner: TypeDef,
        scoped_id: bool,
        vocab_term: bool,
        ref_scope: Optional[int],
    ) -> TypeDef:
        assert inner is not None
        instance_type = inner.instance_type or "Object"
        return self.declare_type(
            TypeDef(
                instance_type=instance_type,  # ?
                name="uri_{}_{}_{}_{}".format(
                    inner.name, scoped_id, vocab_term, ref_scope
                ),
                init="new UriLoader({}, {}, {}, {})".format(
                    inner.name,
                    self.to_java(scoped_id),
                    self.to_java(vocab_term),
                    self.to_java(ref_scope),
                ),
                is_uri=True,
                scoped_id=scoped_id,
                ref_scope=ref_scope,
                loader_type="Loader<{}>".format(instance_type),
            )
        )

    def idmap_loader(
        self, field: str, inner: TypeDef, map_subject: str, map_predicate: Optional[str]
    ) -> TypeDef:
        assert inner is not None
        instance_type = inner.instance_type or "Object"
        return self.declare_type(
            TypeDef(
                instance_type=instance_type,
                name="idmap_{}_{}".format(self.safe_name(field), inner.name),
                init='new IdMapLoader({}, "{}", "{}")'.format(
                    inner.name, map_subject, map_predicate
                ),
                loader_type="Loader<{}>".format(instance_type),
            )
        )

    def typedsl_loader(self, inner: TypeDef, ref_scope: Union[int, None]) -> TypeDef:
        instance_type = inner.instance_type or "Object"
        return self.declare_type(
            TypeDef(
                instance_type=instance_type,
                name="typedsl_{}_{}".format(inner.name, ref_scope),
                init="new TypeDslLoader({}, {})".format(inner.name, ref_scope),
                loader_type="Loader<{}>".format(instance_type),
            )
        )

    def to_java(self, val: Any) -> Any:
        if val is True:
            return "true"
        elif val is None:
            return "null"
        elif val is False:
            return "false"
        return val

    def epilogue(self, root_loader: TypeDef) -> None:
        pd = "This project contains Java objects and utilities "
        pd = pd + ' auto-generated by <a href="https://github.com/'
        pd = pd + 'common-workflow-language/schema_salad">Schema Salad</a>'
        pd = pd + " for parsing documents corresponding to the "
        pd = pd + str(self.base_uri) + " schema."

        template_vars = dict(
            base_uri=self.base_uri,
            package=self.package,
            group_id=self.package,
            artifact_id=self.artifact,
            version="0.0.1-SNAPSHOT",
            project_name=self.package,
            project_description=pd,
            license_name="Apache License, Version 2.0",
            license_url="https://www.apache.org/licenses/LICENSE-2.0.txt",
        )  # type: MutableMapping[str, str]

        def template_from_resource(resource):
            # type: (str) -> string.Template
            template_str = pkg_resources.resource_string(
                __name__, "java/%s" % resource
            ).decode("utf-8")
            template = string.Template(template_str)
            return template

        def expand_resource_template_to(resource, path):
            # type: (str, str) -> None
            template = template_from_resource(resource)
            src = template.safe_substitute(template_vars)
            _ensure_directory_and_write(path, src)

        expand_resource_template_to("pom.xml", os.path.join(self.target_dir, "pom.xml"))
        expand_resource_template_to(
            "gitignore", os.path.join(self.target_dir, ".gitignore")
        )
        expand_resource_template_to(
            "package.html", os.path.join(self.main_src_dir, "package.html")
        )
        expand_resource_template_to(
            "overview.html",
            os.path.join(self.target_dir, "src", "main", "javadoc", "overview.html"),
        )
        expand_resource_template_to(
            "MANIFEST.MF",
            os.path.join(
                self.target_dir, "src", "main", "resources", "META-INF", "MANIFEST.MF"
            ),
        )
        expand_resource_template_to(
            "README.md", os.path.join(self.target_dir, "README.md"),
        )

        vocab = ""
        rvocab = ""
        for k in sorted(self.vocab.keys()):
            vocab += """    vocab.put("{}", "{}");\n""".format(k, self.vocab[k])
            rvocab += """    rvocab.put("{}", "{}");\n""".format(self.vocab[k], k)

        loader_instances = ""
        for _, collected_type in self.collected_types.items():
            loader_instances += "  public static {} {} = {};\n".format(
                collected_type.loader_type, collected_type.name, collected_type.init
            )

        example_tests = ""
        if self.examples:
            _safe_makedirs(self.test_resources_dir)
            utils_resources = os.path.join(self.test_resources_dir, "utils")
            if os.path.exists(utils_resources):
                shutil.rmtree(utils_resources)
            shutil.copytree(self.examples, utils_resources)
            for example_name in os.listdir(self.examples):
                if example_name.startswith("valid"):
                    basename = os.path.basename(example_name).split(".", 1)[0]
                    example_tests += """
  @org.junit.Test
  public void test{basename}ByString() throws Exception {{
    String path = java.nio.file.Paths.get(".").toAbsolutePath().normalize().toString();
    String baseUri = Uris.fileUri(path) + "/";
    java.net.URL url = getClass().getResource("{example_name}");
    java.nio.file.Path resPath = java.nio.file.Paths.get(url.toURI());
    String yaml = new String(java.nio.file.Files.readAllBytes(resPath), "UTF8");
    RootLoader.loadDocument(yaml, baseUri);
  }}

  @org.junit.Test
  public void test{basename}ByPath() throws Exception {{
    java.net.URL url = getClass().getResource("{example_name}");
    java.nio.file.Path resPath = java.nio.file.Paths.get(url.toURI());
    RootLoader.loadDocument(resPath);
  }}

  @org.junit.Test
  public void test{basename}ByMap() throws Exception {{
    java.net.URL url = getClass().getResource("{example_name}");
    java.nio.file.Path resPath = java.nio.file.Paths.get(url.toURI());
    String yaml = new String(java.nio.file.Files.readAllBytes(resPath), "UTF8");
    java.util.Map<String, Object> doc;
    doc = (java.util.Map<String, Object>) YamlUtils.mapFromString(yaml);
    RootLoader.loadDocument(doc);
  }}""".format(
                        basename=basename, example_name=example_name,
                    )

        template_args = dict(
            package=self.package,
            vocab=vocab,
            rvocab=rvocab,
            loader_instances=loader_instances,
            root_loader_name=root_loader.name,
            root_loader_instance_type=root_loader.instance_type or "Object",
            example_tests=example_tests,
        )  # type: MutableMapping[str, str]

        util_src_dirs = {
            "main_utils": self.main_src_dir,
            "test_utils": self.test_src_dir,
        }
        for (util_src, util_target) in util_src_dirs.items():
            for util in pkg_resources.resource_listdir(__name__, "java/%s" % util_src):
                src_path = os.path.join(util_target, "utils", util)
                src_template = template_from_resource(os.path.join(util_src, util))
                src = src_template.safe_substitute(template_args)
                _ensure_directory_and_write(src_path, src)
