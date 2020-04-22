"""
Checks loading of some real world tools and workflows found in the wild (e.g. dockstore)

run individually as py.test -k tests/test_real_cwl.py
"""

import pytest

from schema_salad.schema import load_and_validate, load_schema
from schema_salad.validate import ValidationException

from .util import get_data

test_dir_name = "tests/test_real_cwl/"


class TestRealWorldCWL:
    @classmethod
    def setup_class(cls):
        (
            cls.document_loader,
            cls.avsc_names,
            schema_metadata,
            metaschema_loader,
        ) = load_schema(  # noqa: B950
            get_data("tests/test_schema/CommonWorkflowLanguage.yml")
        )

    def load_cwl(self, src):
        with pytest.raises(ValidationException):
            try:
                load_and_validate(
                    self.document_loader,
                    self.avsc_names,
                    str(get_data(test_dir_name + src)),
                    True,
                )
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
