import os
from typing import Optional, Text

from pkg_resources import Requirement, ResolutionError, resource_filename


def get_data(filename):  # type: (Text) -> Optional[Text]
    filename = os.path.normpath(filename)  # normalizing path depending on OS
    # or else it will cause problem when joining path
    filepath = None
    try:
        filepath = resource_filename(Requirement.parse("schema-salad"), filename)
    except ResolutionError:
        pass
    if not filepath or not os.path.isfile(filepath):
        filepath = os.path.join(os.path.dirname(__file__), os.pardir, filename)
    return filepath
