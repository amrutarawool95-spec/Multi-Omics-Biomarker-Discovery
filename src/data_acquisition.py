"""Retrieve public dataset metadata without blindly downloading large raw files.

Examples (run from repository root):
    python -m src.data_acquisition --config config/project.yaml --geo-metadata
    python -m src.data_acquisition --config config/project.yaml --pride-metadata
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yaml
import GEOparse


LOGGER = logging.getLogger("data_acquisition")


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Configuration must contain a YAML mapping.")
    return config


def ensure_directories(config: dict[str, Any]) -> None:
    for key in ("raw_geo", "raw_pride", "processed", "metadata"):
        Path(config["paths"][key]).mkdir(parents=True, exist_ok=True)
    Path(config["paths"]["reports"]).mkdir(parents=True, exist_ok=True)


def write_log(config: dict[str, Any], entry: dict[str, Any]) -> None:
    log_path = Path(config["paths"]["metadata"]) / "acquisition_log.json"
    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOGGER.warning("Existing acquisition log is invalid; starting a new log.")
    existing.append(entry)
    log_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def acquire_geo_metadata(accession: str, config: dict[str, Any]) -> Path:
    """Download GEO SOFT metadata and export one row per GSM sample."""
    raw_dir = Path(config["paths"]["raw_geo"])
    metadata_dir = Path(config["paths"]["metadata"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Retrieving GEO record %s", accession)
    gse = GEOparse.get_GEO(
        geo=accession,
        destdir=str(raw_dir),
        silent=True,
        how="full",
    )

    rows: list[dict[str, Any]] = []
    for gsm_id, gsm in gse.gsms.items():
        row: dict[str, Any] = {
            "sample_accession": gsm_id,
            "sample_title": gsm.metadata.get("title", [""])[0],
            "source_name": gsm.metadata.get("source_name_ch1", [""])[0],
            "organism": gsm.metadata.get("organism_ch1", [""])[0],
            "platform_accessions": ";".join(gsm.metadata.get("platform_id", [])),
        }
        # Preserve all characteristics as explicit columns; GEO fields are free text.
        for key, values in gsm.metadata.items():
            if key.startswith("characteristics_ch"):
                row[key] = " | ".join(str(value) for value in values)
        rows.append(row)

    if not rows:
        raise RuntimeError(f"No GSM sample records were returned for {accession}.")

    frame = pd.DataFrame(rows).sort_values("sample_accession")
    output = metadata_dir / f"{accession}_samples.csv"
    frame.to_csv(output, index=False)

    write_log(config, {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "action": "geo_metadata_download",
        "accession": accession,
        "source_url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
        "output": str(output),
        "sample_records_exported": int(len(frame)),
    })
    LOGGER.info("Wrote %d sample records to %s", len(frame), output)
    return output


def acquire_pride_metadata(accession: str, config: dict[str, Any]) -> tuple[Path, Path]:
    """Retrieve PRIDE project metadata and file manifest via PRIDE Archive REST API."""
    metadata_dir = Path(config["paths"]["metadata"])
    metadata_dir.mkdir(parents=True, exist_ok=True)

    timeout = int(config.get("acquisition", {}).get("request_timeout_seconds", 60))
    user_agent = config.get("acquisition", {}).get(
        "user_agent", "MultiOmicsBiomarkerDiscovery/0.1"
    )
    headers = {"User-Agent": user_agent, "Accept": "application/json"}

    base = "https://www.ebi.ac.uk/pride/ws/archive/v2"
    project_url = f"{base}/projects/{accession}"
    files_url = f"{base}/projects/{accession}/files"

    session = requests.Session()
    session.headers.update(headers)

    project_response = session.get(project_url, timeout=timeout)
    project_response.raise_for_status()
    project_json = project_response.json()

    # PRIDE API responses can be paginated or shaped differently across API versions.
    files_response = session.get(files_url, timeout=timeout)
    files_response.raise_for_status()
    files_payload = files_response.json()

    project_path = metadata_dir / f"{accession}_project.json"
    project_path.write_text(json.dumps(project_json, indent=2), encoding="utf-8")

    if isinstance(files_payload, list):
        file_records = files_payload
    elif isinstance(files_payload, dict):
        file_records = files_payload.get("list", files_payload.get("files", []))
        if not isinstance(file_records, list):
            file_records = [files_payload]
    else:
        file_records = []

    files_frame = pd.json_normalize(file_records) if file_records else pd.DataFrame()
    files_path = metadata_dir / f"{accession}_files.csv"
    files_frame.to_csv(files_path, index=False)

    write_log(config, {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "action": "pride_metadata_download",
        "accession": accession,
        "source_url": f"https://www.ebi.ac.uk/pride/archive/projects/{accession}",
        "api_project_url": project_url,
        "api_files_url": files_url,
        "project_output": str(project_path),
        "files_output": str(files_path),
        "file_records_exported": int(len(files_frame)),
    })
    LOGGER.info("Wrote PRIDE project metadata to %s", project_path)
    LOGGER.info("Wrote %d file records to %s", len(files_frame), files_path)
    return project_path, files_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/project.yaml")
    parser.add_argument("--geo-metadata", action="store_true")
    parser.add_argument("--pride-metadata", action="store_true")
    args = parser.parse_args()

    if not args.geo_metadata and not args.pride_metadata:
        parser.error("Select at least one action: --geo-metadata and/or --pride-metadata")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = load_config(args.config)
    ensure_directories(config)

    if args.geo_metadata:
        for key in ("discovery_transcriptomics", "validation_transcriptomics"):
            dataset = config["datasets"][key]
            acquire_geo_metadata(dataset["accession"], config)

    if args.pride_metadata:
        dataset = config["datasets"]["candidate_proteomics"]
        acquire_pride_metadata(dataset["accession"], config)


if __name__ == "__main__":
    main()
