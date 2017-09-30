import json
import sys
import cStringIO
from six.moves import urllib
import collections
import logging

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
        self.out.write(
        """from types import NoneType

class ValidationException(Exception):
    pass

class Savable(object):
    pass

def try_load(doc, field, fieldtype, baseuri):
    val = None
    for f in field:
        if f in doc:
            val = doc[f]
            break

    if isinstance(fieldtype, _Loader):
        return fieldtype.load(val, baseuri)
    elif isinstance(val, fieldtype):
        return val
    raise ValidationException()

def save(val):
   if isinstance(val, Savable):
       return val.save()
   if isinstance(val, list):
       return [save(v) for v in val]
   return val

class _Loader(object):
   def load(self, doc, baseuri):
       pass

class _ArrayLoader(_Loader):
   def __init__(self, items):
       self.items = items

   def load(self, doc, baseuri):
       if not isinstance(doc, list):
           raise ValidationException()
       return [self.items.load(i, baseuri) for i in doc]


class _EnumLoader(_Loader):
   def __init__(self, symbols):
       self.symbols = symbols

   def load(self, doc, baseuri):
       if doc in self.symbols:
           return doc
       else:
           raise ValidationException()

class _RecordLoader(_Loader):
   def __init__(self, classtype):
       self.classtype = classtype

   def load(self, doc, baseuri):
       if not isinstance(dict, doc):
           raise ValidationException()
       return self.classtype(doc, baseuri)

class _UnionLoader(_Loader):
   def __init__(self, alternates):
       self.alternates = alternates

   def load(self, doc, baseuri):
        for t in self.alternates:
            if isinstance(t, _Loader):
                try:
                    return t.load(doc, baseuri)
                except ValidationException:
                    pass
            elif isinstance(doc, t):
                return doc
        raise ValidationException()

class IdentiferLoader(_Loader):
   def load(self, doc, baseuri):
       pass

class IdentityLoader(_Loader):
   def load(self, doc, baseuri):
       pass

class URILoader(_Loader):
   def load(self, doc, baseuri):
       pass

class TypeDSLLoader(_Loader):
   def load(self, doc, baseuri):
       pass

class IdMapLoader(_Loader):
   def load(self, doc, baseuri):
       pass

""")

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

        self.out.write("    def __init__(self, doc, baseuri):\n")

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
        self.out.write("        self.%s = try_load(doc, ('%s', '%s'), %s, baseuri)\n" % (self.safe_name(name), shortname(name), name, fieldtype.name))
        self.serializer.write("        if self.%s is not None:\n            r['%s'] = save(self.%s)\n" % (self.safe_name(name), shortname(name), self.safe_name(name)))


    def epilogue(self):
        self.out.write("\n\n")
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

            for f in rec["fields"]:
                cg.declare_field(f["name"], cg.type_loader(f["type"]), f.get("doc"))

            cg.end_class()

    cg.epilogue()
