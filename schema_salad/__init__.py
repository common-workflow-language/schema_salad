from __future__ import absolute_import
import logging
import os
import sys
import typing
from .utils import onWindows
__author__ = 'peter.amstutz@curoverse.com'

_logger = logging.getLogger("salad")
_logger.addHandler(logging.StreamHandler())
_logger.setLevel(logging.INFO)

import six
if six.PY3:

    if onWindows:
        # create '/tmp' folder if not present
        # required by autotranslate module
        if not os.path.exists("/tmp"):
            try:
                os.mkdirs("/tmp")
            except OSError as exception:
                exit(0)

    from past import autotranslate  # type: ignore
    autotranslate(['avro', 'avro.schema'])
