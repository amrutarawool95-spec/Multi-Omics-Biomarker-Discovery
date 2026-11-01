# Dataset selection rationale

## Selected disease

Type 2 diabetes mellitus (T2D), with human pancreatic islets as the primary biological system.

## Planned research question

Can integrated transcriptomic and proteomic evidence from human pancreatic islets identify reproducible molecular candidates associated with T2D?

## Candidate datasets

| Role | Accession | Repository | Planned use |
|---|---|---|---|
| Discovery transcriptomics | GSE164416 | NCBI GEO | T2D vs non-diabetic control |
| Candidate proteomics | PXD022561 | PRIDE / ProteomeXchange | Differential protein abundance and cross-omics support, subject to file/sample audit |
| External transcriptomic validation | GSE76895 | NCBI GEO | Directional/statistical validation if phenotype and platform are suitable |

## Why this disease/system

Human pancreatic islets are directly relevant to insulin production and beta-cell function. A public transcriptomic dataset and a candidate proteomics accession have been identified in the same broad research context, making the study feasible enough to audit before committing to the full analysis.

## What is not yet established

The following must be verified from the source records and study publications:

1. Exact sample counts after exclusions and availability of usable measurements.
2. Whether the RNA and protein data are from the same donors.
3. Whether the PRIDE project contains quantitative protein abundance tables suitable for differential analysis.
4. The precise RNA-seq data type (raw integer counts, normalised counts, TPM/FPKM, or another format).
5. Tissue/sample comparability and disease definitions in GSE76895.
6. Covariates, batch structure, sex, age, BMI and other available clinical metadata.

## Primary contrast

T2D versus non-diabetic controls in GSE164416. Samples with impaired glucose tolerance and type 3c diabetes should not be silently pooled into either group. They may be used in separate exploratory analyses only if justified and documented.

## Analysis decision gates

- If RNA/protein samples are not paired, describe the work as **cross-study multi-omics integration**, not paired multi-omics correlation.
- If no suitable PRIDE quantitative matrix exists, revise the proteomic dataset choice before continuing.
- If the validation cohort differs in tissue or phenotype, treat it as indirect validation and explain the limitation.
- If sample size is inadequate for robust supervised learning, prioritise descriptive/statistical analysis and avoid overstated ML claims.

## Status

Disease and candidate accessions are selected provisionally. Dataset-level feasibility is not considered complete until Stage 2 audit is finished.
