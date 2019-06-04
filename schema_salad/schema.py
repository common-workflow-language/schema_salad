"""Functions to process Schema Salad schemas."""
from __future__ import absolute_import

import copy
import hashlib
from typing import (IO, Any, AnyStr, Dict, List, Mapping, MutableMapping,
                    MutableSequence, Set, Tuple, TypeVar, Union, cast)

from pkg_resources import resource_stream
from ruamel import yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from six import iteritems, string_types
from six.moves import urllib
from typing_extensions import Text  # pylint: disable=unused-import

from schema_salad.utils import (add_dictlist, aslist, convert_to_dict, flatten,
                                json_dumps)
from . import _logger
from .avro.schema import Names, SchemaParseException, make_avsc_object
from . import jsonld_context, ref_resolver, validate
from .ref_resolver import Loader
from .sourceline import (SourceLine, add_lc_filename, bullets, relname,
                         strip_dup_lineno)

SALAD_FILES = ('metaschema.yml',
               'metaschema_base.yml',
               'salad.md',
               'field_name.yml',
               'import_include.md',
               'link_res.yml',
               'ident_res.yml',
               'vocab_res.yml',
               'vocab_res.yml',
               'field_name_schema.yml',
               'field_name_src.yml',
               'field_name_proc.yml',
               'ident_res_schema.yml',
               'ident_res_src.yml',
               'ident_res_proc.yml',
               'link_res_schema.yml',
               'link_res_src.yml',
               'link_res_proc.yml',
               'vocab_res_schema.yml',
               'vocab_res_src.yml',
               'vocab_res_proc.yml',
               'map_res.yml',
               'map_res_schema.yml',
               'map_res_src.yml',
               'map_res_proc.yml',
               'typedsl_res.yml',
               'typedsl_res_schema.yml',
               'typedsl_res_src.yml',
               'typedsl_res_proc.yml',
               'sfdsl_res.yml',
               'sfdsl_res_schema.yml',
               'sfdsl_res_src.yml',
               'sfdsl_res_proc.yml')


