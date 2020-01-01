"""Salad is a schema language for describing JSON or YAML structured linked data documents"""

import logging

__author__ = "peter.amstutz@curoverse.com"

_logger = logging.getLogger("salad")
_logger.addHandler(logging.StreamHandler())
_logger.setLevel(logging.INFO)
