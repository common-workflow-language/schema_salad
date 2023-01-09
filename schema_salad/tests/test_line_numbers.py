#from parser import load_document_by_uri, save
from pathlib import Path
from schema_salad.utils import yaml_no_ts
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from typing import Any, Dict, List, Optional, cast
import schema_salad.metaschema as cg_metaschema
from schema_salad import codegen
from schema_salad.avro.schema import Names
from schema_salad.fetcher import DefaultFetcher
from schema_salad.python_codegen import PythonCodeGen
from schema_salad.python_codegen_support import LoadingOptions
from schema_salad.schema import load_schema
import os



def check_structure(codegen_doc):
    assert type(codegen_doc) == CommentedMap


def compare_comments(original_doc, codegen_doc):
    return None

def compare_line_numbers(original_doc, codegen_doc):
    assert type(original_doc) == CommentedMap
    assert type(codegen_doc) == CommentedMap

    assert original_doc.lc == codegen_doc.lc

    assert original_doc.lc.data == codegen_doc.lc.data

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
        package=package,
    )

if __name__ == "__main__":
    python_codegen('https://github.com/common-workflow-language/common-workflow-language/raw/codegen/v1.0/CommonWorkflowLanguage.yml', 'cwl_v1_0.py')
    assert(os.path.exists('cwl_v1_0.py'))