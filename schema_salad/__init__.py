"""A schema language for describing JSON or YAML structured linked data documents."""

import logging
import sys
import warnings

__author__ = "peter.amstutz@curoverse.com"

_logger = logging.getLogger("salad")
_logger.addHandler(logging.StreamHandler())
_logger.setLevel(logging.INFO)

if sys.version_info < (3, 7):
    warnings.filterwarnings("ignore", message="urllib3.*", module="requests")