def get_metaschema():  # type: () -> Tuple[Names, List[Dict[Text, Any]], Loader]
    """Instantiate the metaschema."""
    loader = ref_resolver.Loader({
        "Any": "https://w3id.org/cwl/salad#Any",
        "ArraySchema": "https://w3id.org/cwl/salad#ArraySchema",
        "Array_symbol": "https://w3id.org/cwl/salad#ArraySchema/type/Array_symbol",
        "DocType": "https://w3id.org/cwl/salad#DocType",
        "Documentation": "https://w3id.org/cwl/salad#Documentation",
        "Documentation_symbol":
            "https://w3id.org/cwl/salad#Documentation/type/Documentation_symbol",
        "Documented": "https://w3id.org/cwl/salad#Documented",
        "EnumSchema": "https://w3id.org/cwl/salad#EnumSchema",
        "Enum_symbol": "https://w3id.org/cwl/salad#EnumSchema/type/Enum_symbol",
        "JsonldPredicate": "https://w3id.org/cwl/salad#JsonldPredicate",
        "NamedType": "https://w3id.org/cwl/salad#NamedType",
        "PrimitiveType": "https://w3id.org/cwl/salad#PrimitiveType",
        "RecordField": "https://w3id.org/cwl/salad#RecordField",
        "RecordSchema": "https://w3id.org/cwl/salad#RecordSchema",
        "Record_symbol": "https://w3id.org/cwl/salad#RecordSchema/type/Record_symbol",
        "SaladEnumSchema": "https://w3id.org/cwl/salad#SaladEnumSchema",
        "SaladRecordField": "https://w3id.org/cwl/salad#SaladRecordField",
        "SaladRecordSchema": "https://w3id.org/cwl/salad#SaladRecordSchema",
        "SchemaDefinedType": "https://w3id.org/cwl/salad#SchemaDefinedType",
        "SpecializeDef": "https://w3id.org/cwl/salad#SpecializeDef",
        "_container": "https://w3id.org/cwl/salad#JsonldPredicate/_container",
        "_id": {
            "@id": "https://w3id.org/cwl/salad#_id",
            "@type": "@id",
            "identity": True
        },
        "_type": "https://w3id.org/cwl/salad#JsonldPredicate/_type",
        "abstract": "https://w3id.org/cwl/salad#SaladRecordSchema/abstract",
        "array": "https://w3id.org/cwl/salad#array",
        "boolean": "http://www.w3.org/2001/XMLSchema#boolean",
        "dct": "http://purl.org/dc/terms/",
        "default": {
            "@id": "https://w3id.org/cwl/salad#default",
            "noLinkCheck": True
        },
        "doc": "rdfs:comment",
        "docAfter": {
            "@id": "https://w3id.org/cwl/salad#docAfter",
            "@type": "@id"
        },
        "docChild": {
            "@id": "https://w3id.org/cwl/salad#docChild",
            "@type": "@id"
        },
        "docParent": {
            "@id": "https://w3id.org/cwl/salad#docParent",
            "@type": "@id"
        },
        "documentRoot": "https://w3id.org/cwl/salad#SchemaDefinedType/documentRoot",
        "documentation": "https://w3id.org/cwl/salad#documentation",
        "double": "http://www.w3.org/2001/XMLSchema#double",
        "enum": "https://w3id.org/cwl/salad#enum",
        "extends": {
            "@id": "https://w3id.org/cwl/salad#extends",
            "@type": "@id",
            "refScope": 1
        },
        "fields": {
            "@id": "https://w3id.org/cwl/salad#fields",
            "mapPredicate": "type",
            "mapSubject": "name"
        },
        "float": "http://www.w3.org/2001/XMLSchema#float",
        "identity": "https://w3id.org/cwl/salad#JsonldPredicate/identity",
        "inVocab": "https://w3id.org/cwl/salad#NamedType/inVocab",
        "int": "http://www.w3.org/2001/XMLSchema#int",
        "items": {
            "@id": "https://w3id.org/cwl/salad#items",
            "@type": "@vocab",
            "refScope": 2
        },
        "jsonldPredicate": "sld:jsonldPredicate",
        "long": "http://www.w3.org/2001/XMLSchema#long",
        "mapPredicate": "https://w3id.org/cwl/salad#JsonldPredicate/mapPredicate",
        "mapSubject": "https://w3id.org/cwl/salad#JsonldPredicate/mapSubject",
        "name": "@id",
        "noLinkCheck": "https://w3id.org/cwl/salad#JsonldPredicate/noLinkCheck",
        "null": "https://w3id.org/cwl/salad#null",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "record": "https://w3id.org/cwl/salad#record",
        "refScope": "https://w3id.org/cwl/salad#JsonldPredicate/refScope",
        "sld": "https://w3id.org/cwl/salad#",
        "specialize": {
            "@id": "https://w3id.org/cwl/salad#specialize",
            "mapPredicate": "specializeTo",
            "mapSubject": "specializeFrom"
        },
        "specializeFrom": {
            "@id": "https://w3id.org/cwl/salad#specializeFrom",
            "@type": "@id",
            "refScope": 1
        },
        "specializeTo": {
            "@id": "https://w3id.org/cwl/salad#specializeTo",
            "@type": "@id",
            "refScope": 1
        },
        "string": "http://www.w3.org/2001/XMLSchema#string",
        "subscope": "https://w3id.org/cwl/salad#JsonldPredicate/subscope",
        "symbols": {
            "@id": "https://w3id.org/cwl/salad#symbols",
            "@type": "@id",
            "identity": True
        },
        "type": {
            "@id": "https://w3id.org/cwl/salad#type",
            "@type": "@vocab",
            "refScope": 2,
            "typeDSL": True
        },
        "typeDSL": "https://w3id.org/cwl/salad#JsonldPredicate/typeDSL",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    })

    for salad in SALAD_FILES:
        with resource_stream(__name__, 'metaschema/' + salad) as stream:
            loader.cache["https://w3id.org/cwl/" + salad] = stream.read()

    with resource_stream(__name__, 'metaschema/metaschema.yml') as stream:
        loader.cache["https://w3id.org/cwl/salad"] = stream.read()

    j = yaml.round_trip_load(loader.cache["https://w3id.org/cwl/salad"])
    add_lc_filename(j, "metaschema.yml")
    j, _ = loader.resolve_all(j, "https://w3id.org/cwl/salad#")

    sch_obj = make_avro(j, loader)
    try:
        sch_names = make_avro_schema_from_avro(sch_obj)
    except SchemaParseException:
        _logger.error("Metaschema error, avro was:\n%s",
                      json_dumps(sch_obj, indent=4))
        raise
    validate_doc(sch_names, j, loader, strict=True)
    return (sch_names, j, loader)

