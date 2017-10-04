import collections
from six.moves import urllib

def shortname(inputid):
    # type: (Text) -> Text
    d = urllib.parse.urlparse(inputid)
    if d.fragment:
        return d.fragment.split(u"/")[-1]
    else:
        return d.path.split(u"/")[-1]

class TypeDef(object):
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

    def end_class(self, classname):
        raise NotImplementedError()

    def type_loader(self, t):
        raise NotImplementedError()

    def declare_field(self, name, types, doc):
        raise NotImplementedError()

    def declare_id_field(self, name, types, doc):
        raise NotImplementedError()

    def add_vocab(self, name, uri):
        self.vocab[name] = uri

    def uri_loader(self, inner, scoped_id, vocab_term, refScope):
        raise NotImplementedError()

    def idmap_loader(self, field, inner, mapSubject, mapPredicate):
        raise NotImplementedError()

    def typedsl_loader(self, inner, refScope):
        raise NotImplementedError()

    def epilogue(self, rootLoader):
        raise NotImplementedError()

    def declare_type(self, t):
        if t not in self.collected_types:
            self.collected_types[t.name] = t
        return t
