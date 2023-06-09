# from parser import load_document_by_uri, save
from pathlib import Path
from typing import Any, MutableSequence, Optional, cast
from urllib.parse import unquote_plus, urlparse

from ruamel.yaml.comments import CommentedMap

import schema_salad.tests.cwl_v1_2 as cwl_v1_2
from schema_salad.utils import yaml_no_ts

from .util import get_data


def test_secondary_files_dsl() -> None:
    """
    Checks object is properly saving when dsl is used
    """
    t = "test_secondary_files_dsl.cwl"
    path = get_data("tests/" + t)
    obj = load_document_by_uri(str(path))
    saved_obj = obj.save()
    assert isinstance(saved_obj, CommentedMap)
    assert saved_obj.lc.data == {
        "cwlVersion": [1, 0, 1, 12],
        "baseCommand": [2, 0, 2, 13],
        "inputs": [4, 0, 5, 2],
        "outputs": [15, 0, 16, 2],
        "stdout": [25, 0, 25, 8],
        "id": [26, 0, 26, 4],
    }
    assert saved_obj["inputs"][0].lc.data == {
        "type": [6, 3, 6, 9],
        "secondaryFiles": [10, 3, 13, 19],
        "default": [11, 3, 11, 12],
        "id": [12, 3, 12, 7],
    }
    assert saved_obj["inputs"][0]["type"] == "File"
    assert saved_obj["inputs"][1].lc.data == {"id": [13, 2, 13, 6], "type": [14, 2, 14, 8]}
    assert saved_obj["outputs"][0].lc.data == {
        "type": [17, 4, 17, 10],
        "secondaryFiles": [21, 4, 28, 20],
        "outputBinding": [22, 4, 23, 6],
        "id": [24, 4, 24, 8],
    }
    assert saved_obj["outputs"][0]["secondaryFiles"][0].lc.data == {"pattern": [18, 21, 18, 30]}
    assert saved_obj["outputs"][0]["secondaryFiles"][1].lc.data == {
        "pattern": [19, 35, 19, 44],
        "required": [20, 35, 20, 45],
    }


def test_outputs_before_inputs() -> None:
    """
    Tests when output comes in cwl file before inputs
    """
    t = "test_outputs_before_inputs.cwl"
    path = get_data("tests/" + t)
    obj = load_document_by_uri(str(path))
    saved_obj = obj.save()
    assert isinstance(saved_obj, CommentedMap)
    assert {
        "cwlVersion": [1, 0, 1, 12],
        "baseCommand": [2, 0, 2, 13],
        "outputs": [4, 0, 5, 2],
        "inputs": [10, 0, 11, 2],
        "stdout": [17, 0, 17, 8],
        "id": [18, 0, 18, 4],
    }
    assert saved_obj["inputs"][0].lc.data == {
        "type": [12, 3, 12, 9],
        "default": [13, 3, 13, 12],
        "id": [14, 3, 14, 7],
    }
    assert saved_obj["inputs"][0]["type"] == "File"
    assert saved_obj["inputs"][1].lc.data == {"id": [15, 2, 15, 6], "type": [16, 2, 16, 8]}
    assert saved_obj["outputs"][0].lc.data == {
        "type": [6, 4, 6, 10],
        "outputBinding": [7, 4, 8, 6],
        "id": [9, 4, 9, 8],
    }


def test_type_dsl() -> None:
    """
    Checks object is properly saving when type DSL is used.
    In this example, type for the input is File? which should expand to
    null, File.
    """
    t = "test_type_dsl.cwl"
    path = get_data("tests/" + t)
    obj = load_document_by_uri(str(path))
    saved_obj = obj.save()
    assert isinstance(saved_obj, CommentedMap)
    assert {
        "cwlVersion": [1, 0, 1, 12],
        "baseCommand": [2, 0, 2, 13],
        "inputs": [4, 0, 5, 2],
        "outputs": [11, 0, 12, 2],
        "stdout": [17, 0, 17, 8],
        "id": [18, 0, 18, 4],
    }
    assert saved_obj["inputs"][0].lc.data == {
        "type": [6, 3, 6, 9],
        "default": [7, 3, 7, 12],
        "id": [8, 3, 8, 7],
    }
    assert saved_obj["inputs"][0]["type"] == ["null", "File"]
    assert saved_obj["inputs"][1].lc.data == {"id": [9, 2, 9, 6], "type": [10, 2, 10, 8]}
    assert saved_obj["outputs"][0].lc.data == {
        "type": [13, 4, 13, 10],
        "outputBinding": [14, 4, 15, 6],
        "id": [16, 4, 16, 8],
    }
    assert saved_obj["outputs"][0]["outputBinding"].lc.data == {"glob": [15, 6, 15, 12]}


def load_document_by_uri(path: str) -> Any:
    """
    Takes in a path and loads it via the python codegen.
    """
    uri = urlparse(path)
    if not uri.scheme or uri.scheme == "file":
        real_path = Path(unquote_plus(uri.path)).resolve().as_uri()
    else:
        real_path = path

    baseuri = str(real_path)

    loadingOptions = cwl_v1_2.LoadingOptions(fileuri=baseuri)
    # doc = loadingOptions.fetcher.fetch_text(real_path)
    with open(path, 'r') as file:
        doc = file.read()

    yaml = yaml_no_ts()
    doc = yaml.load(doc)

    result = cwl_v1_2.load_document_by_yaml(
        doc, baseuri, cast(Optional[cwl_v1_2.LoadingOptions], loadingOptions)
    )

    if isinstance(result, MutableSequence):
        lst = []
        for r in result:
            lst.append(r)
        return lst
    return result
