# Stage 2 workflow: acquisition and dataset audit

## 1. Install environment

```bash
pip install -r requirements.txt
```

## 2. Retrieve GEO metadata

```bash
python -m src.data_acquisition --config config/project.yaml --geo-metadata
```

Expected exports:
- `data/metadata/GSE164416_samples.csv`
- `data/metadata/GSE76895_samples.csv`

The GEO SOFT records are cached under `data/raw/geo/`.

## 3. Retrieve PRIDE project and file metadata

```bash
python -m src.data_acquisition --config config/project.yaml --pride-metadata
```

Expected exports:
- `data/metadata/PXD022561_project.json`
- `data/metadata/PXD022561_files.csv`

The PRIDE API may change response pagination/field structure. If the file list is empty or the request fails, inspect the public project page and API documentation; do not infer that the project has no files.

## 4. Audit local metadata exports

```bash
python -m src.dataset_audit --config config/project.yaml
```

## 5. Create a manual phenotype curation template

```bash
python -m src.metadata_processing \
  --input data/metadata/GSE164416_samples.csv \
  --output data/metadata/GSE164416_sample_annotations.csv
```

Open the output and curate each sample against the source publication and GEO metadata. Never let a keyword-matching script silently decide disease status.

Validate after curation:

```bash
python -m src.metadata_processing \
  --input data/metadata/GSE164416_sample_annotations.csv \
  --output unused.csv \
  --validate-only
```

## 6. Stage 2 exit criteria

Do not proceed to differential expression until the following are documented:

- Sample-level phenotype labels and exclusions.
- Donor IDs, if available.
- RNA-seq data type and quantification method.
- PRIDE quantitative file(s), assay type and protein identifier format.
- Whether transcriptomic and proteomic samples are paired.
- Missingness and batch structure.
- Data-use and redistribution conditions.
