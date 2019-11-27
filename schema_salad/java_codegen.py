"""Work-in-progress Java code generator for a given schema salad definition."""
import os
import pkg_resources
import string
from typing import Any, Dict, List, MutableMapping, MutableSequence, Union

from six import iteritems, itervalues, string_types
from six.moves import cStringIO, urllib
from typing_extensions import Text  # pylint: disable=unused-import

from . import schema
from .codegen_base import CodeGenBase, TypeDef
from .schema import shortname

# move to a regular typing import when Python 3.3-3.6 is no longer supported
POM_SRC_TEMPLATE = string.Template(pkg_resources.resource_string(__name__, "java/pom.xml"))


def _ensure_directory_and_write(path, contents):
    # type: (str, Text) -> None
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, "w") as f:
        f.write(contents)


class JavaTypeDef(TypeDef):  # pylint: disable=too-few-public-methods
    """Extend TypeDef with Java concepts."""

    __slots__ = ["name", "init", "is_uri", "scoped_id", "ref_scope", "loader_type", "instance_type"]

    def __init__(
        self,  # pylint: disable=too-many-arguments
        name,  # type: Text
        init,  # type: Text
        is_uri=False,  # type: bool
        scoped_id=False,  # type: bool
        ref_scope=0,  # type: Optional[int]
        loader_type="Loader<Object>",  # type: Text
        instance_type="Object",  # type: Text
    ):  # type: (...) -> None
        super(JavaTypeDef, self).__init__(name, init, is_uri, scoped_id, ref_scope)
        self.loader_type = loader_type
        self.instance_type = instance_type


