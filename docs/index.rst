############################################################################
Schema language for describing JSON or YAML structured linked data documents
############################################################################

Salad is a schema language for describing JSON or YAML structured
linked data documents.  Salad schema describes rules for
preprocessing, structural validation, and hyperlink checking for
documents described by a Salad schema. Salad supports rich data
modeling with inheritance, template specialization, object
identifiers, object references, documentation generation, code
generation, and transformation to RDF_. Salad provides a bridge
between document and record oriented data modeling and the Semantic
Web.

Modules
=======

.. toctree::
   :maxdepth: 2

Command Line Options
====================

.. autoprogram:: schema_salad.main:arg_parser()
   :prog: schema-salad-tool

.. autoprogram:: schema_salad.makedoc:arg_parser()
   :prog: schema-salad-doc

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _RDF: https://www.w3.org/RDF/
