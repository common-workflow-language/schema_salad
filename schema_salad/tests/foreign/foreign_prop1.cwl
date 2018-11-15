doc: |
  Foreign properties test case. Should pass with a warning about
  unrecognized prefix 'edam'
cwlVersion: v1.0
class: CommandLineTool
inputs: []
outputs: []
baseCommand: echo
'edam:has_topic': abc