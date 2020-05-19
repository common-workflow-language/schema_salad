"""Command line interface to schema-salad."""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Mapping, MutableSequence, Optional, Union, cast
from urllib.parse import urlparse

import pkg_resources  # part of setuptools
from rdflib.parser import Parser
from rdflib.plugin import register

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from . import codegen, jsonld_context, schema
from .avro.schema import SchemaParseException
from .exceptions import ValidationException, to_one_line_messages
from .makedoc import makedoc
from .ref_resolver import Loader, file_uri
from .utils import json_dumps

register("json-ld", Parser, "rdflib_jsonld.parser", "JsonLDParser")
_logger = logging.getLogger("salad")


def printrdf(
    workflow: str, wf: Union[CommentedMap, CommentedSeq], ctx: Dict[str, Any], sr: str,
) -> None:
    g = jsonld_context.makerdf(workflow, wf, ctx)
    print(g.serialize(format=sr, encoding="utf-8").decode("utf-8"))


def main(argsl: Optional[List[str]] = None) -> int:
    if argsl is None:
        argsl = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rdf-serializer",
        help="Output RDF serialization format used by --print-rdf"
        "(one of turtle (default), n3, nt, xml)",
        default="turtle",
    )

    parser.add_argument(
        "--skip-schemas",
        action="store_true",
        default=False,
        help="If specified, ignore $schemas sections.",
    )
    parser.add_argument(
        "--strict-foreign-properties",
        action="store_true",
        help="Strict checking of foreign properties",
        default=False,
    )

    exgroup = parser.add_mutually_exclusive_group()
    exgroup.add_argument(
        "--print-jsonld-context",
        action="store_true",
        help="Print JSON-LD context for schema",
    )
    exgroup.add_argument("--print-rdfs", action="store_true", help="Print RDF schema")
    exgroup.add_argument("--print-avro", action="store_true", help="Print Avro schema")

    exgroup.add_argument(
        "--print-rdf",
        action="store_true",
        help="Print corresponding RDF graph for document",
    )
    exgroup.add_argument(
        "--print-pre", action="store_true", help="Print document after preprocessing"
    )
    exgroup.add_argument("--print-index", action="store_true", help="Print node index")
    exgroup.add_argument(
        "--print-metadata", action="store_true", help="Print document metadata"
    )
    exgroup.add_argument(
        "--print-inheritance-dot",
        action="store_true",
        help="Print graphviz file of inheritance",
    )
    exgroup.add_argument(
        "--print-fieldrefs-dot",
        action="store_true",
        help="Print graphviz file of field refs",
    )

    exgroup.add_argument(
        "--codegen",
        type=str,
        metavar="language",
        help="Generate classes in target language, currently supported: python, java",
    )

    parser.add_argument(
        "--codegen-target",
        type=str,
        default=None,
        help="Defaults to sys.stdout for python and ./ for Java",
    )

    parser.add_argument(
        "--codegen-examples",
        type=str,
        metavar="directory",
        default=None,
        help="Directory of example documents for test case generation (Java only).",
    )

    exgroup.add_argument(
        "--print-oneline",
        action="store_true",
        help="Print each error message in oneline",
    )

    exgroup.add_argument(
        "--print-doc", action="store_true", help="Print HTML schema documentation page"
    )

    exgroup_strict = parser.add_mutually_exclusive_group()
    exgroup_strict.add_argument(
        "--strict",
        action="store_true",
        help="Strict validation (unrecognized or out of place fields are error)",
        default=True,
        dest="strict",
    )
    exgroup_strict.add_argument(
        "--non-strict",
        action="store_false",
        help="Lenient validation (ignore unrecognized fields)",
        default=True,
        dest="strict",
    )

    exgroup_volume = parser.add_mutually_exclusive_group()
    exgroup_volume.add_argument(
        "--verbose", action="store_true", help="Default logging"
    )
    exgroup_volume.add_argument(
        "--quiet", action="store_true", help="Only print warnings and errors."
    )
    exgroup_volume.add_argument(
        "--debug", action="store_true", help="Print even more logging"
    )

    parser.add_argument(
        "--only",
        action="append",
        help="Use with --print-doc, document only listed types",
    )
    parser.add_argument(
        "--redirect",
        action="append",
        help="Use with --print-doc, override default link for type",
    )
    parser.add_argument(
        "--brand", help="Use with --print-doc, set the 'brand' text in nav bar"
    )
    parser.add_argument(
        "--brandlink", help="Use with --print-doc, set the link for 'brand' in nav bar"
    )
    parser.add_argument(
        "--primtype",
        default="#PrimitiveType",
        help="Use with --print-doc, link to use for primitive types (string, int etc)",
    )

    parser.add_argument("schema", type=str, nargs="?", default=None)
    parser.add_argument("document", type=str, nargs="?", default=None)
    parser.add_argument(
        "--version", "-v", action="store_true", help="Print version", default=None
    )

    args = parser.parse_args(argsl)

    if args.version is None and args.schema is None:
        print("{}: error: too few arguments".format(sys.argv[0]))
        return 1

    if args.quiet:
        _logger.setLevel(logging.WARN)
    if args.debug:
        _logger.setLevel(logging.DEBUG)

    pkg = pkg_resources.require("schema_salad")
    if pkg:
        if args.version:
            print("{} Current version: {}".format(sys.argv[0], pkg[0].version))
            return 0
        else:
            _logger.info("%s Current version: %s", sys.argv[0], pkg[0].version)

    # Get the metaschema to validate the schema
    metaschema_names, metaschema_doc, metaschema_loader = schema.get_metaschema()

    # Load schema document and resolve refs

    schema_uri = args.schema
    if not (
        urlparse(schema_uri)[0] and urlparse(schema_uri)[0] in ["http", "https", "file"]
    ):
        schema_uri = file_uri(os.path.abspath(schema_uri))
    schema_raw_doc = metaschema_loader.fetch(schema_uri)

    try:
        schema_doc, schema_metadata = metaschema_loader.resolve_all(
            schema_raw_doc, schema_uri
        )
    except ValidationException as e:
        _logger.error(
            "Schema `%s` failed link checking:\n%s",
            args.schema,
            str(e),
            exc_info=(True if args.debug else False),
        )
        _logger.debug("Index is %s", list(metaschema_loader.idx.keys()))
        _logger.debug("Vocabulary is %s", list(metaschema_loader.vocab.keys()))
        return 1
    except (RuntimeError) as e:
        _logger.error(
            "Schema `%s` read error:\n%s",
            args.schema,
            str(e),
            exc_info=(True if args.debug else False),
        )
        return 1

    if args.print_doc:
        makedoc(args)
        return 0

    # Optionally print the schema after ref resolution
    if not args.document and args.print_pre:
        print(json_dumps(schema_doc, indent=4))
        return 0

    if not args.document and args.print_index:
        print(json_dumps(list(metaschema_loader.idx.keys()), indent=4))
        return 0

    # Validate the schema document against the metaschema
    try:
        schema.validate_doc(
            metaschema_names, schema_doc, metaschema_loader, args.strict
        )
    except ValidationException as e:
        _logger.error("While validating schema `%s`:\n%s", args.schema, str(e))
        return 1

    # Get the json-ld context and RDFS representation from the schema
    metactx = schema.collect_namespaces(schema_metadata)
    if "$base" in schema_metadata:
        metactx["@base"] = schema_metadata["$base"]
    if isinstance(schema_doc, CommentedSeq):
        (schema_ctx, rdfs) = jsonld_context.salad_to_jsonld_context(schema_doc, metactx)
    else:
        raise ValidationException(
            "Expected a CommentedSeq, got {}: {}.".format(type(schema_doc), schema_doc)
        )

    # Create the loader that will be used to load the target document.
    document_loader = Loader(schema_ctx, skip_schemas=args.skip_schemas)

    if args.codegen:
        codegen.codegen(
            args.codegen,
            cast(List[Dict[str, Any]], schema_doc),
            schema_metadata,
            document_loader,
            target=args.codegen_target,
            examples=args.codegen_examples,
        )
        return 0

    # Make the Avro validation that will be used to validate the target
    # document
    if isinstance(schema_doc, MutableSequence):
        avsc_obj = schema.make_avro(schema_doc, document_loader)
        try:
            avsc_names = schema.make_avro_schema_from_avro(avsc_obj)
        except SchemaParseException as err:
            _logger.error(
                "Schema `%s` error:\n%s",
                args.schema,
                str(err),
                exc_info=((type(err), err, None) if args.debug else None),
            )
            if args.print_avro:
                print(json_dumps(avsc_obj, indent=4))
            return 1
    else:
        _logger.error("Schema `%s` must be a list.", args.schema)
        return 1

    # Optionally print Avro-compatible schema from schema
    if args.print_avro:
        print(json_dumps(avsc_obj, indent=4))
        return 0

    # Optionally print the json-ld context from the schema
    if args.print_jsonld_context:
        j = {"@context": schema_ctx}
        print(json_dumps(j, indent=4, sort_keys=True))
        return 0

    # Optionally print the RDFS graph from the schema
    if args.print_rdfs:
        print(rdfs.serialize(format=args.rdf_serializer).decode("utf-8"))
        return 0

    if args.print_metadata and not args.document:
        print(json_dumps(schema_metadata, indent=4))
        return 0

    if args.print_inheritance_dot:
        schema.print_inheritance(schema_doc, sys.stdout)
        return 0

    if args.print_fieldrefs_dot:
        schema.print_fieldrefs(schema_doc, document_loader, sys.stdout)
        return 0

    # If no document specified, all done.
    if not args.document:
        print("Schema `{}` is valid".format(args.schema))
        return 0

    # Load target document and resolve refs
    try:
        uri = args.document
        document, doc_metadata = document_loader.resolve_ref(
            uri, strict_foreign_properties=args.strict_foreign_properties
        )
    except ValidationException as e:
        msg = to_one_line_messages(e) if args.print_oneline else str(e)
        _logger.error(
            "Document `%s` failed validation:\n%s",
            args.document,
            msg,
            exc_info=args.debug,
        )
        return 1

    # Optionally print the document after ref resolution
    if args.print_pre:
        print(json_dumps(document, indent=4))
        return 0

    if args.print_index:
        print(json_dumps(list(document_loader.idx.keys()), indent=4))
        return 0

    # Validate the user document against the schema
    try:
        schema.validate_doc(
            avsc_names,
            document,
            document_loader,
            args.strict,
            strict_foreign_properties=args.strict_foreign_properties,
        )
    except ValidationException as e:
        msg2 = to_one_line_messages(e) if args.print_oneline else str(e)
        _logger.error("While validating document `%s`:\n%s" % (args.document, msg2))
        return 1

    # Optionally convert the document to RDF
    if args.print_rdf:
        if isinstance(document, (Mapping, MutableSequence)):
            printrdf(args.document, document, schema_ctx, args.rdf_serializer)
            return 0
        else:
            print("Document must be a dictionary or list.")
            return 1

    if args.print_metadata:
        print(json_dumps(doc_metadata, indent=4))
        return 0

    print("Document `{}` is valid".format(args.document))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
