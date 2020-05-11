import contextlib
import os.path
import shutil
import tempfile
from typing import Any, Dict, Iterator, List, Optional, Text, cast

from schema_salad import codegen, ref_resolver
from schema_salad.schema import load_schema

from .util import get_data


def test_cwl_gen() -> None:
    topmed_example_path = get_data(
        "tests/test_real_cwl/topmed/topmed_variant_calling_pipeline.cwl"
    )
    assert topmed_example_path
    with t_directory() as test_dir:
        target_dir = os.path.join(test_dir, "target")
        examples_dir = os.path.join(test_dir, "examples")

        os.mkdir(target_dir)
        os.mkdir(examples_dir)
        shutil.copyfile(
            topmed_example_path, os.path.join(examples_dir, "valid_topmed.cwl")
        )

        java_codegen(cwl_file_uri, target_dir, examples=examples_dir)
        pom_xml_path = os.path.join(target_dir, "pom.xml")
        assert os.path.exists(pom_xml_path)
        tests_dir = os.path.join(
            target_dir, "src", "test", "java", "org", "w3id", "cwl", "cwl", "utils"
        )
        assert os.path.exists(tests_dir)
        with open(os.path.join(tests_dir, "ExamplesTest.java")) as f:
            assert "topmed" in f.read()


def test_meta_schema_gen() -> None:
    with t_directory() as test_dir:
        target_dir = os.path.join(test_dir, "target")
        os.mkdir(target_dir)
        java_codegen(metaschema_file_uri, target_dir)
        pom_xml_path = os.path.join(target_dir, "pom.xml")
        assert os.path.exists(pom_xml_path)
        src_dir = os.path.join(
            target_dir, "src", "main", "java", "org", "w3id", "cwl", "salad"
        )
        assert os.path.exists(src_dir)


@contextlib.contextmanager
def t_directory() -> Iterator[str]:
    test_dir = tempfile.mkdtemp()
    try:
        yield test_dir
    finally:
        shutil.rmtree(test_dir)


def get_data_uri(resource_path: str) -> str:
    path = get_data(resource_path)
    assert path
    return ref_resolver.file_uri(path)


cwl_file_uri = get_data_uri("tests/test_schema/CommonWorkflowLanguage.yml")
metaschema_file_uri = get_data_uri("metaschema/metaschema.yml")


def java_codegen(file_uri: str, target: str, examples: Optional[str] = None) -> None:
    document_loader, avsc_names, schema_metadata, metaschema_loader = load_schema(
        file_uri
    )
    schema_raw_doc = metaschema_loader.fetch(file_uri)
    schema_doc, schema_metadata = metaschema_loader.resolve_all(
        schema_raw_doc, file_uri
    )
    codegen.codegen(
        "java",
        cast(List[Dict[Text, Any]], schema_doc),
        schema_metadata,
        document_loader,
        target=target,
        examples=examples,
    )
