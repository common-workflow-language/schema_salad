from typing import List

from ._base import BaseDirective as BaseDirective
from ._base import DirectiveParser as DirectiveParser
from ._base import DirectivePlugin as DirectivePlugin
from ._fenced import FencedDirective as FencedDirective
from ._rst import RSTDirective as RSTDirective
from .admonition import Admonition as Admonition
from .image import Figure as Figure
from .image import Image as Image
from .include import Include as Include
from .toc import TableOfContents as TableOfContents

__all__ = [
    "DirectiveParser",
    "BaseDirective",
    "DirectivePlugin",
    "RSTDirective",
    "FencedDirective",
    "Admonition",
    "TableOfContents",
    "Include",
    "Image",
    "Figure",
]

class RstDirective(RSTDirective):
    def __init__(self, plugins: List[DirectivePlugin]) -> None: ...