def add_namespaces(metadata, namespaces):
    # type: (Mapping[Text, Any], MutableMapping[Text, Text]) -> None
    """Collect the provided namespaces, checking for conflicts."""
    for key, value in metadata.items():
        if key not in namespaces:
            namespaces[key] = value
        elif namespaces[key] != value:
            raise validate.ValidationException(
                "Namespace prefix '{}' has conflicting definitions '{}'"
                " and '{}'.".format(key, namespaces[key], value))


def collect_namespaces(metadata):
    # type: (Mapping[Text, Any]) -> Dict[Text, Text]
    """Walk through the metadata object, collecting namespace declarations."""
    namespaces = {}  # type: Dict[Text, Text]
    if "$import_metadata" in metadata:
        for value in metadata["$import_metadata"].values():
            add_namespaces(collect_namespaces(value), namespaces)
    if "$namespaces" in metadata:
        add_namespaces(metadata["$namespaces"], namespaces)
    return namespaces

def load_schema(schema_ref,  # type: Union[CommentedMap, CommentedSeq, Text]
                cache=None   # type: Dict
                ):
    # type: (...) -> Tuple[Loader, Union[Names, SchemaParseException], Dict[Text, Any], Loader]
    """
    Load a schema that can be used to validate documents using load_and_validate.

    return: document_loader, avsc_names, schema_metadata, metaschema_loader
    """

    metaschema_names, _metaschema_doc, metaschema_loader = get_metaschema()
    if cache is not None:
        metaschema_loader.cache.update(cache)
    schema_doc, schema_metadata = metaschema_loader.resolve_ref(schema_ref, "")

    if not isinstance(schema_doc, MutableSequence):
        raise ValueError("Schema reference must resolve to a list.")

    validate_doc(metaschema_names, schema_doc, metaschema_loader, True)
    metactx = schema_metadata.get("@context", {})
    metactx.update(collect_namespaces(schema_metadata))
    schema_ctx = jsonld_context.salad_to_jsonld_context(schema_doc, metactx)[0]

    # Create the loader that will be used to load the target document.
    document_loader = Loader(schema_ctx, cache=cache)

    # Make the Avro validation that will be used to validate the target
    # document
    avsc_names = make_avro_schema(schema_doc, document_loader)

    return document_loader, avsc_names, schema_metadata, metaschema_loader


def load_and_validate(document_loader,                 # type: Loader
                      avsc_names,                      # type: Names
                      document,                        # type: Union[CommentedMap, Text]
                      strict,                          # type: bool
                      strict_foreign_properties=False  # type: bool
                      ):
    # type: (...) -> Tuple[Any, Dict[Text, Any]]
    """Load a document and validate it with the provided schema.

    return data, metadata
    """
    try:
        if isinstance(document, CommentedMap):
            data, metadata = document_loader.resolve_all(
                document, document["id"], checklinks=True,
                strict_foreign_properties=strict_foreign_properties)
        else:
            data, metadata = document_loader.resolve_ref(
                document, checklinks=True,
                strict_foreign_properties=strict_foreign_properties)

        validate_doc(avsc_names, data, document_loader, strict,
                     strict_foreign_properties=strict_foreign_properties)

        return data, metadata
    except validate.ValidationException as exc:
        raise validate.ValidationException(strip_dup_lineno(str(exc)))


