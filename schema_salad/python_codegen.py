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
from typing import Any, Dict, IO, List, Optional, Text, Union, List

class PythonCodeGen(CodeGenBase):
    def __init__(self, out):
        # type: (IO[str]) -> None
        super(PythonCodeGen, self).__init__()
        self.out = out
        self.current_class_is_abstract = False

    def safe_name(self, n):
        # type: (Text) -> Text

        avn = schema.avro_name(n)
        if avn in ("class", "in"):
            # reserved words
            avn = avn+"_"
        return avn


    def prologue(self):
        # type: () -> None

        self.out.write("""#
# This file was autogenerated using schema-salad-tool --codegen=python
#
""")

        rs = resource_stream(__name__, 'sourceline.py')
        self.out.write(rs.read().decode("UTF-8"))
        rs.close()
        self.out.write("\n\n")

        rs = resource_stream(__name__, 'python_codegen_support.py')
        self.out.write(rs.read().decode("UTF-8"))
        rs.close()
        self.out.write("\n\n")

        for p in six.itervalues(self.prims):
            self.declare_type(p)


    def begin_class(self, classname, extends, doc, abstract, field_names, idfield):
        # type: (Text, List[Text], Text, bool, List[Text], Text) -> None
        classname = self.safe_name(classname)

        if extends:
            ext = ", ".join(self.safe_name(e) for e in extends)
        else:
            ext = "Savable"

        self.out.write("class %s(%s):\n" % (self.safe_name(classname), ext))

        if doc:
            self.out.write('    """\n')
            self.out.write(str(doc))
            self.out.write('\n    """\n')

        self.serializer = cStringIO()

        self.current_class_is_abstract = abstract
        if self.current_class_is_abstract:
            self.out.write("    pass\n\n")
            return

        self.out.write(
            """    def __init__(self, _doc, baseuri, loadingOptions, docRoot=None):
        doc = copy.copy(_doc)
        if hasattr(_doc, 'lc'):
            doc.lc.data = _doc.lc.data
            doc.lc.filename = _doc.lc.filename
        errors = []
        self.loadingOptions = loadingOptions
""")

        self.idfield = idfield

        self.serializer.write("""
    def save(self, top=False, base_url=""):
        r = {}
        for ef in self.extension_fields:
            r[prefix_url(ef, self.loadingOptions.vocab)] = self.extension_fields[ef]
""")

        if "class" in field_names:
            self.out.write("""
        if doc.get('class') != '{class_}':
            raise ValidationException("Not a {class_}")

""".format(class_=classname))

            self.serializer.write("""
        r['class'] = '{class_}'
""".format(class_=classname))


    def end_class(self, classname, field_names):
        # type: (Text, List[Text]) -> None

        if self.current_class_is_abstract:
            return

        self.out.write("""
        self.extension_fields = {{}}
        for k in doc.keys():
            if k not in self.attrs:
                if ":" in k:
                    ex = expand_url(k, u"", loadingOptions, scoped_id=False, vocab_term=False)
                    self.extension_fields[ex] = doc[k]
                else:
                    errors.append(SourceLine(doc, k, str).makeError("invalid field `%s`, expected one of: {attrstr}" % (k)))
                    break

        if errors:
            raise ValidationException(\"Trying '{class_}'\\n\"+\"\\n\".join(errors))
""".
                       format(attrstr=", ".join(["`%s`" % f for f in field_names]),
                              class_=self.safe_name(classname)))

        self.serializer.write("""
        if top and self.loadingOptions.namespaces:
            r["$namespaces"] = self.loadingOptions.namespaces

""")

        self.serializer.write("        return r\n\n")

        self.serializer.write("    attrs = frozenset({attrs})\n".format(attrs=field_names))

        self.out.write(self.serializer.getvalue())
        self.out.write("\n\n")

    prims = {
        u"http://www.w3.org/2001/XMLSchema#string": TypeDef("strtype", "_PrimitiveLoader((str, six.text_type))"),
        u"http://www.w3.org/2001/XMLSchema#int": TypeDef("inttype", "_PrimitiveLoader(int)"),
        u"http://www.w3.org/2001/XMLSchema#long": TypeDef("inttype", "_PrimitiveLoader(int)"),
        u"http://www.w3.org/2001/XMLSchema#float": TypeDef("floattype", "_PrimitiveLoader(float)"),
        u"http://www.w3.org/2001/XMLSchema#double": TypeDef("floattype", "_PrimitiveLoader(float)"),
        u"http://www.w3.org/2001/XMLSchema#boolean": TypeDef("booltype", "_PrimitiveLoader(bool)"),
        u"https://w3id.org/cwl/salad#null": TypeDef("None_type", "_PrimitiveLoader(type(None))"),
        u"https://w3id.org/cwl/salad#Any": TypeDef("Any_type", "_AnyLoader()")
    }

    def type_loader(self, t):
        # type: (Union[List[Any], Dict[Text, Any], Text]) -> TypeDef

        if isinstance(t, list):
            sub = [self.type_loader(i) for i in t]
            return self.declare_type(TypeDef("union_of_%s" % "_or_".join(s.name for s in sub), "_UnionLoader((%s,))" % (", ".join(s.name for s in sub))))
        if isinstance(t, dict):
            if t["type"] in ("array", "https://w3id.org/cwl/salad#array"):
                i = self.type_loader(t["items"])
                return self.declare_type(TypeDef("array_of_%s" % i.name, "_ArrayLoader(%s)" % i.name))
            elif t["type"] in ("enum", "https://w3id.org/cwl/salad#enum"):
                for sym in t["symbols"]:
                    self.add_vocab(shortname(sym), sym)
                return self.declare_type(TypeDef(self.safe_name(t["name"])+"Loader", '_EnumLoader(("%s",))' % (
                    '", "'.join(self.safe_name(sym) for sym in t["symbols"]))))
            elif t["type"] in ("record", "https://w3id.org/cwl/salad#record"):
                return self.declare_type(TypeDef(self.safe_name(t["name"])+"Loader", "_RecordLoader(%s)" % self.safe_name(t["name"])))
            else:
                raise Exception("wft %s" % t["type"])
        if t in self.prims:
            return self.prims[t]
        return self.collected_types[self.safe_name(t)+"Loader"]

    def declare_id_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None

        if self.current_class_is_abstract:
            return

        self.declare_field(name, fieldtype, doc, True)

        if optional:
            opt = """self.{safename} = "_:" + str(uuid.uuid4())""".format(safename=self.safe_name(name))
        else:
            opt = """raise ValidationException("Missing {fieldname}")""".format(fieldname=shortname(name))

        self.out.write("""
        if self.{safename} is None:
            if docRoot is not None:
                self.{safename} = docRoot
            else:
                {opt}
        baseuri = self.{safename}
""".
                       format(safename=self.safe_name(name),
                              fieldname=shortname(name),
                              opt=opt))

        self.has_id = """
        base_url = base_url + "/" + self.{safename}
""".format(safename=self.safe_name(name))

    def declare_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None

        if self.current_class_is_abstract:
            return

        if shortname(name) == "class":
            return

        if optional:
            self.out.write("        if '{fieldname}' in doc:\n".format(fieldname=shortname(name)))
            spc = "    "
        else:
            spc = ""
        self.out.write("""{spc}        try:
{spc}            self.{safename} = load_field(doc.get('{fieldname}'), {fieldtype}, baseuri, loadingOptions)
{spc}        except ValidationException as e:
{spc}            errors.append(SourceLine(doc, '{fieldname}', str).makeError(\"the `{fieldname}` field is not valid because:\\n\"+str(e)))
""".
                       format(safename=self.safe_name(name),
                              fieldname=shortname(name),
                              fieldtype=fieldtype.name,
                              spc=spc))
        if optional:
            self.out.write("""        else:
            self.{safename} = None
""".format(safename=self.safe_name(name)))

        self.out.write("\n")

        baseurl = 'base_url'

        if fieldtype.is_uri:
            self.serializer.write("""
        if self.{safename} is not None:
            u = save_relative_uri(self.{safename}, {baseurl}, {scoped_id}, {ref_scope})
            if u:
                r['{fieldname}'] = u
""".
                                  format(safename=self.safe_name(name),
                                         fieldname=shortname(name),
                                         baseurl=baseurl,
                                         scoped_id=fieldtype.scoped_id,
                                         ref_scope=fieldtype.ref_scope))
        else:
            self.serializer.write("""
        if self.{safename} is not None:
            r['{fieldname}'] = save(self.{safename}, top=False, base_url={baseurl})
""".
                                  format(safename=self.safe_name(name),
                                         fieldname=shortname(name),
                                         baseurl=baseurl))

    def uri_loader(self, inner, scoped_id, vocab_term, refScope):
        # type: (TypeDef, bool, bool, Union[int, None]) -> TypeDef
        return self.declare_type(TypeDef("uri_%s_%s_%s_%s" % (inner.name, scoped_id, vocab_term, refScope),
                                         "_URILoader(%s, %s, %s, %s)" % (inner.name, scoped_id, vocab_term, refScope),
                                         is_uri=True, scoped_id=scoped_id, ref_scope=refScope))

    def idmap_loader(self, field, inner, mapSubject, mapPredicate):
        # type: (Text, TypeDef, Text, Union[Text, None]) -> TypeDef
        return self.declare_type(TypeDef("idmap_%s_%s" % (self.safe_name(field), inner.name),
                                         "_IdMapLoader(%s, '%s', '%s')" % (inner.name, mapSubject, mapPredicate)))

    def typedsl_loader(self, inner, refScope):
        # type: (TypeDef, Union[int, None]) -> TypeDef
        return self.declare_type(TypeDef("typedsl_%s_%s" % (inner.name, refScope),
                                         "_TypeDSLLoader(%s, %s)" % (inner.name, refScope)))

    def epilogue(self, rootLoader):
        # type: (TypeDef) -> None
        self.out.write("_vocab = {\n")
        for k in sorted(self.vocab.keys()):
            self.out.write("    \"%s\": \"%s\",\n" % (k, self.vocab[k]))
        self.out.write("}\n")

        self.out.write("_rvocab = {\n")
        for k in sorted(self.vocab.keys()):
            self.out.write("    \"%s\": \"%s\",\n" % (self.vocab[k], k))
        self.out.write("}\n\n")

        for k,tv in six.iteritems(self.collected_types):
            self.out.write("%s = %s\n" % (tv.name, tv.init))
        self.out.write("\n\n")

        self.out.write("""
def load_document(doc, baseuri=None, loadingOptions=None):
    if baseuri is None:
        baseuri = file_uri(os.getcwd()) + "/"
    if loadingOptions is None:
        loadingOptions = LoadingOptions()
    return _document_load(%s, doc, baseuri, loadingOptions)
""" % rootLoader.name)
