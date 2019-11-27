"""Work-in-progress Java code generator for a given schema salad definition."""
import os
import pkg_resources
import string
from typing import Any, Dict, List, MutableSequence, Union

from six import string_types
from six.moves import cStringIO, urllib
from typing_extensions import Text  # pylint: disable=unused-import

from . import schema
from .codegen_base import CodeGenBase, TypeDef

# move to a regular typing import when Python 3.3-3.6 is no longer supported
POM_SRC_TEMPLATE = string.Template(pkg_resources.resource_string(__name__, "java/pom.xml"))


def _ensure_directory_and_write(path, contents):
    # type: (str, Text) -> None
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, "w") as f:
        f.write(contents)


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

    @staticmethod
    def safe_name(name):  # type: (Text) -> Text
        avn = schema.avro_name(name)
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
        self.current_fields = cStringIO()
        with open(os.path.join(self.main_src_dir, "{}.java".format(cls)), "w") as f:
            if extends:
                ext = "extends " + ", ".join(self.interface_name(e) for e in extends)
            else:
                ext = ""
            f.write(
                """package {package};

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

public class {cls}Impl implements {cls} {{
""".format(
                    package=self.package, cls=cls, ext=ext
                )
            )
        self.current_loader.write(
            """
    void Load() {
"""
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

        self.current_loader.write(
            """
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
        u"http://www.w3.org/2001/XMLSchema#string": TypeDef(
            "String", "Support.StringLoader()"
        ),
        u"http://www.w3.org/2001/XMLSchema#int": TypeDef(
            "Integer", "Support.IntLoader()"
        ),
        u"http://www.w3.org/2001/XMLSchema#long": TypeDef(
            "Long", "Support.LongLoader()"
        ),
        u"http://www.w3.org/2001/XMLSchema#float": TypeDef(
            "Float", "Support.FloatLoader()"
        ),
        u"http://www.w3.org/2001/XMLSchema#double": TypeDef(
            "Double", "Support.DoubleLoader()"
        ),
        u"http://www.w3.org/2001/XMLSchema#boolean": TypeDef(
            "Boolean", "Support.BoolLoader()"
        ),
        u"https://w3id.org/cwl/salad#null": TypeDef(
            "null_type", "Support.NullLoader()"
        ),
        u"https://w3id.org/cwl/salad#Any": TypeDef("Object", "Support.AnyLoader()"),
    }

    def type_loader(self, type_declaration):
        # type: (Union[List[Any], Dict[Text, Any]]) -> TypeDef
        if isinstance(type_declaration, MutableSequence) and len(type_declaration) == 2:
            if type_declaration[0] == "https://w3id.org/cwl/salad#null":
                type_declaration = type_declaration[1]
        if isinstance(type_declaration, string_types):
            if type_declaration in self.prims:
                return self.prims[type_declaration]
        return TypeDef("Object", "")

    def declare_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None
        fieldname = self.safe_name(name)
        with open(
            os.path.join(self.main_src_dir, "{}.java".format(self.current_class)), "a"
        ) as f:
            f.write(
                """
    {type} get{capfieldname}();
""".format(
                    fieldname=fieldname,
                    capfieldname=fieldname[0].upper() + fieldname[1:],
                    type=fieldtype.name,
                )
            )

        if self.current_class_is_abstract:
            return

        self.current_fields.write(
            """
    private {type} {fieldname};
    public {type} get{capfieldname}() {{
        return this.{fieldname};
    }}
""".format(
                fieldname=fieldname,
                capfieldname=fieldname[0].upper() + fieldname[1:],
                type=fieldtype.name,
            )
        )

        self.current_loader.write(
            """
        this.{fieldname} = null; // TODO: loaders
        """.format(
                fieldname=fieldname
            )
        )

    def declare_id_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None
        pass

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

        template_args = dict(
            package=self.package,
            vocab=vocab,
            rvocab=rvocab,
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