def validate_doc(schema_names,  # type: Names
                 doc,           # type: Union[Dict[Text, Any], List[Dict[Text, Any]], Text, None]
                 loader,        # type: Loader
                 strict,        # type: bool
                 strict_foreign_properties=False  # type: bool
                 ):
    # type: (...) -> None
    """Validate a document using the provided schema."""
    has_root = False
    for root in schema_names.names.values():
        if ((hasattr(root, 'get_prop') and root.get_prop(u"documentRoot")) or (
                u"documentRoot" in root.props)):
            has_root = True
            break

    if not has_root:
        raise validate.ValidationException(
            "No document roots defined in the schema")

    if isinstance(doc, MutableSequence):
        vdoc = doc
    elif isinstance(doc, CommentedMap):
        vdoc = CommentedSeq([doc])
        vdoc.lc.add_kv_line_col(0, [doc.lc.line, doc.lc.col])
        vdoc.lc.filename = doc.lc.filename
    else:
        raise validate.ValidationException("Document must be dict or list")

    roots = []
    for root in schema_names.names.values():
        if ((hasattr(root, "get_prop") and root.get_prop(u"documentRoot")) or (
                root.props.get(u"documentRoot"))):
            roots.append(root)

    anyerrors = []
    for pos, item in enumerate(vdoc):
        sourceline = SourceLine(vdoc, pos, Text)
        success = False
        for root in roots:
            success = validate.validate_ex(
                root, item, loader.identifiers, strict,
                foreign_properties=loader.foreign_properties,
                raise_ex=False, skip_foreign_properties=loader.skip_schemas,
                strict_foreign_properties=strict_foreign_properties)
            if success:
                break

        if not success:
            errors = []  # type: List[Text]
            for root in roots:
                if hasattr(root, "get_prop"):
                    name = root.get_prop(u"name")
                elif hasattr(root, "name"):
                    name = root.name

                try:
                    validate.validate_ex(
                        root, item, loader.identifiers, strict,
                        foreign_properties=loader.foreign_properties,
                        raise_ex=True, skip_foreign_properties=loader.skip_schemas,
                        strict_foreign_properties=strict_foreign_properties)
                except validate.ClassValidationException as exc:
                    errors = [sourceline.makeError(u"tried `%s` but\n%s" % (
                        name, validate.indent(str(exc), nolead=False)))]
                    break
                except validate.ValidationException as exc:
                    errors.append(sourceline.makeError(u"tried `%s` but\n%s" % (
                        name, validate.indent(str(exc), nolead=False))))

            objerr = sourceline.makeError(u"Invalid")
            for ident in loader.identifiers:
                if ident in item:
                    objerr = sourceline.makeError(
                        u"Object `%s` is not valid because"
                        % (relname(item[ident])))
                    break
            anyerrors.append(u"%s\n%s" %
                             (objerr, validate.indent(bullets(errors, "- "))))
    if anyerrors:
        raise validate.ValidationException(
            strip_dup_lineno(bullets(anyerrors, "* ")))

def get_anon_name(rec):
    # type: (MutableMapping[Text, Any]) -> Text
    """Calculate a reproducible name for anonymous types."""
    if "name" in rec:
        return rec["name"]
    anon_name = ""
    if rec['type'] in ('enum', 'https://w3id.org/cwl/salad#enum'):
        for sym in rec["symbols"]:
            anon_name += sym
        return "enum_"+hashlib.sha1(anon_name.encode("UTF-8")).hexdigest()
    if rec['type'] in ('record', 'https://w3id.org/cwl/salad#record'):
        for field in rec["fields"]:
            anon_name += field["name"]
        return "record_"+hashlib.sha1(anon_name.encode("UTF-8")).hexdigest()
    if rec['type'] in ('array', 'https://w3id.org/cwl/salad#array'):
        return ""
    raise validate.ValidationException("Expected enum or record, was %s" % rec['type'])

def replace_type(items, spec, loader, found, find_embeds=True, deepen=True):
    # type: (Any, Dict[Text, Any], Loader, Set[Text], bool, bool) -> Any
    """ Go through and replace types in the 'spec' mapping"""

    if isinstance(items, MutableMapping):
        # recursively check these fields for types to replace
        if items.get("type") in ("record", "enum") and items.get("name"):
            if items["name"] in found:
                return items["name"]
            found.add(items["name"])

        if not deepen:
            return items

        items = copy.copy(items)
        if not items.get("name"):
            items["name"] = get_anon_name(items)
        for name in ("type", "items", "fields"):
            if name in items:
                items[name] = replace_type(
                    items[name], spec, loader, found, find_embeds=find_embeds,
                    deepen=find_embeds)
                if isinstance(items[name], MutableSequence):
                    items[name] = flatten(items[name])

        return items
    if isinstance(items, MutableSequence):
        # recursively transform list
        return [replace_type(i, spec, loader, found, find_embeds=find_embeds,
                             deepen=deepen) for i in items]
    if isinstance(items, string_types):
        # found a string which is a symbol corresponding to a type.
        replace_with = None
        if items in loader.vocab:
            # If it's a vocabulary term, first expand it to its fully qualified
            # URI
            items = loader.vocab[items]

        if items in spec:
            # Look up in specialization map
            replace_with = spec[items]

        if replace_with:
            return replace_type(replace_with, spec, loader, found, find_embeds=find_embeds)
        found.add(items)
    return items


