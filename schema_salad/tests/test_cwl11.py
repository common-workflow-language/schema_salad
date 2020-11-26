"""
Ensure codegen-produced parsers accept $schemas directives

run individually as py.test -k test_cwl11
"""

import os
import shutil
import tarfile
from typing import Any, Dict, Generator, Tuple, Union

import pytest
import requests
from _pytest.tmpdir import TempPathFactory

from schema_salad.avro.schema import Names, SchemaParseException
from schema_salad.ref_resolver import Loader
from schema_salad.schema import load_and_validate, load_schema

from .util import get_data

test_dir_name = "tests/"

SchemaType = Tuple[Loader, Union[Names, SchemaParseException], Dict[str, Any], Loader]


@pytest.fixture(scope="session")
def cwl_v1_2_schema(
    tmp_path_factory: TempPathFactory,
) -> Generator[SchemaType, None, None]:
    tmp_path = tmp_path_factory.mktemp("cwl_v1_2_schema")
    with requests.get(
        "https://github.com/common-workflow-language/cwl-v1.2/archive/v1.2.0.tar.gz",
        stream=True,
    ).raw as specfileobj:
        tf = tarfile.open(fileobj=specfileobj)
        tf.extractall(path=tmp_path)  # this becomes cwl-v1.2-1.2.0
    path = str(tmp_path / "cwl-v1.2-1.2.0/CommonWorkflowLanguage.yml")
    yield load_schema(path)
    shutil.rmtree(os.path.join(tmp_path))


def load_cwl(cwl_v1_2_schema: SchemaType, src: str) -> Tuple[Any, Dict[str, Any]]:
    (document_loader, avsc_names, schema_metadata, metaschema_loader) = cwl_v1_2_schema
    path = get_data(test_dir_name + src)
    assert path
    assert isinstance(avsc_names, Names)
    res = load_and_validate(document_loader, avsc_names, path, True)
    return res


def test_secondaryFiles(cwl_v1_2_schema: SchemaType) -> None:
    """secondaryFiles"""
    res = load_cwl(
        cwl_v1_2_schema,
        src="test_real_cwl/bio-cwl-tools/picard_CreateSequenceDictionary.cwl",
    )
    print(f"the res:{res}")


def test_outputBinding(cwl_v1_2_schema: SchemaType) -> None:
    """secondaryFiles"""
    res = load_cwl(
        cwl_v1_2_schema, src="test_real_cwl/bio-cwl-tools/bamtools_stats.cwl"
    )
    print(f"the res:{res}")
