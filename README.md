# Multi-Omics Biomarker Discovery in Type 2 Diabetes

**Primary biological system:** human pancreatic islets  
**Discovery transcriptomics:** GEO `GSE164416`  
**Candidate proteomics resource:** PRIDE `PXD022561`  
**Potential independent transcriptomic validation:** GEO `GSE76895`

> **Project status:** Stage 1 disease selection is provisionally complete. Stage 2 dataset acquisition and audit are next. No biological results are included in this starter repository. Accession-level sample counts and donor matching must be re-verified from the downloaded records before analysis.

## Research question

Can integrated transcriptomic and proteomic evidence from human pancreatic islets identify reproducible molecular candidates associated with type 2 diabetes, supported by functional annotation, network analysis and appropriately validated machine learning?

## Scientific scope and cautions

- The primary contrast is planned as **type 2 diabetes vs non-diabetic controls** in GSE164416.
- Impaired glucose tolerance and type 3c diabetes samples are not part of that primary contrast unless a separate, pre-specified analysis is justified.
- Do not assume RNA and protein samples are paired because accessions belong to the same research programme. Confirm donor/sample identifiers and experimental design.
- GSE76895 is a potential external transcriptomic validation cohort; platform differences must be handled explicitly.
- Pancreatic-islet candidates are tissue-context findings. They are not automatically blood-based or clinically validated biomarkers.
- Do not run RNA-seq count models on TPM/FPKM or other normalised expression values.
- Do not treat missing proteomic values as zero.
- Do not perform random sample-level train/test splits across related cohorts if this leaks cohort or batch information.

## Repository layout

```text
MultiOmics-Biomarker-Discovery/
├── README.md
├── requirements.txt
├── config/
│   └── project.yaml
├── data/
│   ├── raw/
│   │   ├── geo/
│   │   └── pride/
│   ├── processed/
│   └── metadata/
├── src/
│   ├── __init__.py
│   ├── data_acquisition.py
│   ├── metadata_processing.py
│   └── dataset_audit.py
├── reports/
│   └── DATASET_SELECTION.md
└── docs/
    ├── DATA_DICTIONARY.md
    └── STAGE_2_WORKFLOW.md
```

## Setup

Python 3.10 or 3.11 is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Stage 2: acquire metadata and audit files

Run commands from the repository root:

```bash
python -m src.data_acquisition --config config/project.yaml --geo-metadata
python -m src.data_acquisition --config config/project.yaml --pride-metadata
python -m src.dataset_audit --config config/project.yaml
```

The acquisition script retrieves GEO sample metadata and PRIDE project/file metadata. It does **not** automatically download all raw sequencing or mass-spectrometry files. This is intentional: first inspect file names, sizes, formats, permissions and sample manifests; then choose the correct processed or raw files.

## Important outputs

- `data/metadata/GSE164416_samples.csv`
- `data/metadata/GSE76895_samples.csv`
- `data/metadata/PXD022561_project.json`
- `data/metadata/PXD022561_files.csv`
- `data/metadata/acquisition_log.json`
- `reports/dataset_audit.json`
- `reports/dataset_audit.md`

## Manual curation is required

GEO metadata fields are often free text. Review the sample metadata and create a curated file named `data/metadata/GSE164416_sample_annotations.csv` with at least:

`sample_accession,donor_id,condition,include_primary,exclusion_reason`

Use only labels supported by the source publication or repository metadata. Do not infer disease status from sample titles alone when the record is ambiguous.

## Reproducibility

- The project configuration is stored in `config/project.yaml`.
- Acquisition logs include timestamps, source URLs and output paths.
- The audit script records file sizes, hashes for local tabular files, missingness and duplicate identifiers where applicable.
- Raw data should remain outside Git if large or subject to repository/database terms. Commit accession references, metadata provenance and analysis code instead.

## Next scientific gate

Do not proceed to differential expression until:
1. Sample labels are checked against the original study.
2. The RNA-seq data type is established (raw integer counts vs normalised values).
3. The PRIDE file manifest and protein quantification format are inspected.
4. Donor matching is explicitly established or explicitly ruled out.
5. Inclusion/exclusion decisions are documented.
