import os.path
import shutil
import tempfile
from typing import Any, Dict, cast, List, Text

from schema_salad.schema import load_schema
from schema_salad import codegen, ref_resolver
from .util import get_data


def test_cwl_gen():
    file_path = get_data(u"tests/test_schema/CommonWorkflowLanguage.yml")
    topmed_example_path = get_data(
        u"tests/test_real_cwl/topmed/topmed_variant_calling_pipeline.cwl"
    )
    file_uri = ref_resolver.file_uri(file_path)
    test_dir = tempfile.mkdtemp()
    try:
        target_dir = os.path.join(test_dir, "target")
        examples_dir = os.path.join(test_dir, "examples")

        os.mkdir(target_dir)
        os.mkdir(examples_dir)
        shutil.copyfile(
            topmed_example_path, os.path.join(examples_dir, "valid_topmed.cwl")
        )

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
            target=target_dir,
            examples=examples_dir,
        )
        pom_xml_path = os.path.join(target_dir, "pom.xml")
        assert os.path.exists(pom_xml_path)
        tests_dir = os.path.join(
            target_dir, "src", "test", "java", "org", "w3id", "cwl", "cwl", "utils"
        )
        assert os.path.exists(tests_dir)
        with open(os.path.join(tests_dir, "ExamplesTest.java")) as f:
            assert "topmed" in f.read()

    finally:
        shutil.rmtree(test_dir)
