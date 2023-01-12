#from parser import load_document_by_uri, save
from pathlib import Path
from schema_salad.utils import yaml_no_ts
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from typing import Any, Dict, List, Optional, cast
from schema_salad import codegen
from schema_salad.avro.schema import Names
from schema_salad.schema import load_schema

def test_codegen()->None:
    compare_line_numbers()
    compare_line_numbers()
    compare_line_numbers()

def compare_line_numbers(original_doc:CommentedMap, codegen_doc:CommentedMap)->None:
    assert type(original_doc) == CommentedMap
    assert type(codegen_doc) == CommentedMap

    assert original_doc.lc.line == codegen_doc.lc.line
    assert original_doc.lc.col == codegen_doc.lc.col

    for key, lc_info in original_doc.lc.data.items():
        assert key in codegen_doc.lc.data
        assert lc_info==codegen_doc.lc.data[key]

    max_line = get_max_line_number(original_doc)

    for key, lc_info in codegen_doc.lc.data.items():
        if key in original_doc:
            continue
        assert lc_info == [max_line, 0, max_line, len(key) + 2]
        max_line += 1

def get_max_line_number(original_doc:CommentedMap)->int:
    max_key = ""
    max_line = 0
    temp_doc = original_doc
    while (type(temp_doc) == CommentedMap) and len(temp_doc) > 0:
        for key, lc_info in temp_doc.lc.data.items():
            if lc_info[0] >= max_line:
                max_line = lc_info[0]
                max_key = key
        temp_doc = temp_doc[max_key]
    return max_line + 1

def python_codegen(
    file_uri: str,
    target: Path,
    parser_info: Optional[str] = None,
    package: Optional[str] = None,
) -> None:
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        file_uri
    )
    assert isinstance(avsc_names, Names)
    schema_raw_doc = metaschema_loader.fetch(file_uri)
    schema_doc, schema_metadata = metaschema_loader.resolve_all(
        schema_raw_doc, file_uri
    )
    codegen.codegen(
        "python",
        cast(List[Dict[str, Any]], schema_doc),
        schema_metadata,
        document_loader,
        target=str(target),
        parser_info=parser_info,
        package=package
    )
