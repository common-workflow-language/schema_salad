# from parser import load_document_by_uri, save
from pathlib import Path
from typing import MutableSequence, Optional, cast, Any
from urllib.parse import unquote_plus, urlparse

import schema_salad.tests.cwl_v1_2 as cwl_v1_2
from schema_salad.utils import yaml_no_ts
from ruamel.yaml.comments import CommentedMap

from .util import get_data


def test_secondary_files_dsl() -> None:
    """
    Checks object is properly saving when dsl is used
    """
    t = "test_schema/test_secondary_files_dsl.cwl"
    path = get_data("tests/" + t)
    obj = load_document_by_uri(str(path))
    saved_obj = obj.save()
    assert isinstance(saved_obj, CommentedMap)
    assert saved_obj.lc.data == {'cwlVersion': [1, 0, 1, 12],
                                 'baseCommand': [2, 0, 2, 13],
                                 'inputs': [4, 0, 5, 2],
                                 'outputs': [10, 0, 11, 2],
                                 'stdout': [19, 0, 21, 8],
                                 'id': [20, 0, 20, 4]
                                 }
    assert saved_obj['inputs'][0].lc.data == {'type': [6, 3, 6, 9],
                                              'default': [7, 3, 7, 12],
                                              'id': [5, 2, 5, 6]
                                              }
    assert saved_obj['inputs'][0]['type'] == 'File'
    assert saved_obj['inputs'][1].lc.data == {'id': [8, 2, 8, 6], 'type': [9, 2, 9, 8]}
    assert saved_obj['outputs'][0].lc.data == {'type': [12, 4, 12, 10],
                                               'secondaryFiles': [16, 4, 19, 20],
                                               'outputBinding': [18, 4, 21, 6],
                                               'id': [11, 2, 11, 6]
                                               }
    assert saved_obj["outputs"][0]['secondaryFiles'][0].lc.data == {'pattern': [13, 35, 13, 44]}
    assert saved_obj["outputs"][0]['secondaryFiles'][1].lc.data == {'pattern': [14, 35, 14, 44],
                                                                    'required': [15, 35, 15, 45]
                                                                    }

    cwl_v1_2.inserted_line_info = {}


def test_outputs_before_inputs() -> None:
    """
    Tests when output comes in cwl file before inputs
    """
    t = "test_schema/test_outputs_before_inputs.cwl"
    path = get_data("tests/" + t)
    obj = load_document_by_uri(str(path))
    saved_obj = obj.save()
    assert isinstance(saved_obj, CommentedMap)
    assert saved_obj.lc.data == {'cwlVersion': [1, 0, 1, 12],
                                 'baseCommand': [2, 0, 2, 13],
                                 'outputs': [4, 0, 5, 2],
                                 'inputs': [10, 0, 11, 2],
                                 'stdout': [16, 0, 16, 8],
                                 'id': [17, 0, 17, 4]
                                 }
    assert saved_obj['inputs'][0].lc.data == {'type': [12, 3, 12, 9],
                                              'default': [13, 3, 13, 12],
                                              'id': [11, 2, 11, 6]
                                              }
    assert saved_obj['inputs'][0]['type'] == 'File'
    assert saved_obj['inputs'][1].lc.data == {'id': [14, 2, 14, 6], 'type': [15, 2, 15, 8]}
    assert saved_obj['outputs'][0].lc.data == {'type': [6, 4, 6, 10],
                                               'outputBinding': [7, 4, 8, 6],
                                               'id': [5, 2, 5, 6]
                                               }
    cwl_v1_2.inserted_line_info = {}


def test_type_dsl() -> None:
    """
    Checks object is properly saving when type DSL is used.
    In this example, type for the input is File? which should expand to
    null, File.
    """
    t = "test_schema/test_type_dsl.cwl"
    path = get_data("tests/" + t)
    obj = load_document_by_uri(str(path))
    saved_obj = obj.save()
    assert isinstance(saved_obj, CommentedMap)
    assert saved_obj.lc.data == {'cwlVersion': [1, 0, 1, 12],
                                 'baseCommand': [2, 0, 2, 13],
                                 'inputs': [4, 0, 5, 2],
                                 'outputs': [10, 0, 11, 2],
                                 'stdout': [16, 0, 16, 8],
                                 'id': [17, 0, 17, 4]
                                 }
    assert saved_obj['inputs'][0].lc.data == {'type': [6, 3, 6, 9],
                                              'default': [7, 3, 7, 12],
                                              'id': [5, 2, 5, 6]
                                              }
    assert saved_obj['inputs'][0]['type'] == ['null', 'File']
    assert saved_obj['inputs'][1].lc.data == {'id': [8, 2, 8, 6],
                                              'type': [9, 2, 9, 8]
                                              }
    assert saved_obj['outputs'][0].lc.data == {'type': [12, 4, 12, 10],
                                               'outputBinding': [13, 4, 14, 6],
                                               'id': [11, 2, 11, 6]
                                               }
    assert saved_obj["outputs"][0]['outputBinding'].lc.data == {'glob': [14, 6, 14, 12]}


def load_document_by_uri(path: str) -> Any:
    """
    Takes in a path and loads it via the python codegen.
    """
    if isinstance(path, str):
        uri = urlparse(path)
        if not uri.scheme or uri.scheme == "file":
            real_path = Path(unquote_plus(uri.path)).resolve().as_uri()
        else:
            real_path = path
    else:
        real_path = path.resolve().as_uri()

    baseuri = str(real_path)

    loadingOptions = cwl_v1_2.LoadingOptions(fileuri=baseuri)

    doc = loadingOptions.fetcher.fetch_text(real_path)

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
