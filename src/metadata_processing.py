"""Create a curation template; never infer disease labels from ambiguous free text."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "sample_accession",
    "donor_id",
    "condition",
    "include_primary",
    "exclusion_reason",
]


def make_template(input_csv: str | Path, output_csv: str | Path) -> None:
    source = pd.read_csv(input_csv)
    if "sample_accession" not in source.columns:
        raise ValueError(f"{input_csv} must contain sample_accession.")

    template = source[["sample_accession"]].copy()
    template["donor_id"] = ""
    template["condition"] = ""
    template["include_primary"] = ""
    template["exclusion_reason"] = ""
    # Include source title/characteristics for human review, without auto-classification.
    for column in ("sample_title", "source_name"):
        if column in source.columns:
            template[column] = source[column]
    characteristic_columns = [c for c in source.columns if c.startswith("characteristics_ch")]
    for column in characteristic_columns:
        template[column] = source[column]

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(output_csv, index=False)
    print(f"Created manual-curation template: {output_csv}")
    print("Fill condition and inclusion fields only after checking the source study.")


def validate_curated_file(path: str | Path) -> None:
    frame = pd.read_csv(path, dtype=str).fillna("")
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if frame["sample_accession"].duplicated().any():
        duplicates = frame.loc[
            frame["sample_accession"].duplicated(), "sample_accession"
        ].tolist()
        raise ValueError(f"Duplicate sample accessions: {duplicates[:10]}")
    allowed_include = {"yes", "no"}
    observed = set(frame["include_primary"].str.strip().str.lower()) - {""}
    if not observed.issubset(allowed_include):
        raise ValueError("include_primary must contain only yes/no (or blank while curating).")
    print(f"Validated {len(frame)} curated sample rows. Blank fields still require review.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="GEO sample metadata CSV")
    parser.add_argument("--output", required=True, help="Curated annotation CSV")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    if args.validate_only:
        validate_curated_file(args.input)
    else:
        make_template(args.input, args.output)


if __name__ == "__main__":
    main()
