class: CommandLineTool
cwlVersion: v1.2
baseCommand: python3

inputs: 
  files: 
   type: File
   default: "script.py"
  other_file: File

outputs:
  hello_output:
    type: File
    secondaryFiles: ["inputB.txt", "inputC.txt?"]
    outputBinding:
      glob: hello-out.txt  

stdout: hello-out.txt
