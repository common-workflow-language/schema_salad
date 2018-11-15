doc: |
  Foreign properties test.  Should pass with a warning because the
  property is not valid in the ontology.
cwlVersion: v1.0
$schemas:
  - ../EDAM.owl
$namespaces:
  edam: http://edamontology.org/
class: CommandLineTool
inputs: []
outputs: []
baseCommand: echo
'edam:fake_property': abc