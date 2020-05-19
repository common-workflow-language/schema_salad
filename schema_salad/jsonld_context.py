import logging
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Tuple,
    Union,
    cast,
)
from urllib.parse import urldefrag, urlsplit

import rdflib
import rdflib.namespace
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .exceptions import SchemaException
from .ref_resolver import ContextType
from .utils import aslist, json_dumps

_logger = logging.getLogger("salad")


def pred(
    datatype: MutableMapping[str, Union[Dict[str, str], str]],
    field: Optional[Dict[str, Any]],
    name: str,
    context: ContextType,
    defaultBase: str,
    namespaces: Dict[str, rdflib.namespace.Namespace],
) -> Union[Dict[str, Union[str, None]], str]:
    split = urlsplit(name)

    vee = None  # type: Optional[str]

    if split.scheme != "":
        vee = name
        (ns, ln) = rdflib.namespace.split_uri(str(vee))
        name = ln
        if ns[0:-1] in namespaces:
            vee = str(namespaces[ns[0:-1]][ln])
        _logger.debug("name, v %s %s", name, vee)

    v = None  # type: Optional[Union[Dict[str, Union[str, None]], str]]

    if field is not None and "jsonldPredicate" in field:
        if isinstance(field["jsonldPredicate"], MutableMapping):
            v = {}
            for k, val in field["jsonldPredicate"].items():
                v[("@" + k[1:] if k.startswith("_") else k)] = val
            if "@id" not in v:
                v["@id"] = vee
        else:
            v = field["jsonldPredicate"]
    elif "jsonldPredicate" in datatype:
        if isinstance(datatype["jsonldPredicate"], Iterable):
            for d in datatype["jsonldPredicate"]:
                if isinstance(d, MutableMapping):
                    if d["symbol"] == name:
                        v = d["predicate"]
                else:
                    raise SchemaException(
                        "entries in the jsonldPredicate List must be " "Dictionaries"
                    )
        else:
            raise SchemaException("jsonldPredicate must be a List of Dictionaries.")

    ret = v or vee

    if not ret:
        ret = defaultBase + name

    if name in context:
        if context[name] != ret:
            raise SchemaException(
                "Predicate collision on {}, '{}' != '{}'".format(
                    name, context[name], ret
                )
            )
    else:
        _logger.debug("Adding to context '%s' %s (%s)", name, ret, type(ret))
        context[name] = ret

    return ret


def process_type(
    t: MutableMapping[str, Any],
    g: Graph,
    context: ContextType,
    defaultBase: str,
    namespaces: Dict[str, rdflib.namespace.Namespace],
    defaultPrefix: str,
) -> None:
    if t["type"] not in ("record", "enum"):
        return

    if "name" in t:
        recordname = t["name"]

        _logger.debug("Processing %s %s\n", t.get("type"), t)

        classnode = URIRef(recordname)
        g.add((classnode, RDF.type, RDFS.Class))

        split = urlsplit(recordname)
        predicate = recordname
        if t.get("inVocab", True):
            if split.scheme:
                (ns, ln) = rdflib.namespace.split_uri(str(recordname))
                predicate = recordname
                recordname = ln
            else:
                predicate = "{}:{}".format(defaultPrefix, recordname)

        if context.get(recordname, predicate) != predicate:
            raise SchemaException(
                "Predicate collision on '{}', '{}' != '{}'".format(
                    recordname, context[recordname], predicate
                )
            )

        if not recordname:
            raise SchemaException("Unable to find/derive recordname for {}".format(t))

        _logger.debug(
            "Adding to context '%s' %s (%s)", recordname, predicate, type(predicate)
        )
        context[recordname] = predicate

    if t["type"] == "record":
        for i in t.get("fields", []):
            fieldname = i["name"]

            _logger.debug("Processing field %s", i)

            v = pred(
                t, i, fieldname, context, defaultPrefix, namespaces
            )  # type: Union[Dict[Any, Any], str, None]

            if isinstance(v, str):
                v = v if v[0] != "@" else None
            elif v is not None:
                v = v["_@id"] if v.get("_@id", "@")[0] != "@" else None

            if bool(v):
                (ns, ln) = rdflib.namespace.split_uri(str(v))
                if ns[0:-1] in namespaces:
                    propnode = namespaces[ns[0:-1]][ln]
                else:
                    propnode = URIRef(v)

                g.add((propnode, RDF.type, RDF.Property))
                g.add((propnode, RDFS.domain, classnode))

                # TODO generate range from datatype.

            if isinstance(i["type"], MutableMapping):
                process_type(
                    i["type"], g, context, defaultBase, namespaces, defaultPrefix
                )

        if "extends" in t:
            for e in aslist(t["extends"]):
                g.add((classnode, RDFS.subClassOf, URIRef(e)))
    elif t["type"] == "enum":
        _logger.debug("Processing enum %s", t.get("name"))

        for i in t["symbols"]:
            pred(t, None, i, context, defaultBase, namespaces)


def salad_to_jsonld_context(
    j: Iterable[MutableMapping[str, Any]], schema_ctx: MutableMapping[str, Any]
) -> Tuple[ContextType, Graph]:
    context = {}  # type: ContextType
    namespaces = {}
    g = Graph()
    defaultPrefix = ""

    for k, v in schema_ctx.items():
        context[k] = v
        namespaces[k] = rdflib.namespace.Namespace(v)

    if "@base" in context:
        defaultBase = cast(str, context["@base"])
        del context["@base"]
    else:
        defaultBase = ""

    for k, v in namespaces.items():
        g.bind(str(k), v)

    for t in j:
        process_type(t, g, context, defaultBase, namespaces, defaultPrefix)

    return (context, g)


def fix_jsonld_ids(
    obj: Union[CommentedMap, float, str, CommentedSeq], ids: List[str]
) -> None:
    if isinstance(obj, MutableMapping):
        for i in ids:
            if i in obj:
                obj["@id"] = obj[i]
        for v in obj.values():
            fix_jsonld_ids(v, ids)
    if isinstance(obj, MutableSequence):
        for entry in obj:
            fix_jsonld_ids(entry, ids)


def makerdf(
    workflow: Optional[str],
    wf: Union[CommentedMap, float, str, CommentedSeq],
    ctx: ContextType,
    graph: Optional[Graph] = None,
) -> Graph:
    prefixes = {}
    idfields = []
    for k, v in ctx.items():
        if isinstance(v, MutableMapping):
            url = v["@id"]
        else:
            url = v
        if url == "@id":
            idfields.append(k)
        doc_url, frg = urldefrag(url)
        if "/" in frg:
            p = frg.split("/")[0]
            prefixes[p] = "{}#{}/".format(doc_url, p)

    fix_jsonld_ids(wf, idfields)

    g = Graph() if graph is None else graph

    if isinstance(wf, MutableSequence):
        for w in wf:
            w["@context"] = ctx
            g.parse(data=json_dumps(w), format="json-ld", publicID=str(workflow))
    elif isinstance(wf, MutableMapping):
        wf["@context"] = ctx
        g.parse(data=json_dumps(wf), format="json-ld", publicID=str(workflow))
    else:
        raise SchemaException("{} is not a workflow".format(wf))

    # Bug in json-ld loader causes @id fields to be added to the graph
    for sub, pred, obj in g.triples((None, URIRef("@id"), None)):
        g.remove((sub, pred, obj))

    for k2, v2 in prefixes.items():
        g.namespace_manager.bind(k2, v2)

    return g
