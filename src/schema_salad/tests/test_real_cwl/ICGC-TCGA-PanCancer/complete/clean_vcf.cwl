#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool

doc: |
    This tool will clean a VCF for use in the OxoG workflow.

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
    clean_vcf:
      type: File
      outputBinding:
        glob: "*.cleaned.vcf"

baseCommand: /opt/oxog_scripts/clean_vcf.sh
