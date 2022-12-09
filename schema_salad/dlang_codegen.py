"""D code generator for a given schema salad definition."""

import datetime
import textwrap
from typing import IO, Any, Dict, List, Optional, Tuple, Union, cast

from . import _logger, schema
from .codegen_base import CodeGenBase, TypeDef
from .cpp_codegen import isArray, isEnumSchema, isRecordSchema, pred
from .exceptions import SchemaException
from .schema import shortname


class DlangCodeGen(CodeGenBase):
    """Generation of D code for a given Schema Salad definition."""

    def __init__(
        self,
        base: str,
        target: IO[str],
        examples: Optional[str],
        package: str,
        copyright_: Optional[str],
        parser_info: Optional[str],
    ) -> None:
        """Initialize the D codegen."""
        super().__init__()
        self.base_uri = base
        self.examples = examples
        self.target = target
        self.package = package
        self.copyright = copyright_
        self.parser_info = parser_info
        self.doc_root_types: List[str] = []

    def prologue(self) -> None:
        """Trigger to generate the prolouge code."""

        module_comment = []

        if self.parser_info:
            module_comment.append(self.parser_info + "\n")

        module_comment += [
            "This module was generated using schema-salad code generator.",
            "",
            "The embedded document is subject to the license of the original schema.",
        ]

        if self.copyright:
            module_comment.append(f"The original schema is {self.copyright}.")

        module_comment += [
            "",
            "License: Apache-2.0",
            f"Date: {datetime.date.today().isoformat()}",
        ]

        self.target.write(self.to_doc_comment(module_comment))
        self.target.write(
            f"""module {self.package};

import salad.meta.dumper : genDumper;
import salad.meta.impl : genCtor, genIdentifier, genOpEq;
import salad.meta.parser : import_ = importFromURI;
import salad.meta.uda : documentRoot, id, idMap, link, LinkResolver, secondaryFilesDSL, typeDSL;
import salad.primitives : SchemaBase;
import salad.type : None, Either;

"""
        )
        if self.parser_info:
            self.target.write(
                f"""/// parser information
enum parserInfo = "{self.parser_info}";
"""
            )

    def epilogue(self, root_loader: TypeDef) -> None:
        """Trigger to generate the epilouge code."""
        doc_root_type_str = ", ".join(self.doc_root_types)
        doc_root_type = f"Either!({doc_root_type_str})"
        self.target.write(
            f"""
///
alias DocumentRootType = {doc_root_type};

///
alias importFromURI = import_!DocumentRootType;
"""
        )
        if self.examples:
            self.target.write(
                f"""
@("Test for generated parser")
unittest
{{
    import std : dirEntries, SpanMode;

    auto resourceDir = "{self.examples}";
    foreach (file; dirEntries(resourceDir, SpanMode.depth))
    {{
        import std : assertNotThrown, baseName, format, startsWith;
        import salad.resolver : absoluteURI;

        if (!file.baseName.startsWith("valid"))
        {{
            continue;
        }}
        importFromURI(file.absoluteURI).assertNotThrown(format!"Failed to load %s"(file));
    }}
}}
"""
            )

    @staticmethod
    def safe_name(name: str) -> str:
        """Generate a safe version of the given name."""
        avn = schema.avro_field_name(name)
        if avn in ("class", "abstract", "default", "package"):
            # reserved words
            avn = avn + "_"
        if avn and avn.startswith("anon."):
            avn = avn[5:]
        return avn

    def to_doc_comment(self, doc: Union[None, str, List[str]]) -> str:
        """Return an embedded documentation comments for a given string."""
        if doc is None:
            return "///\n"
        if isinstance(doc, str):
            lines = doc.split("\n")
        else:
            lines = sum((d.split("\n") for d in doc), [])

        if not lines[-1]:
            lines = lines[0:-1]

        lines = [
            line.replace("`(`", "`$(LPAREN)`").replace("`)`", "`$(RPAREN)`")
            for line in lines
        ]

        doc_lines = "\n".join((f" * {line}" for line in lines))

        return f"""/**
{doc_lines}
 */
"""

    def parse_record_field_type(
        self, type_: Any, jsonld_pred: Union[None, str, Dict[str, Any]]
    ) -> Tuple[str, str]:
        """Return an annotation string and a type string."""
        annotations: List[str] = []
        if isinstance(jsonld_pred, str):
            if jsonld_pred == "@id":
                annotations.append("@id")
        elif isinstance(jsonld_pred, dict):
            if jsonld_pred.get("typeDSL", False):
                annotations.append("@typeDSL")
            if jsonld_pred.get("secondaryFilesDSL", False):
                annotations.append("@secondaryFilesDSL")
            if "mapSubject" in jsonld_pred:
                subject = jsonld_pred["mapSubject"]
                if "mapPredicate" in jsonld_pred:
                    predicate = jsonld_pred["mapPredicate"]
                    annotations.append(f'@idMap("{subject}", "{predicate}")')
                else:
                    annotations.append(f'@idMap("{subject}")')
            if jsonld_pred.get("_type", "") == "@id":
                if jsonld_pred.get("identity", False):
                    annotations.append("@link(LinkResolver.id)")
                else:
                    annotations.append("@link()")
        if annotations:
            annotate_str = " ".join(annotations) + " "
        else:
            annotate_str = ""

        if isinstance(type_, str):
            stype = shortname(type_)
            if stype == "boolean":
                type_str = "bool"
            elif stype == "null":
                type_str = "None"
            else:
                type_str = stype
        elif isinstance(type_, list):
            t_str = [self.parse_record_field_type(t, None)[1] for t in type_]
            union_types = ", ".join(t_str)
            type_str = f"Either!({union_types})"
        elif shortname(type_["type"]) == "array":
            item_type = self.parse_record_field_type(type_["items"], None)[1]
            type_str = f"{item_type}[]"
        elif shortname(type_["type"]) == "record":
            return annotate_str, shortname(type_.get("name", "record"))
        elif shortname(type_["type"]) == "enum":
            return annotate_str, "'not yet implemented'"
        return annotate_str, type_str

    def parse_record_field(
        self, field: Dict[str, Any], parent_name: Optional[str] = None
    ) -> str:
        """Return a declaration string for a given record field."""
        fname = shortname(field["name"]) + "_"
        jsonld_pred = field.get("jsonldPredicate", None)
        doc_comment = self.to_doc_comment(field.get("doc", None))
        type_ = field["type"]
        if (
            (
                (isinstance(type_, dict) and shortname(type_.get("type", "")) == "enum")
                or (isinstance(type_, str) and shortname(type_) == "string")
            )
            and isinstance(jsonld_pred, dict)
            and (
                shortname(jsonld_pred.get("_id", "")) == "type"
                or shortname(jsonld_pred.get("_id", "")) == "@type"
            )
            and jsonld_pred.get("_type", "") == "@vocab"
        ):
            # special case
            if isinstance(type_, dict):
                # assert len(type["symbols"]) == 1
                value = shortname(type_["symbols"][0])
            else:
                value = cast(str, parent_name)
            return f'{doc_comment}static immutable {fname} = "{value}";'

        annotate_str, type_str = self.parse_record_field_type(type_, jsonld_pred)
        return f"{doc_comment}{annotate_str}{type_str} {fname};"

    def parse_record_schema(self, stype: Dict[str, Any]) -> str:
        """Return a declaration string for a given record schema."""
        name = cast(str, stype["name"])
        classname = self.safe_name(name)

        field_decls = []
        if "fields" in stype:
            for field in stype["fields"]:
                field_decls.append(self.parse_record_field(field, classname))
        decl_str = "\n".join((textwrap.indent(f"{d}", " " * 4) for d in field_decls))

        if stype.get("documentRoot", False):
            doc_root_annotation = "@documentRoot "
            self.doc_root_types.append(classname)
        else:
            doc_root_annotation = ""

        doc_comment = self.to_doc_comment(stype.get("doc", None))

        return f"""
{doc_comment}{doc_root_annotation}class {classname} : SchemaBase
{{
{decl_str}

    mixin genCtor;
    mixin genIdentifier;
    mixin genDumper;
}}"""

    def parse_enum(self, stype: Dict[str, Any]) -> str:
        """Return a declaration string for a given enum schema."""
        name = cast(str, stype["name"])
        if shortname(name) == "Any":
            return "\n///\npublic import salad.primitives : Any;"
        if shortname(name) == "Expression":
            return "\n///\npublic import salad.primitives : Expression;"

        classname = self.safe_name(name)
        syms = "\n".join(
            (
                f'        s{i} = "{shortname(sym)}", ///'
                for i, sym in enumerate(stype["symbols"])
            )
        )

        if stype.get("documentRoot", False):
            doc_root_annotation = "@documentRoot "
            self.doc_root_types.append(classname)
        else:
            doc_root_annotation = ""

        if "doc" in stype:
            doc_comment = self.to_doc_comment(stype["doc"])
        else:
            doc_comment = ""

        return f"""
{doc_comment}{doc_root_annotation}class {classname} : SchemaBase
{{
    ///
    enum Symbol
    {{
{syms}
    }}

    Symbol value;

    mixin genCtor;
    mixin genOpEq;
    mixin genDumper;
}}"""

    def parse(self, items: List[Dict[str, Any]]) -> None:
        """Generate D code from items and write it to target."""
        dlang_defs = []

        self.prologue()

        for stype in items:
            if "type" in stype and stype["type"] == "documentation":
                continue

            if not (pred(stype) or isArray(stype)):
                raise SchemaException("not a valid SaladRecordField")

            # parsing a record
            if isRecordSchema(stype):
                if stype.get("abstract", False):
                    continue
                dlang_defs.append(self.parse_record_schema(stype))
            elif isEnumSchema(stype):
                dlang_defs.append(self.parse_enum(stype))
            else:
                _logger.error("not parsed %s", stype)

        self.target.write("\n".join(dlang_defs))
        self.target.write("\n")

        self.epilogue(TypeDef("dummy", "data"))

        self.target.close()
