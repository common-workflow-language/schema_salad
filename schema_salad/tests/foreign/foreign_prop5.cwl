doc: |
  Foreign properties test.  Should fail with because the property is
  supposed to cross reference another concept node, but that node doesn't
  exist.
cwlVersion: v1.0
$schemas:
  - ../EDAM.owl
$namespaces:
  edam: http://edamontology.org/
class: CommandLineTool
inputs: []
outputs: []
baseCommand: echo
edam:has_topic: abc