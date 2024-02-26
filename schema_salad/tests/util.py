"""Shared test functions and attributes."""

import atexit
import os
from contextlib import ExitStack
from pathlib import Path
from typing import Optional

from schema_salad import ref_resolver
from schema_salad.utils import as_file, files


def get_data(filename: str) -> Optional[str]:
    """Get the file path for a given schema file name.

    It is able to find file names in the ``schema_salad`` namespace, but
    also able to load schema files from the ``tests`` directory.
    """
    filename = os.path.normpath(filename)  # normalizing path depending on OS
    # or else it will cause problem when joining path
    filepath = None
    try:
        file_manager = ExitStack()
        atexit.register(file_manager.close)
        traversable = files("schema-salad") / filename
        filepath = file_manager.enter_context(as_file(traversable))
    except ModuleNotFoundError:
        pass
    if not filepath or not os.path.isfile(filepath):
        # First try to load it from the local directory, probably ``./tests/``.
        filepath = Path(os.path.dirname(__file__)) / filename
        if not filepath.is_file():
            # If that didn't work, then default to tests/../${filename},
            # note that we return the parent as it is expected that __file__
            # is a test file.
            filepath = Path(os.path.dirname(__file__)) / ".." / filename
    return str(filepath.resolve())


def get_data_uri(resource_path: str) -> str:
    """Get the file URI for tests."""
    path = get_data(resource_path)
    assert path
    return ref_resolver.file_uri(path)


# Schemas used in tests

cwl_file_uri = get_data_uri("tests/test_schema/CommonWorkflowLanguage.yml")
metaschema_file_uri = get_data_uri("metaschema/metaschema.yml")
basket_file_uri = get_data_uri("tests/basket_schema.yml")
