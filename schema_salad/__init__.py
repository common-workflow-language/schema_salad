from __future__ import absolute_import
import logging
import os
import sys
import typing
import threading

import six

from .utils import onWindows
__author__ = 'peter.amstutz@curoverse.com'

_logger = logging.getLogger("salad")
_logger.addHandler(logging.StreamHandler())
_logger.setLevel(logging.INFO)
