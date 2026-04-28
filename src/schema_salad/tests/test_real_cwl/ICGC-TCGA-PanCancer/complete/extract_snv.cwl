#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool

doc: |
    This tool will extract SNVs from INDEL VCFs

$namespaces:
 s: https://schema.org/

$schemas:
 - https://schema.org/version/latest/schemaorg-current-https.rdf

s:author:
    s:name: "Solomon Shorser"
    s:email: "solomon.shorser@oicr.on.ca"

requirements:
  - class: DockerRequirement
    dockerPull: quay.io/pancancer/pcawg-oxog-tools

inputs:
    - id: "#vcf"
      type: File
      inputBinding:
        position: 1

outputs:
    extracted_snvs:
      type: File?
      outputBinding:
        glob: "*.extracted-SNVs.vcf.gz"

baseCommand: /opt/oxog_scripts/extract_snvs_from_indels.sh