class JavaCodeGen(CodeGenBase):
    def __init__(self, base, target):
        # type: (Text, Optional[str]) -> None

        super(JavaCodeGen, self).__init__()
        sp = urllib.parse.urlsplit(base)
        self.package = ".".join(
            list(reversed(sp.netloc.split("."))) + sp.path.strip("/").split("/")
        )
        self.artifact = self.package.split(".")[-1]
        target = target or "."
        self.target_dir = target
        rel_package_dir = self.package.replace(".", "/")
        self.main_src_dir = os.path.join(self.target_dir, "src", "main", "java", rel_package_dir)
        self.test_src_dir = os.path.join(self.target_dir, "src", "test", "java", rel_package_dir)

    def prologue(self):  # type: () -> None
        for src_dir in [self.main_src_dir, self.test_src_dir]:
            if not os.path.exists(src_dir):
                os.makedirs(src_dir)

        for primative in itervalues(self.prims):
            self.declare_type(primative)

    @staticmethod
    def property_name(name):  # type: (Text) -> Text
        avn = schema.avro_name(name)
        return avn

    @staticmethod
    def safe_name(name):  # type: (Text) -> Text
        avn = JavaCodeGen.property_name(name)
        if avn in ("class", "extends", "abstract", "default"):
            # reserved words
            avn = avn + "_"
        return avn

    def interface_name(self, n):
        # type: (Text) -> Text
        return self.safe_name(n)

    def begin_class(
        self,
        classname,  # type: Text
        extends,  # type: MutableSequence[Text]
        doc,  # type: Text
        abstract,  # type: bool
        field_names,  # type: MutableSequence[Text]
        idfield,  # type: Text
    ):  # type: (...) -> None
        cls = self.interface_name(classname)
        self.current_class = cls
        self.current_class_is_abstract = abstract
        self.current_loader = cStringIO()
        self.current_fieldtypes = {}
        self.current_fields = cStringIO()
        with open(os.path.join(self.main_src_dir, "{}.java".format(cls)), "w") as f:

            if extends:
                ext = "extends " + ", ".join(self.interface_name(e) for e in extends) + ", Savable"
            else:
                ext = "extends Savable"
            f.write(
                """package {package};

import java.util.List;

import {package}.utils.Savable;

public interface {cls} {ext} {{
""".format(
                    package=self.package, cls=cls, ext=ext
                )
            )

        if self.current_class_is_abstract:
            return

        with open(os.path.join(self.main_src_dir, "{}Impl.java".format(cls)), "w") as f:
            f.write(
                """package {package};

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.UUID;
import {package}.utils.LoaderInstances;
import {package}.utils.LoadingOptions;
import {package}.utils.LoadingOptionsBuilder;
import {package}.utils.ValidationException;

public class {cls}Impl implements {cls} {{
    private LoadingOptions loadingOptions_ = new LoadingOptionsBuilder().build();
    private Map<String, Object> extensionFields_ = new HashMap<String, Object>();
""".format(
                    package=self.package, cls=cls, ext=ext
                )
            )
        self.current_loader.write(
            """
    public static {cls}Impl fromDoc(final Object __doc_, final String __baseUri_, LoadingOptions __loadingOptions, final String __docRoot_) {{
        // Prefix plumbing variables with '__' to reduce likelihood of collision with
        // generated names.
        String __baseUri = __baseUri_;
        String __docRoot = __docRoot_;
        if(!(__doc_ instanceof Map)) {{
            throw new ValidationException("fromDoc called on non-map");
        }}
        final Map<String, Object> __doc = (Map<String, Object>) __doc_;
        final {cls}Impl __bean = new {cls}Impl();
        if(__loadingOptions != null) {{
            __bean.loadingOptions_ = __loadingOptions;
        }}
""".format(cls=cls)
        )

    def end_class(self, classname, field_names):
        # type: (Text, List[Text]) -> None
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
        for fieldname in field_names:
            fieldtype = self.current_fieldtypes[fieldname]
            self.current_loader.write("""        __bean.{safename} = ({type}) {safename};
""".format(safename=self.safe_name(fieldname), type=fieldtype.instance_type))

        self.current_loader.write(
            """        
        return __bean;
    }
"""
        )

        with open(
            os.path.join(self.main_src_dir, "{}Impl.java".format(self.current_class)), "a"
        ) as f:
            f.write(self.current_fields.getvalue())
            f.write(self.current_loader.getvalue())
            f.write(
                """
}
"""
            )

    prims = {
        u"http://www.w3.org/2001/XMLSchema#string": JavaTypeDef(
            instance_type="String", init="new PrimitiveLoader<String>(String.class)", name="StringLoaderInstance", loader_type="Loader<String>"
        ),
        u"http://www.w3.org/2001/XMLSchema#int": JavaTypeDef(
            instance_type="Integer", init="new PrimitiveLoader<Integer>(Integer.class)", name="IntegerLoaderInstance", loader_type="Loader<Integer>"
        ),
        u"http://www.w3.org/2001/XMLSchema#long": JavaTypeDef(
            instance_type="Long", name="LongLoaderInstance", loader_type="Loader<Long>", init="new PrimitiveLoader<Long>(Long.class)"
        ),
        u"http://www.w3.org/2001/XMLSchema#float": JavaTypeDef(
            instance_type="Float", name="FloatLoaderInstance", loader_type="Loader<Float>", init="new PrimitiveLoader<Float>(Float.class)"
        ),
        u"http://www.w3.org/2001/XMLSchema#double": JavaTypeDef(
            instance_type="Double", name="DoubleLoaderInstance", loader_type="Loader<Double>", init="new PrimitiveLoader<Double>(Double.class)"
        ),
        u"http://www.w3.org/2001/XMLSchema#boolean": JavaTypeDef(
            instance_type="Boolean", name="BooleanLoaderInstance", loader_type="Loader<Boolean>", init="new PrimitiveLoader<Boolean>(Boolean.class)"
        ),
        u"https://w3id.org/cwl/salad#null": JavaTypeDef(
            instance_type="Object", name="NullLoaderInstance", loader_type="Loader<Object>", init="new NullLoader()"
        ),
        u"https://w3id.org/cwl/salad#Any": JavaTypeDef(instance_type="Object", name="AnyLoaderInstance", init="new AnyLoader()", loader_type="Loader<Object>"),
    }

    def type_loader(self, type_declaration):
        # type: (Union[List[Any], Dict[Text, Any], Text]) -> JavaTypeDef
        if isinstance(type_declaration, MutableSequence):
            sub = [self.type_loader(i) for i in type_declaration]
            return self.declare_type(
                JavaTypeDef(
                    instance_type="Object",
                    init="new UnionLoader(new Loader[] {{ {} }})".format(", ".join(s.name for s in sub)),
                    name="union_of_{}".format("_or_".join(s.name for s in sub)),
                    loader_type="Loader<Object>"
                )
            )
        if isinstance(type_declaration, MutableMapping):
            if type_declaration["type"] in (
                "array",
                "https://w3id.org/cwl/salad#array",
            ):
                i = self.type_loader(type_declaration["items"])
                return self.declare_type(
                    JavaTypeDef(
                        # instance_type="List<{}>".format(i.instance_type),  # special doesn't work out, gotta actual use extends and such.
                        instance_type="List<Object>",
                        name="array_of_{}".format(i.name),
                        init="new ArrayLoader({})".format(i.name),
                        loader_type="Loader<List<Object>>"
                    )
                )
            if type_declaration["type"] in ("enum", "https://w3id.org/cwl/salad#enum"):
                for sym in type_declaration["symbols"]:
                    self.add_vocab(shortname(sym), sym)
                return self.declare_type(
                    JavaTypeDef(
                        instance_type="String",
                        name=self.safe_name(type_declaration["name"]) + "Loader",
                        loader_type="Loader<String>",
                        init='new EnumLoader(new String[] {{ "{}" }})'.format(
                            '", "'.join(
                                self.safe_name(sym)
                                for sym in type_declaration["symbols"]
                            )
                        ),
                    )
                )
            if type_declaration["type"] in (
                "record",
                "https://w3id.org/cwl/salad#record",
            ):
                fqclass = "{}.{}".format(self.package, self.safe_name(type_declaration["name"]))
                return self.declare_type(
                    JavaTypeDef(
                        instance_type=self.safe_name(type_declaration["name"]),
                        name=self.safe_name(type_declaration["name"]) + "Loader",
                        init="new RecordLoader<{}>({}.class)".format(
                            fqclass,
                            fqclass
                        ),
                        loader_type="Loader<{}>".format(fqclass)
                    )
                )
            raise SchemaException("wft {}".format(type_declaration["type"]))
        if type_declaration in self.prims:
            return self.prims[type_declaration]
        return self.collected_types[self.safe_name(type_declaration) + "Loader"]

    def declare_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None
        fieldname = name
        property_name = self.property_name(fieldname)
        cap_case_property_name = property_name[0].upper() + property_name[1:]
        if cap_case_property_name == "Class":
            cap_case_property_name = "Class_"

        safename = self.safe_name(fieldname)
        self.current_fieldtypes[property_name] = fieldtype
        with open(
            os.path.join(self.main_src_dir, "{}.java".format(self.current_class)), "a"
        ) as f:
            f.write(
                """
    {type} get{capfieldname}();
""".format(
                    fieldname=fieldname,
                    capfieldname=cap_case_property_name,
                    type=fieldtype.instance_type,
                )
            )

        if self.current_class_is_abstract:
            return

        self.current_fields.write(
            """
    private {type} {safename};
    public {type} get{capfieldname}() {{
        return this.{safename};
    }}
""".format(
                safename=safename,
                capfieldname=cap_case_property_name,
                type=fieldtype.instance_type,
            )
        )

        self.current_loader.write("""    {type} {safename};
""".format(type=fieldtype.instance_type, safename=safename))
        if optional:
            self.current_loader.write("""
        if(__doc.containsKey("{fieldname}")) {{
""".format(fieldname=fieldname))
            spc = "    "
        else:
            spc = ""

        self.current_loader.write(
            """{spc}        {safename} = LoaderInstances.{fieldtype}.loadField(__doc.get("{fieldname}"), __baseUri, __loadingOptions);
""".format(
                fieldtype=fieldtype.name,
                safename=safename,
                fieldname=name,
                spc=spc
            )
        )

        if optional:
            self.current_loader.write("""
        }} else {{
            {safename} = null;
        }}
""".format(safename=safename))

    def declare_id_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None
        if self.current_class_is_abstract:
            return

        self.declare_field(name, fieldtype, doc, True)

        if optional:
            opt = """{safename} = "_:" + UUID.randomUUID().toString();""".format(
                safename=self.safe_name(name)
            )
        else:
            opt = """throw new ValidationException("Missing {fieldname}");""".format(
                fieldname=shortname(name)
            )

        self.current_loader.write(
            """
        if({safename} == null) {{
            if(__docRoot != null) {{
                {safename} = __docRoot;
            }} else {{
                {opt}
            }}
        }}
        __baseUri = (String) {safename};
""".format(
                safename=self.safe_name(name), fieldname=shortname(name), opt=opt
            )
        )

    def uri_loader(self, inner, scoped_id, vocab_term, ref_scope):
        # type: (TypeDef, bool, bool, Union[int, None]) -> TypeDef
        return inner

    def idmap_loader(self, field, inner, map_subject, map_predicate):
        # type: (Text, TypeDef, Text, Union[Text, None]) -> TypeDef
        return inner

    def typedsl_loader(self, inner, ref_scope):
        # type: (TypeDef, Union[int, None]) -> TypeDef
        return inner

    def epilogue(self, root_loader):  # type: (TypeDef) -> None
        pom_src = POM_SRC_TEMPLATE.safe_substitute(
            group_id=self.package,
            artifact_id=self.artifact,
            version="0.0.1-SNAPSHOT",
        )
        with open(os.path.join(self.target_dir, "pom.xml"), "w") as f:
            f.write(pom_src)

        vocab = "";
        rvocab = "";
        for k in sorted(self.vocab.keys()):
            vocab += '''        vocab.put("{}", "{}");\n'''.format(k, self.vocab[k])
            rvocab += '''        rvocab.put("{}", "{}");\n'''.format(self.vocab[k], k)

        loader_instances = ""
        for _, collected_type in iteritems(self.collected_types):
            loader_instances += "    public static {} {} = {};\n".format(collected_type.loader_type, collected_type.name, collected_type.init)

        template_args = dict(
            package=self.package,
            vocab=vocab,
            rvocab=rvocab,
            loader_instances=loader_instances,
            root_loader_name=root_loader.name,
            root_loader_instance_type=root_loader.instance_type,
        )

        util_src_dirs = {
            "main_utils": self.main_src_dir,
            "test_utils": self.test_src_dir,
        }
        for (util_src, util_target) in util_src_dirs.items():
            for util in pkg_resources.resource_listdir(__name__, "java/%s" % util_src):
                src_path = os.path.join(util_target, "utils", util)
                src_template = string.Template(pkg_resources.resource_string(__name__, "java/%s/%s" % (util_src, util)))
                src = src_template.safe_substitute(**template_args)
                _ensure_directory_and_write(src_path, src)

        pass
