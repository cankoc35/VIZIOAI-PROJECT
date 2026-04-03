"""Pipeline orchestration entrypoint for local job normalization."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from src.normalize import (
    JOB_COLUMNS,
    SKILL_COLUMNS,
    normalize_dice_row,
    normalize_naukri_row,
    normalize_reed_row,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"

Normalizer = Callable[[Dict[str, str]], Tuple[Dict[str, str], List[Dict[str, str]]]]

SOURCE_FILES: Dict[str, Tuple[str, Normalizer]] = {
    "dataset_dice_jobs.csv": ("dice", normalize_dice_row),
    "dataset_naukri_jobs.csv": ("naukri", normalize_naukri_row),
    "dataset_reed_jobs.csv": ("reed", normalize_reed_row),
}


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    """Load CSV rows as dictionaries."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(csv_path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    """Write normalized rows to a CSV file."""
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_pipeline() -> None:
    """Run the local normalization pipeline."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    normalized_jobs: List[Dict[str, str]] = []
    normalized_skills: List[Dict[str, str]] = []

    for file_name, (_, normalizer) in SOURCE_FILES.items():
        csv_path = RAW_DATA_DIR / file_name
        for row in load_rows(csv_path):
            job_record, skill_records = normalizer(row)
            normalized_jobs.append(job_record)
            normalized_skills.extend(skill_records)

    write_rows(PROCESSED_DATA_DIR / "jobs.csv", JOB_COLUMNS, normalized_jobs)
    write_rows(PROCESSED_DATA_DIR / "job_skills.csv", SKILL_COLUMNS, normalized_skills)
