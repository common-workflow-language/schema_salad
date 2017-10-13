import json
import sys
import six
from six.moves import urllib, cStringIO
import collections
import logging
from pkg_resources import resource_stream
from .utils import aslist, flatten
from . import schema
from .codegen_base import TypeDef, CodeGenBase, shortname
import os

class JavaCodeGen(CodeGenBase):
    def __init__(self, base):
        super(JavaCodeGen, self).__init__()
        sp = urllib.parse.urlsplit(base)
        self.package = ".".join(list(reversed(sp.netloc.split("."))) + sp.path.strip("/").split("/"))
        self.outdir = self.package.replace(".", "/")

    def prologue(self):
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    def safe_name(self, n):
        avn = schema.avro_name(n)
        if avn in ("class", "extends", "abstract"):
            # reserved words
            avn = avn+"_"
        return avn

    def interface_name(self, n):
        return self.safe_name(n)

    def begin_class(self, classname, extends, doc, abstract):
        cls = self.interface_name(classname)
        self.current_class = cls
        self.current_class_is_abstract = abstract
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


    def end_class(self, classname):
        with open(os.path.join(self.outdir, "%s.java" % self.current_class), "a") as f:
            f.write("""
}
""")
        if self.current_class_is_abstract:
            return

        with open(os.path.join(self.outdir, "%sImpl.java" % self.current_class), "a") as f:
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

    def type_loader(self, t):
        if isinstance(t, list) and len(t) == 2:
            if t[0] == "https://w3id.org/cwl/salad#null":
                t = t[1]
        if isinstance(t, basestring):
            if t in self.prims:
                return self.prims[t]
        return TypeDef("Object", "")

    def declare_field(self, name, typedef, doc, optional):
        fieldname = self.safe_name(name)
        with open(os.path.join(self.outdir, "%s.java" % self.current_class), "a") as f:
            f.write("""
    {type} get{capfieldname}();
""".
                    format(fieldname=fieldname,
                           capfieldname=fieldname[0].upper() + fieldname[1:],
                           type=typedef.name))

        if self.current_class_is_abstract:
            return

        with open(os.path.join(self.outdir, "%sImpl.java" % self.current_class), "a") as f:
            f.write("""
    private {type} {fieldname};
    public {type} get{capfieldname}() {{
        return this.{fieldname};
    }}
""".
                    format(fieldname=fieldname,
                           capfieldname=fieldname[0].upper() + fieldname[1:],
                           type=typedef.name))


    def declare_id_field(self, name, typedef, doc):
        pass

    def uri_loader(self, inner, scoped_id, vocab_term, refScope):
        return inner

    def idmap_loader(self, field, inner, mapSubject, mapPredicate):
        return inner

    def typedsl_loader(self, inner, refScope):
        return inner

    def epilogue(self, rootLoader):
        pass
