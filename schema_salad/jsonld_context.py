import collections
import shutil
import json
import ruamel.yaml as yaml
try:
        from ruamel.yaml import CSafeLoader as SafeLoader
except ImportError:
        from ruamel.yaml import SafeLoader
import os
import subprocess
import copy
import pprint
import re
import sys
import rdflib
from rdflib import Graph, URIRef
import rdflib.namespace
from rdflib.namespace import RDF, RDFS
import urlparse
import logging
from .aslist import aslist
from typing import Any, Dict, Iterable, Tuple, Union
from .ref_resolver import Loader

_logger = logging.getLogger("salad")

def pred(datatype, field, name, context, defaultBase, namespaces):
    # type: (Dict[str, Union[Dict, str]], Dict, str, Dict[str, Union[Dict, str]], str, Dict[str, rdflib.namespace.Namespace]) -> Union[Dict, str]
    split = urlparse.urlsplit(name)

    if split.scheme:
        vee = name  # type: Union[str, unicode]
        (ns, ln) = rdflib.namespace.split_uri(unicode(vee))
        name = ln
        if ns[0:-1] in namespaces:
            vee = unicode(namespaces[ns[0:-1]][ln])
        _logger.debug("name, v %s %s", name, vee)

    v = None  # type: Any
    if field and "jsonldPredicate" in field:
        if isinstance(field["jsonldPredicate"], dict):
            v = {}
            for k, val in field["jsonldPredicate"].items():
                v[("@"+k[1:] if k.startswith("_") else k)] = val
        else:
            v = field["jsonldPredicate"]
    elif "jsonldPredicate" in datatype:
        if isinstance(datatype["jsonldPredicate"], collections.Iterable):
            for d in datatype["jsonldPredicate"]:
                if isinstance(d, dict):
                    if d["symbol"] == name:
                        v = d["predicate"]
                else:
                    raise Exception(
                            "entries in the jsonldPredicate List must be "
                            "Dictionaries")
        else:
            raise Exception("jsonldPredicate must be a List of Dictionaries.")
    # if not v:
    #     if field and "jsonldPrefix" in field:
    #         defaultBase = field["jsonldPrefix"]
    #     elif "jsonldPrefix" in datatype:
    #         defaultBase = datatype["jsonldPrefix"]

    if not v:
        v = defaultBase + name

    if name in context:
        if context[name] != v:
            raise Exception("Predicate collision on %s, '%s' != '%s'" % (name, context[name], v))
    else:
        _logger.debug("Adding to context '%s' %s (%s)", name, v, type(v))
        context[name] = v

    return v

def process_type(t, g, context, defaultBase, namespaces, defaultPrefix):
    # type: (Dict[str, Any], Graph, Dict[str, Union[Dict[Any, Any], str]], str, Dict[str, rdflib.namespace.Namespace], str) -> None
    if t["type"] == "record":
        recordname = t["name"]

        _logger.debug("Processing record %s\n", t)

        classnode = URIRef(recordname)
        g.add((classnode, RDF.type, RDFS.Class))

        split = urlparse.urlsplit(recordname)
        if "jsonldPrefix" in t:
            predicate = "%s:%s" % (t["jsonldPrefix"], recordname)
        elif split.scheme:
            (ns, ln) = rdflib.namespace.split_uri(unicode(recordname))
            predicate = recordname
            recordname = ln
        else:
            predicate = "%s:%s" % (defaultPrefix, recordname)

        if context.get(recordname, predicate) != predicate:
            raise Exception("Predicate collision on '%s', '%s' != '%s'" % (recordname, context[recordname], predicate))

        if not recordname:
            raise Exception()

        _logger.debug("Adding to context '%s' %s (%s)", recordname, predicate, type(predicate))
        context[recordname] = predicate

        for i in t.get("fields", []):
            fieldname = i["name"]

            _logger.debug("Processing field %s", i)

            v = pred(t, i, fieldname, context, defaultPrefix, namespaces)

            if isinstance(v, basestring):
                v = v if v[0] != "@" else None
            else:
                v = v["_@id"] if v.get("_@id", "@")[0] != "@" else None

            if v:
                (ns, ln) = rdflib.namespace.split_uri(unicode(v))
                if ns[0:-1] in namespaces:
                    propnode = namespaces[ns[0:-1]][ln]
                else:
                    propnode = URIRef(v)

                g.add((propnode, RDF.type, RDF.Property))
                g.add((propnode, RDFS.domain, classnode))

                # TODO generate range from datatype.

            if isinstance(i["type"], dict) and "name" in i["type"]:
                process_type(i["type"], g, context, defaultBase, namespaces, defaultPrefix)

        if "extends" in t:
            for e in aslist(t["extends"]):
                g.add((classnode, RDFS.subClassOf, URIRef(e)))
    elif t["type"] == "enum":
        _logger.debug("Processing enum %s", t["name"])

        for i in t["symbols"]:
            pred(t, None, i, context, defaultBase, namespaces)


def salad_to_jsonld_context(j, schema_ctx):
    # type: (Iterable, Dict[str, Any]) -> Tuple[Loader.ContextType, Graph]
    context = {}
    namespaces = {}
    g = Graph()
    defaultPrefix = ""

    for k,v in schema_ctx.items():
        context[k] = v
        namespaces[k] = rdflib.namespace.Namespace(v)

    if "@base" in context:
        defaultBase = context["@base"]
        del context["@base"]
    else:
        defaultBase = ""

    for k,v in namespaces.items():
        g.bind(k, v)

    for t in j:
        process_type(t, g, context, defaultBase, namespaces, defaultPrefix)

    return (context, g)
