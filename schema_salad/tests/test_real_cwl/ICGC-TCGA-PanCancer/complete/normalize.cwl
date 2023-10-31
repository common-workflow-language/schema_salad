#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool

doc: |
    This tool will normalize an INDEL VCF using bcf-tools norm.

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
    - id: "#ref"
      type: File
      inputBinding:
        position: 2
      secondaryFiles:
        - .fai


outputs:
    - id: "#normalized-vcf"
      type: File
      outputBinding:
        glob: "*.normalized.vcf.gz"

baseCommand: /opt/oxog_scripts/normalize.sh
