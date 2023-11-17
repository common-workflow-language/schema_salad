class: CommandLineTool
cwlVersion: v1.0
baseCommand: python3

outputs:
  hello_output:
    type: File
    outputBinding:
      glob: hello-out.txt  

inputs: 
  files: 
   type: File
   default: "script.py"
  other_file: File

stdout: hello-out.txt