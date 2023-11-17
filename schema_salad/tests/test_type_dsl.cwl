class: CommandLineTool
cwlVersion: v1.0
baseCommand: python3

inputs: 
  files: 
   type: File?
   default: "script.py"
  other_file: File

outputs:
  hello_output:
    type: File
    outputBinding:
      glob: hello-out.txt  

stdout: hello-out.txt
