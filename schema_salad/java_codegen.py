"""Work-in-progress Java code generator for a given schema salad definition."""
import os
from typing import MutableSequence

from six import string_types
from six.moves import cStringIO, urllib
from typing_extensions import Text  # pylint: disable=unused-import
# move to a regular typing import when Python 3.3-3.6 is no longer supported

from . import schema
from .codegen_base import CodeGenBase, TypeDef


class JavaCodeGen(CodeGenBase):
    def __init__(self, base):
        # type: (Text) -> None

        super(JavaCodeGen, self).__init__()
        sp = urllib.parse.urlsplit(base)
        self.package = ".".join(list(reversed(sp.netloc.split("."))) + sp.path.strip("/").split("/"))
        self.outdir = self.package.replace(".", "/")

    def prologue(self):  # type: () -> None
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    @staticmethod
    def safe_name(name):  # type: (Text) -> Text
        avn = schema.avro_name(name)
        if avn in ("class", "extends", "abstract"):
            # reserved words
            avn = avn+"_"
        return avn

    def interface_name(self, n):
        # type: (Text) -> Text
        return self.safe_name(n)

    def begin_class(self,
                    classname,    # type: Text
                    extends,      # type: MutableSequence[Text]
                    doc,          # type: Text
                    abstract,     # type: bool
                    field_names,  # type: MutableSequence[Text]
                    idfield       # type: Text
                   ):  # type: (...) -> None
        cls = self.interface_name(classname)
        self.current_class = cls
        self.current_class_is_abstract = abstract
        self.current_loader = cStringIO()
        self.current_fields = cStringIO()
        with open(os.path.join(self.outdir, "%s.java" % cls), "w") as f:
            if extends:
                ext = "extends " + ", ".join(self.interface_name(e) for e in extends)
            else:
                ext = ""
            f.write("""package {package};

public interface {cls} {ext} {{
""".
                    format(package=self.package,
                           cls=cls,
                           ext=ext))

        if self.current_class_is_abstract:
            return

        with open(os.path.join(self.outdir, "%sImpl.java" % cls), "w") as f:
            f.write("""package {package};

public class {cls}Impl implements {cls} {{
""".
                    format(package=self.package,
                           cls=cls,
                           ext=ext))
        self.current_loader.write("""
    void Load() {
""")

    def end_class(self, classname, field_names):
        with open(os.path.join(self.outdir, "%s.java" % self.current_class), "a") as f:
            f.write("""
}
""")
        if self.current_class_is_abstract:
            return

        self.current_loader.write("""
    }
""")

        with open(os.path.join(self.outdir, "%sImpl.java" % self.current_class), "a") as f:
            f.write(self.current_fields.getvalue())
            f.write(self.current_loader.getvalue())
            f.write("""
}
""")

    prims = {
        u"http://www.w3.org/2001/XMLSchema#string": TypeDef("String", "Support.StringLoader()"),
        u"http://www.w3.org/2001/XMLSchema#int": TypeDef("Integer", "Support.IntLoader()"),
        u"http://www.w3.org/2001/XMLSchema#long": TypeDef("Long", "Support.LongLoader()"),
        u"http://www.w3.org/2001/XMLSchema#float": TypeDef("Float", "Support.FloatLoader()"),
        u"http://www.w3.org/2001/XMLSchema#double": TypeDef("Double", "Support.DoubleLoader()"),
        u"http://www.w3.org/2001/XMLSchema#boolean": TypeDef("Boolean", "Support.BoolLoader()"),
        u"https://w3id.org/cwl/salad#null": TypeDef("null_type", "Support.NullLoader()"),
        u"https://w3id.org/cwl/salad#Any": TypeDef("Any_type", "Support.AnyLoader()")
    }

    def type_loader(self, type_declaration):
        if isinstance(type_declaration, MutableSequence) and len(type_declaration) == 2:
            if type_declaration[0] == "https://w3id.org/cwl/salad#null":
                type_declaration = type_declaration[1]
        if isinstance(type_declaration, string_types):
            if type_declaration in self.prims:
                return self.prims[type_declaration]
        return TypeDef("Object", "")

    def declare_field(self, name, fieldtype, doc, optional):
        fieldname = self.safe_name(name)
        with open(os.path.join(self.outdir, "%s.java" % self.current_class), "a") as f:
            f.write("""
    {type} get{capfieldname}();
""".
                    format(fieldname=fieldname,
                           capfieldname=fieldname[0].upper() + fieldname[1:],
                           type=fieldtype.name))

        if self.current_class_is_abstract:
            return

        self.current_fields.write("""
    private {type} {fieldname};
    public {type} get{capfieldname}() {{
        return this.{fieldname};
    }}
""".
                    format(fieldname=fieldname,
                           capfieldname=fieldname[0].upper() + fieldname[1:],
                           type=fieldtype.name))

        self.current_loader.write("""
        this.{fieldname} = null; // TODO: loaders
        """.
                                  format(fieldname=fieldname))


    def declare_id_field(self, name, fieldtype, doc, optional):
        pass

    def uri_loader(self, inner, scoped_id, vocab_term, ref_scope):
        return inner

    def idmap_loader(self, field, inner, map_subject, map_predicate):
        return inner

    def typedsl_loader(self, inner, ref_scope):
        return inner

    def epilogue(self, root_loader):

        pass
