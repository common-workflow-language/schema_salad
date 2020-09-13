"""
Checks for accepting $schemas directive

run individually as py.test -k tests/test_schemas_directive.py
"""

from typing import Any, Dict, Union, Tuple
from schema_salad.avro.schema import Names, SchemaParseException
from schema_salad.exceptions import ValidationException
from schema_salad.ref_resolver import Loader
from schema_salad.schema import load_and_validate, load_schema
import os
import tarfile
import pathlib
import shutil

from .util import get_data

test_dir_name = "tests/"




class TestCwl11:
    """Ensure codegen-produced parsers accept $schemas directives"""

    document_loader = None  # type: Loader
    avsc_names = None  # type: Union[Names, SchemaParseException]
    schema_metadata = None  # type: Dict[str, Any]
    metaschema_loader = None  # type: Loader

    @classmethod
    def setup_class(cls) -> None:

        #filepath = pathlib.Path(__file__).resolve().parent
        print("here i am {}".format(os.getcwd()))
        #filepath = "schema_salad/tests/test_schema/" #/"+test_dir_name
        filepath = "."
        tf = tarfile.open(os.path.join(filepath,"v1.2.0.tar.gz"))
        tf.extractall(os.path.join(filepath)) #this becomes cwl-v1.2-1.2.0
        path = get_data(os.path.join(filepath,"cwl-v1.2-1.2.0/CommonWorkflowLanguage.yml"))
        assert path
        (
            cls.document_loader,
            cls.avsc_names,
            schema_metadata,
            metaschema_loader,
        ) = load_schema(path)

    @classmethod
    def teardown_class(cls) -> None:
        #filepath = pathlib.Path(__file__).resolve().parent
        filepath = "."
        shutil.rmtree(os.path.join(filepath,"cwl-v1.2-1.2.0/"))

    def load_cwl(self, src: str) -> Tuple[Any, Dict[str, Any]]:
        path = get_data(test_dir_name + src)
        assert path
        assert isinstance(self.avsc_names, Names)
        res = load_and_validate(self.document_loader, self.avsc_names, path, True)
        return res

    def test_secondaryFiles(self) -> None:
        """secondaryFiles"""
        res = self.load_cwl(src="test_real_cwl/bio-cwl-tools/picard_CreateSequenceDictionary.cwl")
        print("the res:{}".format(res))

    def test_outputBinding(self) -> None:
        """secondaryFiles"""
        res = self.load_cwl(src="test_real_cwl/bio-cwl-tools/bamtools_stats.cwl")
        print("the res:{}".format(res))