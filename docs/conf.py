# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from schema_salad import _version

# -- Project information -----------------------------------------------------

project = 'Schema Salad'
copyright = '2019, Peter Amstutz and contributors'
author = 'Peter Amstutz and contributors'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
        "sphinx.ext.autodoc",
        "sphinx.ext.autosummary",
        "sphinx.ext.inheritance_diagram",
        "autoapi.extension",
        "sphinx_autodoc_typehints",
        "sphinx_rtd_theme",
        "sphinxcontrib.autoprogram"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']


version = _version.version

autoapi_dirs = ['../schema_salad']
autodoc_typehints = 'description'
autoapi_keep_files = True
autoapi_ignore = ['*migrations*', '*.pyi']
autoapi_options = [ 'members', 'undoc-members', 'show-inheritance', 'show-inheritance-diagram', 'show-module-summary', 'imported-members', 'special-members' ]
#sphinx-autodoc-typehints
always_document_param_types = True
# If False, do not add type info for undocumented parameters.
# If True, add stub documentation for undocumented parameters to be able to add type info.

