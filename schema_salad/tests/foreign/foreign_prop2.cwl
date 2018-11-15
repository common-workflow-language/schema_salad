doc: |
  Foreign properties test.  Should pass 'edam' prefix is valid but no
  schema is imported that would all for further checking.
cwlVersion: v1.0
class: CommandLineTool
$namespaces:
  edam: http://edamontology.org/
inputs: []
outputs: []
baseCommand: echo
'edam:has_topic': abc