def avro_name(url):  # type: (AnyStr) -> AnyStr
    """
    Turn a URL into an Avro-safe name.

    If the URL has no fragment, return this plain URL.

    Extract either the last part of the URL fragment past the slash, otherwise
    the whole fragment.
    """
    frg = urllib.parse.urldefrag(url)[1]
    if frg != '':
        if '/' in frg:
            return frg[frg.rindex('/') + 1:]
        return frg
    return url


Avro = TypeVar('Avro', Dict[Text, Any], List[Any], Text)


def make_valid_avro(items,          # type: Avro
                    alltypes,       # type: Dict[Text, Dict[Text, Any]]
                    found,          # type: Set[Text]
                    union=False     # type: bool
                    ):
    # type: (...) -> Union[Avro, Dict, Text]
    """Convert our schema to be more avro like."""
    # Possibly could be integrated into our fork of avro/schema.py?
    if isinstance(items, MutableMapping):
        items = copy.copy(items)
        if items.get("name") and items.get("inVocab", True):
            items["name"] = avro_name(items["name"])

        if "type" in items and items["type"] in (
                "https://w3id.org/cwl/salad#record",
                "https://w3id.org/cwl/salad#enum", "record", "enum"):
            if (hasattr(items, "get") and items.get("abstract")) or ("abstract"
                                                                     in items):
                return items
            if items["name"] in found:
                return cast(Text, items["name"])
            found.add(items["name"])
        for field in ("type", "items", "values", "fields"):
            if field in items:
                items[field] = make_valid_avro(
                    items[field], alltypes, found, union=True)
        if "symbols" in items:
            items["symbols"] = [avro_name(sym) for sym in items["symbols"]]
        return items
    if isinstance(items, MutableSequence):
        ret = []
        for i in items:
            ret.append(make_valid_avro(i, alltypes, found, union=union))  # type: ignore
        return ret
    if union and isinstance(items, string_types):
        if items in alltypes and avro_name(items) not in found:
            return cast(Dict, make_valid_avro(alltypes[items], alltypes, found,
                                              union=union))
        items = avro_name(items)
    return items


def deepcopy_strip(item):  # type: (Any) -> Any
    """
    Make a deep copy of list and dict objects.

    Intentionally do not copy attributes.  This is to discard CommentedMap and
    CommentedSeq metadata which is very expensive with regular copy.deepcopy.
    """

    if isinstance(item, MutableMapping):
        return {k: deepcopy_strip(v) for k, v in iteritems(item)}
    if isinstance(item, MutableSequence):
        return [deepcopy_strip(k) for k in item]
    return item


def extend_and_specialize(items, loader):
    # type: (List[Dict[Text, Any]], Loader) -> List[Dict[Text, Any]]
    """
    Apply 'extend' and 'specialize' to fully materialize derived record types.
    """

    items = deepcopy_strip(items)
    types = {i["name"]: i for i in items}  # type: Dict[Text, Any]
    results = []

    for stype in items:
        if "extends" in stype:
            specs = {}  # type: Dict[Text, Text]
            if "specialize" in stype:
                for spec in aslist(stype["specialize"]):
                    specs[spec["specializeFrom"]] = spec["specializeTo"]

            exfields = []  # type: List[Text]
            exsym = []  # type: List[Text]
            for ex in aslist(stype["extends"]):
                if ex not in types:
                    raise Exception(
                        "Extends {} in {} refers to invalid base type.".format(
                            stype["extends"], stype["name"]))

                basetype = copy.copy(types[ex])

                if stype["type"] == "record":
                    if specs:
                        basetype["fields"] = replace_type(
                            basetype.get("fields", []), specs, loader, set())

                    for field in basetype.get("fields", []):
                        if "inherited_from" not in field:
                            field["inherited_from"] = ex

                    exfields.extend(basetype.get("fields", []))
                elif stype["type"] == "enum":
                    exsym.extend(basetype.get("symbols", []))

            if stype["type"] == "record":
                stype = copy.copy(stype)
                exfields.extend(stype.get("fields", []))
                stype["fields"] = exfields

                fieldnames = set()  # type: Set[Text]
                for field in stype["fields"]:
                    if field["name"] in fieldnames:
                        raise validate.ValidationException(
                            "Field name {} appears twice in {}".format(
                                field["name"], stype["name"]))
                    else:
                        fieldnames.add(field["name"])
            elif stype["type"] == "enum":
                stype = copy.copy(stype)
                exsym.extend(stype.get("symbols", []))
                stype["symbol"] = exsym

            types[stype["name"]] = stype

        results.append(stype)

    ex_types = {}
    for result in results:
        ex_types[result["name"]] = result

    extended_by = {}  # type: Dict[Text, Text]
    for result in results:
        if "extends" in result:
            for ex in aslist(result["extends"]):
                if ex_types[ex].get("abstract"):
                    add_dictlist(extended_by, ex, ex_types[result["name"]])
                    add_dictlist(extended_by, avro_name(ex), ex_types[ex])

    for result in results:
        if result.get("abstract") and result["name"] not in extended_by:
            raise validate.ValidationException(
                "{} is abstract but missing a concrete subtype".format(
                    result["name"]))

    for result in results:
        if "fields" in result:
            result["fields"] = replace_type(
                result["fields"], extended_by, loader, set())

    return results


