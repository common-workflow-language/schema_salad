"""Test schema-salad makedoc"""

from io import StringIO

from schema_salad.makedoc import makedoc

from .util import get_data


def test_schema_salad_inherit_docs() -> None:
    """Test schema-salad-doc when types inherit and override values from parent types."""
    schema_path = get_data("tests/inherited-attributes.yml")
    assert schema_path
    stdout = StringIO()
    makedoc(stdout, schema_path)

    # The parent ID documentation (i.e. Parent ID) must appear exactly once.
    assert 1 == stdout.getvalue().count("Parent ID")
