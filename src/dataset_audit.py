"""Audit downloaded metadata and local data files; no biological inference is performed."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_csv(path: Path) -> dict[str, Any]:
    try:
        frame = pd.read_csv(path, low_memory=False)
        return {
            "path": str(path),
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
            "column_names": frame.columns.astype(str).tolist(),
            "duplicate_column_names": int(frame.columns.duplicated().sum()),
            "duplicate_rows": int(frame.duplicated().sum()),
            "missing_cells": int(frame.isna().sum().sum()),
            "missing_fraction": float(frame.isna().sum().sum() / max(frame.size, 1)),
            "sha256": sha256_file(path),
            "read_error": None,
        }
    except Exception as exc:
        return {"path": str(path), "read_error": str(exc), "sha256": sha256_file(path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/project.yaml")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    metadata_dir = Path(config["paths"]["metadata"])
    report_dir = Path(config["paths"]["reports"])
    report_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for path in sorted(metadata_dir.glob("*.csv")):
        records.append(inspect_csv(path))

    expected = [
        metadata_dir / "GSE164416_samples.csv",
        metadata_dir / "GSE76895_samples.csv",
        metadata_dir / "PXD022561_files.csv",
    ]
    missing_expected = [str(path) for path in expected if not path.exists()]

    report = {
        "project": config["project"]["name"],
        "audit_scope": "Local metadata CSV files only; not a biological QC assessment.",
        "metadata_files": records,
        "expected_files_not_found": missing_expected,
        "interpretation": (
            "Inspect the source study and curated sample annotation before selecting samples. "
            "This audit does not verify biological labels, donor matching, assay validity or "
            "whether expression values are raw counts."
        ),
    }

    json_path = report_dir / "dataset_audit.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Dataset metadata audit",
        "",
        "> This is a file/metadata audit, not a biological quality-control analysis.",
        "",
        f"Project: **{report['project']}**",
        "",
        "## Files inspected",
        "",
    ]
    if records:
        for item in records:
            lines.append(f"### `{item['path']}`")
            if item.get("read_error"):
                lines.append(f"- Read error: {item['read_error']}")
            else:
                lines.extend([
                    f"- Rows: {item['rows']}",
                    f"- Columns: {item['columns']}",
                    f"- Missing cells: {item['missing_cells']}",
                    f"- Missing fraction: {item['missing_fraction']:.4f}",
                    f"- Duplicate rows: {item['duplicate_rows']}",
                    f"- SHA-256: `{item['sha256']}`",
                ])
            lines.append("")
    else:
        lines.append("No metadata CSV files found. Run the acquisition commands first.")
        lines.append("")

    lines.extend([
        "## Expected files not found",
        "",
        *([f"- `{item}`" for item in missing_expected] or ["- None"]),
        "",
        "## Interpretation",
        "",
        report["interpretation"],
        "",
    ])
    (report_dir / "dataset_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {report_dir / 'dataset_audit.md'}")


if __name__ == "__main__":
    main()