def make_avro(i,         # type: List[Dict[Text, Any]]
              loader     # type: Loader
             ):  # type: (...) -> List[Any]

    j = extend_and_specialize(i, loader)

    name_dict = {}  # type: Dict[Text, Dict[Text, Any]]
    for entry in j:
        name_dict[entry["name"]] = entry
    avro = make_valid_avro(j, name_dict, set())

    return [t for t in avro if isinstance(t, MutableMapping) and not t.get(
        "abstract") and t.get("type") != "documentation"]


def make_avro_schema(i,         # type: List[Any]
                     loader     # type: Loader
                     ):  # type: (...) -> Names
    """
    All in one convenience function.

    Call make_avro() and make_avro_schema_from_avro() separately if you need
    the intermediate result for diagnostic output.
    """
    names = Names()
    avro = make_avro(i, loader)
    make_avsc_object(convert_to_dict(avro), names)
    return names


def make_avro_schema_from_avro(avro):
    # type: (List[Union[Avro, Dict, Text]]) -> Names
    names = Names()
    make_avsc_object(convert_to_dict(avro), names)
    return names


def shortname(inputid):  # type: (Text) -> Text
    """Returns the last segment of the provided fragment or path."""
    parsed_id = urllib.parse.urlparse(inputid)
    if parsed_id.fragment:
        return parsed_id.fragment.split(u"/")[-1]
    return parsed_id.path.split(u"/")[-1]


def print_inheritance(doc, stream):
    # type: (List[Dict[Text, Any]], IO) -> None
    """Write a Grapviz inheritance graph for the supplied document."""
    stream.write("digraph {\n")
    for entry in doc:
        if entry["type"] == "record":
            label = name = shortname(entry["name"])
            fields = entry.get("fields", [])
            if fields:
                label += "\\n* %s\\l" % (
                    "\\l* ".join(shortname(field["name"])
                                 for field in fields))
            shape = "ellipse" if entry.get("abstract") else "box"
            stream.write("\"%s\" [shape=%s label=\"%s\"];\n"
                         % (name, shape, label))
            if "extends" in entry:
                for target in aslist(entry["extends"]):
                    stream.write("\"%s\" -> \"%s\";\n"
                                 % (shortname(target), name))
    stream.write("}\n")


def print_fieldrefs(doc, loader, stream):
    # type: (List[Dict[Text, Any]], Loader, IO) -> None
    """Write a GraphViz graph of the relationships between the fields."""
    obj = extend_and_specialize(doc, loader)

    primitives = set(("http://www.w3.org/2001/XMLSchema#string",
                      "http://www.w3.org/2001/XMLSchema#boolean",
                      "http://www.w3.org/2001/XMLSchema#int",
                      "http://www.w3.org/2001/XMLSchema#long",
                      "https://w3id.org/cwl/salad#null",
                      "https://w3id.org/cwl/salad#enum",
                      "https://w3id.org/cwl/salad#array",
                      "https://w3id.org/cwl/salad#record",
                      "https://w3id.org/cwl/salad#Any"))

    stream.write("digraph {\n")
    for entry in obj:
        if entry.get("abstract"):
            continue
        if entry["type"] == "record":
            label = shortname(entry["name"])
            for field in entry.get("fields", []):
                found = set()  # type: Set[Text]
                field_name = shortname(field["name"])
                replace_type(field["type"], {}, loader, found, find_embeds=False)
                for each_type in found:
                    if each_type not in primitives:
                        stream.write(
                            "\"%s\" -> \"%s\" [label=\"%s\"];\n"
                            % (label, shortname(each_type), field_name))
    stream.write("}\n")
