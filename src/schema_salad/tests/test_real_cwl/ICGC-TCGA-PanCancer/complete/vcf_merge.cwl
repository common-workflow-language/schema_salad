#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool
id: "merge_vcfs"
label: "merge_vcfs"

doc: |
    This tool will merge VCFs by type (SV, SNV, INDEL). This CWL wrapper was written by Solomon Shorser.
    The Perl script was originaly written by Brian O'Connor and maintained by Solomon Shorser.

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
  - class: InlineJavascriptRequirement
    expressionLib:
      - { $include: vcf_merge_util.js }

inputs:
    - id: "#broad_snv"
      type: File[]

    - id: "#sanger_snv"
      type: File[]

    - id: "#de_snv"
      type: File[]

    - id: "#muse_snv"
      type: File[]

    - id: "#broad_sv"
      type: File[]

    - id: "#sanger_sv"
      type: File[]

    - id: "#de_sv"
      type: File[]

    - id: "#broad_indel"
      type: File[]

    - id: "#sanger_indel"
      type: File[]

    - id: "#de_indel"
      type: File[]

    - id: "#smufin_indel"
      type: File[]

    - id: "#out_dir"
      type: string
      inputBinding:
        position: 12
        prefix: --outdir
outputs:
    output:
      type:
        type: array
        items: File
      outputBinding:
          glob: "*.clean.sorted.vcf.gz"

arguments:
    - prefix: --broad_snv
      valueFrom: $(formatArray(inputs.broad_snv))

    - prefix: --sanger_snv
      valueFrom: $(formatArray(inputs.sanger_snv))

    - prefix: --dkfz_embl_snv
      valueFrom: $(formatArray(inputs.de_snv))

    - prefix: --muse_snv
      valueFrom: $(formatArray(inputs.muse_snv))

    - prefix: --broad_sv
      valueFrom: $(formatArray(inputs.broad_sv))

    - prefix: --sanger_sv
      valueFrom: $(formatArray(inputs.sanger_sv))

    - prefix: --dkfz_embl_sv
      valueFrom: $(formatArray(inputs.de_sv))

    - prefix: --broad_indel
      valueFrom: $(formatArray(inputs.broad_indel))

    - prefix: --sanger_indel
      valueFrom: $(formatArray(inputs.sanger_indel))

    - prefix: --dkfz_embl_indel
      valueFrom: $(formatArray(inputs.de_indel))

    - prefix: --smufin_indel
      valueFrom: $(formatArray(inputs.smufin_indel))

baseCommand: /opt/oxog_scripts/vcf_merge_by_type.pl
