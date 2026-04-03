"""Source-specific normalization logic for job datasets."""

from __future__ import annotations

import json
from typing import Dict, List, Tuple

from src.utils import (
    derive_dice_employment_type,
    derive_dice_workplace_type,
    infer_naukri_city,
    infer_seniority,
    infer_naukri_workplace_type,
    normalize_employment_type,
    normalize_skill_name,
    normalize_workplace_type,
    parse_dice_salary,
    parse_dice_skills,
    parse_dice_location_detail,
    parse_naukri_salary,
    parse_naukri_skills,
    parse_reed_salary,
)

JOB_COLUMNS = [
    "job_uid",
    "source",
    "source_job_id",
    "source_company_id",
    "job_url",
    "apply_url",
    "title",
    "company_name",
    "company_logo_url",
    "company_profile_url",
    "description_text",
    "description_html",
    "industry",
    "seniority",
    "experience_min_years",
    "experience_max_years",
    "employment_type",
    "workplace_type",
    "location_raw",
    "city",
    "region",
    "country",
    "salary_raw",
    "salary_min",
    "salary_max",
    "salary_currency",
    "salary_period",
    "salary_is_disclosed",
    "date_posted",
    "date_updated",
    "valid_through",
    "raw_record",
]

SKILL_COLUMNS = ["job_uid", "skill_raw", "skill_normalized", "skill_source"]

DIRECT_MAPPINGS = {
    "dice": {
        "source_job_id": "id",
        "job_url": "url",
        "apply_url": "applyUrl",
        "title": "title",
        "company_name": "companyName",
        "company_logo_url": "companyLogo",
        "description_text": "description",
        "description_html": "descriptionHtml",
        "location_raw": "location",
        "country": "country",
        "salary_raw": "salaryRaw",
        "salary_period": "salaryRawUnit",
        "date_posted": "datePosted",
        "date_updated": "dateUpdated",
        "valid_through": "lastApplicationDate",
    },
    "naukri": {
        "source_job_id": "jobId",
        "source_company_id": "companyId",
        "job_url": "jdURL",
        "title": "title",
        "company_name": "companyName",
        "company_logo_url": "logoPathV3",
        "company_profile_url": "companyJobsUrl",
        "description_text": "jobDescription",
        "location_raw": "location",
        "experience_min_years": "minimumExperience",
        "experience_max_years": "maximumExperience",
        "salary_raw": "salary",
        "salary_currency": "currency",
        "date_posted": "createdDate",
    },
    "reed": {
        "source_job_id": "id",
        "job_url": "url",
        "title": "title",
        "company_name": "companyName",
        "company_logo_url": "companyLogo",
        "company_profile_url": "companyProfileURL",
        "description_text": "descriptionText",
        "description_html": "descriptionHtml",
        "industry": "industry",
        "location_raw": "jobLocation",
        "region": "jobLocationRegion",
        "country": "jobLocationCountry",
        "salary_min": "salaryMin",
        "salary_max": "salaryMax",
        "salary_currency": "currency",
        "salary_period": "salaryTimeUnit",
        "date_posted": "datePosted",
        "valid_through": "validThrough",
    },
}


def build_empty_job_record() -> Dict[str, str]:
    """Return a normalized job record with all target columns initialized."""
    return {column: "" for column in JOB_COLUMNS}


def build_job_uid(source: str, source_job_id: str) -> str:
    """Build a stable job identifier from source and source-specific job id."""
    return f"{source}_{source_job_id}".lower()


def apply_direct_mapping(source: str, row: Dict[str, str]) -> Dict[str, str]:
    """Populate only the direct one-to-one normalized fields."""
    job = build_empty_job_record()
    job["source"] = source

    for target_column, source_column in DIRECT_MAPPINGS[source].items():
        job[target_column] = (row.get(source_column) or "").strip()

    job["job_uid"] = build_job_uid(source, job["source_job_id"])
    job["raw_record"] = json.dumps(row, ensure_ascii=True, sort_keys=True)
    return job


def build_skill_records(job_uid: str, raw_skills: List[str], skill_source: str) -> List[Dict[str, str]]:
    """Build normalized job-skill rows with per-job deduplication."""
    records: List[Dict[str, str]] = []
    seen_normalized_skills = set()

    for raw_skill in raw_skills:
        normalized_skill = normalize_skill_name(raw_skill)
        if not normalized_skill or normalized_skill in seen_normalized_skills:
            continue

        seen_normalized_skills.add(normalized_skill)
        records.append(
            {
                "job_uid": job_uid,
                "skill_raw": raw_skill.strip(),
                "skill_normalized": normalized_skill,
                "skill_source": skill_source,
            }
        )

    return records


def normalize_dice_row(row: Dict[str, str]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Normalize a Dice job row and extract source-provided skills."""
    job = apply_direct_mapping("dice", row)
    location_detail = parse_dice_location_detail(row.get("locationDetail", ""))
    salary = parse_dice_salary(row.get("salaryRaw", ""), row.get("salaryRawUnit", ""))
    job["seniority"] = infer_seniority(row.get("title", ""))
    job["employment_type"] = derive_dice_employment_type(
        row.get("contractType", ""),
        row.get("positionSchedule", ""),
    )
    job["workplace_type"] = derive_dice_workplace_type(
        row.get("remote", ""),
        row.get("onsite", ""),
        row.get("hybrid", ""),
    )
    job["city"] = location_detail.get("city", "")
    job["region"] = location_detail.get("region", "")
    if location_detail.get("country"):
        job["country"] = location_detail["country"]
    job.update(salary)
    skills = build_skill_records(job["job_uid"], parse_dice_skills(row.get("skills", "")), "skills")
    return job, skills


def normalize_naukri_row(row: Dict[str, str]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Normalize a Naukri job row and extract source-provided skills."""
    job = apply_direct_mapping("naukri", row)
    salary = parse_naukri_salary(
        row.get("salary", ""),
        row.get("salaryDetail", ""),
        row.get("currency", ""),
    )
    job["seniority"] = infer_seniority(
        row.get("title", ""),
        row.get("minimumExperience", ""),
        row.get("maximumExperience", ""),
    )
    job["employment_type"] = normalize_employment_type(row.get("jobType", ""))
    job["workplace_type"] = infer_naukri_workplace_type(row.get("location", ""))
    job["city"] = infer_naukri_city(row.get("location", ""))
    job.update(salary)
    skills = build_skill_records(
        job["job_uid"],
        parse_naukri_skills(row.get("tagsAndSkills", "")),
        "tagsAndSkills",
    )
    return job, skills


def normalize_reed_row(row: Dict[str, str]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Normalize a Reed job row. Reed does not expose a dedicated skill field."""
    job = apply_direct_mapping("reed", row)
    job["seniority"] = infer_seniority(row.get("title", ""))
    job["employment_type"] = normalize_employment_type(row.get("employmentType", ""))
    job["workplace_type"] = normalize_workplace_type(row.get("jobLocationType", ""))
    job["city"] = (row.get("jobLocation") or "").strip()
    job.update(
        parse_reed_salary(
            row.get("salaryExact", ""),
            row.get("salaryMin", ""),
            row.get("salaryMax", ""),
            row.get("currency", ""),
            row.get("salaryTimeUnit", ""),
        )
    )
    return job, []
