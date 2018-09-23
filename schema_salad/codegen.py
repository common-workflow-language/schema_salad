"""Generate langauge specific loaders for a particular SALAD schema."""
import sys
from typing import Any, Dict, List, MutableMapping, Optional, Union

from typing_extensions import Text  # pylint: disable=unused-import
# move to a regular typing import when Python 3.3-3.6 is no longer supported

from . import schema
from .codegen_base import CodeGenBase
from .java_codegen import JavaCodeGen
from .python_codegen import PythonCodeGen
from .ref_resolver import Loader  # pylint: disable=unused-import
from .schema import shortname
from .utils import aslist


def codegen(lang,             # type: str
            i,                # type: List[Dict[Text, Any]]
            schema_metadata,  # type: Dict[Text, Any]
            loader            # type: Loader
           ):  # type: (...) -> None
    """Generate classes with loaders for the given Schema Salad description."""

    j = schema.extend_and_specialize(i, loader)

    gen = None  # type: Optional[CodeGenBase]
    if lang == "python":
        gen = PythonCodeGen(sys.stdout)
    elif lang == "java":
        gen = JavaCodeGen(schema_metadata.get("$base", schema_metadata.get("id")))
    else:
        raise Exception("Unsupported code generation language '%s'" % lang)
    assert gen is not None

    gen.prologue()

    document_roots = []

    for rec in j:
        if rec["type"] in ("enum", "record"):
            gen.type_loader(rec)
            gen.add_vocab(shortname(rec["name"]), rec["name"])

    for rec in j:
        if rec["type"] == "enum":
            for symbol in rec["symbols"]:
                gen.add_vocab(shortname(symbol), symbol)

        if rec["type"] == "record":
            if rec.get("documentRoot"):
                document_roots.append(rec["name"])

            field_names = []
            for field in rec.get("fields", []):
                field_names.append(shortname(field["name"]))

            idfield = ""
            for field in rec.get("fields", []):
                if field.get("jsonldPredicate") == "@id":
                    idfield = field.get("name")

            gen.begin_class(rec["name"], aslist(rec.get("extends", [])), rec.get("doc", ""),
                            rec.get("abstract", False), field_names, idfield)
            gen.add_vocab(shortname(rec["name"]), rec["name"])

            for field in rec.get("fields", []):
                if field.get("jsonldPredicate") == "@id":
                    fieldpred = field["name"]
                    optional = bool("https://w3id.org/cwl/salad#null" in field["type"])
                    uri_loader = gen.uri_loader(gen.type_loader(field["type"]), True, False, None)
                    gen.declare_id_field(fieldpred, uri_loader, field.get("doc"), optional)
                    break

            for field in rec.get("fields", []):
                optional = bool("https://w3id.org/cwl/salad#null" in field["type"])
                type_loader = gen.type_loader(field["type"])
                jld = field.get("jsonldPredicate")
                fieldpred = field["name"]
                if isinstance(jld, MutableMapping):
                    ref_scope = jld.get("refScope")

                    if jld.get("typeDSL"):
                        type_loader = gen.typedsl_loader(type_loader, ref_scope)
                    elif jld.get("_type") == "@id":
                        type_loader = gen.uri_loader(type_loader, jld.get("identity", False),
                                                     False, ref_scope)
                    elif jld.get("_type") == "@vocab":
                        type_loader = gen.uri_loader(type_loader, False, True, ref_scope)

                    map_subject = jld.get("mapSubject")
                    if map_subject:
                        type_loader = gen.idmap_loader(
                            field["name"], type_loader, map_subject, jld.get("mapPredicate"))

                    if "_id" in jld and jld["_id"][0] != "@":
                        fieldpred = jld["_id"]

                if jld == "@id":
                    continue

                gen.declare_field(fieldpred, type_loader, field.get("doc"), optional)

            gen.end_class(rec["name"], field_names)

    root_type = list(document_roots)
    root_type.append({
        "type": "array",
        "items": document_roots
    })

    gen.epilogue(gen.type_loader(root_type))
