"""
Checks loading of some real world tools and workflows found in the wild (e.g. dockstore)

run individually as py.test -k tests/test_real_cwl.py
"""

from .util import get_data
import unittest
from schema_salad.main import to_one_line_messages, reformat_yaml_exception_message
from schema_salad.schema import load_schema, load_and_validate
from schema_salad.sourceline import strip_dup_lineno
from schema_salad.validate import ValidationException
from os.path import normpath
import re
import six

test_dir_name = "tests/test_real_cwl/"


class TestRealWorldCWL(unittest.TestCase):
    def setUp(self):
        self.document_loader, self.avsc_names, schema_metadata, metaschema_loader = \
            load_schema(get_data(u"tests/test_schema/CommonWorkflowLanguage.yml"))

    def load_cwl(self, src):
        with self.assertRaises(ValidationException):
            try:
                load_and_validate(self.document_loader, self.avsc_names,
                                  six.text_type(get_data(test_dir_name+src)), True)
            except ValidationException as e:
                # msgs = to_one_line_messages(str(e)).splitlines()
                print("\n", e)
                raise

    def test_topmed_single_doc(self):
        # TOPMed Variant Calling Pipeline CWL1
        self.load_cwl(src="topmed/topmed_variant_calling_pipeline.cwl")

    def test_h3agatk_WES(self):
        # H3ABioNet GATK Germline Workflow
        self.load_cwl(src="h3agatk/GATK-complete-WES-Workflow-h3abionet.cwl")

    def test_h3agatk_SNP(self):
        # H3ABioNet SNPs Workflow
        self.load_cwl(src="h3agatk/GATK-Sub-Workflow-h3abionet-snp.cwl")

    def test_icgc_pancan(self):
        # ICGC PanCan
        self.load_cwl(src="ICGC-TCGA-PanCancer/preprocess_vcf.cwl")
