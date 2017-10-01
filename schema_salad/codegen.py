import json
import sys
import cStringIO
from six.moves import urllib
import collections
import logging
from pkg_resources import resource_stream

from .utils import aslist, flatten

from . import schema

def shortname(inputid):
    # type: (Text) -> Text
    d = urllib.parse.urlparse(inputid)
    if d.fragment:
        return d.fragment.split(u"/")[-1]
    else:
        return d.path.split(u"/")[-1]

class SimpleType(object):
    def __init__(self, name):
        self.name = name

class CompoundType(object):
    def __init__(self, name, init):
        self.name = name
        self.init = init


class CodeGenBase(object):
    def __init__(self):
        self.collected_types = collections.OrderedDict()
        self.vocab = {}

    def prologue(self):
        raise NotImplementedError()

    def safe_name(self, n):
        return schema.avro_name(n)

    def begin_class(self, classname, extends, doc):
        raise NotImplementedError()

    def end_class(self):
        raise NotImplementedError()

    def type_loader(self, t):
        raise NotImplementedError()

    def declare_field(self, name, types, doc):
        raise NotImplementedError()

    def add_vocab(self, name, uri):
        self.vocab[name] = uri

    def epilogue(self):
        raise NotImplementedError()

    def declare_type(self, t):
        if t not in self.collected_types:
            self.collected_types[t.name] = t
        return t


class PythonCodeGen(CodeGenBase):
    def __init__(self, out):
        super(PythonCodeGen, self).__init__()
        self.out = out

    def prologue(self):
        rs = resource_stream(__name__, 'python_codegen_support.py')
        self.out.write(rs.read())
        rs.close()

    def begin_class(self, classname, extends, doc):
        classname = self.safe_name(classname)

        if extends:
            ext = ", ".join(self.safe_name(e) for e in extends)
        else:
            ext = "Savable"

        self.out.write("class %s(%s):\n" % (self.safe_name(classname), ext))

        if doc:
            self.out.write('    """\n')
            self.out.write(doc)
            self.out.write('\n    """\n')

        self.out.write(
            """    def __init__(self, doc, baseuri, loadingOptions):
           doc = {expand_url(d, u"", loadingOptions, scoped_id=False, vocab_term=True): v for d,v in doc.items()}
""")

        self.serializer = cStringIO.StringIO()
        self.serializer.write("""
    def save(self):
        r = {}
""")

    def end_class(self):
        self.serializer.write("        return r\n")
        self.out.write(self.serializer.getvalue())
        self.out.write("\n\n")

    prims = {
        "http://www.w3.org/2001/XMLSchema#string": SimpleType("str"),
        "http://www.w3.org/2001/XMLSchema#int": SimpleType("int"),
        "http://www.w3.org/2001/XMLSchema#boolean": SimpleType("bool"),
        "https://w3id.org/cwl/salad#null": SimpleType("NoneType")
    }

    def type_loader(self, t):
        if isinstance(t, list):
            sub = [self.type_loader(i) for i in t]
            return self.declare_type(CompoundType("union_of_%s" % "_or_".join(s.name for s in sub), "_UnionLoader((%s))" % (", ".join(s.name for s in sub))))
        if isinstance(t, dict):
            if t["type"] == "https://w3id.org/cwl/salad#array":
                i = self.type_loader(t["items"])
                return self.declare_type(CompoundType("array_of_%s" % i.name, "_ArrayLoader(%s)" % i.name))
            elif t["type"] in ("enum", "https://w3id.org/cwl/salad#enum"):
                return self.declare_type(CompoundType(self.safe_name(t["name"])+"Loader", '_EnumLoader(("%s",))' % (
                    '", "'.join(self.safe_name(sym) for sym in t["symbols"]))))
            elif t["type"] in ("record", "https://w3id.org/cwl/salad#record"):
                return self.declare_type(CompoundType(self.safe_name(t["name"])+"Loader", "_RecordLoader(%s)" % self.safe_name(t["name"])))
            else:
                raise Exception("wft %s" % t["type"])
        if t in self.prims:
            return self.prims[t]
        return self.collected_types[self.safe_name(t)+"Loader"]

    def declare_field(self, name, fieldtype, doc):
        self.out.write("           self.%s = try_load(doc, '%s', %s, baseuri, loadingOptions)\n" % (self.safe_name(name), shortname(name), fieldtype.name if fieldtype.name else fieldtype.init))
        self.serializer.write("        if self.%s is not None:\n            r['%s'] = save(self.%s)\n" % (self.safe_name(name), shortname(name), self.safe_name(name)))

    def uri_loader(self, inner, scoped_id, vocab_term, refScope):
        return self.declare_type(CompoundType("uri_%s_%s_%s_%s" % (inner.name, scoped_id, vocab_term, refScope) ,
                                              "_URILoader(%s, %s, %s, %s)" % (inner.name, scoped_id, vocab_term, refScope)))

    def idmap_loader(self, field, inner, mapSubject, mapPredicate):
        return self.declare_type(CompoundType("idmap_%s_%s" % (self.safe_name(field), inner.name),
                                              "_IdMapLoader(%s, '%s', '%s')" % (inner.name, mapSubject, mapPredicate)))

    def epilogue(self):
        self.out.write("_vocab = {\n")
        for k,v in self.vocab.iteritems():
            self.out.write("    \"%s\": \"%s\",\n" % (k, v))
        self.out.write("}\n")

        self.out.write("_rvocab = {\n")
        for k,v in self.vocab.iteritems():
            self.out.write("    \"%s\": \"%s\",\n" % (v, k))
        self.out.write("}\n\n")

        for k,v in self.collected_types.iteritems():
            if isinstance(v, CompoundType):
                self.out.write("%s = %s\n" % (v.name, v.init))
        self.out.write("\n\n")


class GoCodeGen(object):
    pass


def codegen(lang,      # type: str
            i,         # type: List[Dict[Text, Any]]
            loader     # type: Loader
           ):
    j = schema.extend_and_specialize(i, loader)

    cg = PythonCodeGen(sys.stdout)

    cg.prologue()

    for rec in j:
        if rec["type"] in ("enum", "record"):
            cg.type_loader(rec)

    for rec in j:
        if rec["type"] == "record":
            cg.begin_class(rec["name"], aslist(rec.get("extends", [])), rec.get("doc"))
            cg.add_vocab(shortname(rec["name"]), rec["name"])

            for f in rec["fields"]:
                tl = cg.type_loader(f["type"])
                jld = f.get("jsonldPredicate")
                fieldpred = f["name"]
                if isinstance(jld, dict):
                    refScope = jld.get("refScope")
                    if jld.get("_type") == "@id":
                        tl = cg.uri_loader(tl, False, True, refScope)
                    mapSubject = jld.get("mapSubject")
                    if mapSubject:
                        tl = cg.idmap_loader(f["name"], tl, mapSubject, jld.get("mapPredicate"))
                    if "_id" in jld:
                        fieldpred = jld["_id"]
                if jld == "@id":
                    tl = cg.uri_loader(tl, True, True, None)

                cg.add_vocab(shortname(f["name"]), fieldpred)
                cg.declare_field(fieldpred, tl, f.get("doc"))

            cg.end_class()

    cg.epilogue()
