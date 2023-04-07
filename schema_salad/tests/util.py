import os
from typing import Optional

from pkg_resources import Requirement, ResolutionError, resource_filename

from schema_salad import ref_resolver


def get_data(filename: str) -> Optional[str]:
    """Get the file path for a given schema file name.

    It is able to find file names in the ``schema_salad`` namespace, but
    also able to load schema files from the ``tests`` directory.
    """
    filename = os.path.normpath(filename)  # normalizing path depending on OS
    # or else it will cause problem when joining path
    filepath = None
    try:
        filepath = resource_filename(Requirement.parse("schema-salad"), filename)
    except ResolutionError:
        pass
    if not filepath or not os.path.isfile(filepath):
        # First try to load it from the local directory, probably ``./tests/``.
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.isfile(filepath):
            # If that didn't work, then default to tests/../${filename},
            # note that we return the parent as it is expected that __file__
            # is a test file.
            filepath = os.path.join(os.path.dirname(__file__), os.pardir, filename)
    return filepath


def get_data_uri(resource_path: str) -> str:
    """Get the file URI for tests."""
    path = get_data(resource_path)
    assert path
    return ref_resolver.file_uri(path)


# Schemas used in tests

cwl_file_uri = get_data_uri("tests/test_schema/CommonWorkflowLanguage.yml")
metaschema_file_uri = get_data_uri("metaschema/metaschema.yml")
basket_file_uri = get_data_uri("tests/basket_schema.yml")
