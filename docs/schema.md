# Unified Schema

This document describes the implemented Part 1 normalized outputs.

The pipeline reads three raw job-board CSV files and produces:

- `jobs.csv`: one normalized row per job posting
- `job_skills.csv`: one normalized row per job-skill pair

## Dataset Snapshot

- Raw input: 3,000 job rows total
- `jobs.csv`: 3,000 rows
- `job_skills.csv`: 31,638 rows

## jobs.csv

| Column | Description |
| --- | --- |
| `job_uid` | Stable ID built from source and source job ID |
| `source` | Source dataset: `dice`, `naukri`, or `reed` |
| `source_job_id` | Original job ID from the source |
| `source_company_id` | Original company ID when provided |
| `job_url` | Canonical job posting URL |
| `apply_url` | Application URL when available |
| `title` | Job title |
| `company_name` | Company name |
| `company_logo_url` | Company logo URL when available |
| `company_profile_url` | Company profile or company jobs URL when available |
| `description_text` | Plain-text job description |
| `description_html` | Raw HTML job description when available |
| `industry` | Source-provided industry/category when available |
| `seniority` | Inferred seniority label |
| `experience_min_years` | Minimum required experience in years when available |
| `experience_max_years` | Maximum required experience in years when available |
| `employment_type` | Normalized employment label such as `full_time`, `contract`, `permanent`, `walk_in`, or `internship` |
| `workplace_type` | Normalized workplace label such as `onsite`, `hybrid`, or `remote` |
| `location_raw` | Original location string from the source |
| `city` | Parsed city when the source provides a reliable signal |
| `region` | Parsed state or region when available |
| `country` | Parsed country when available |
| `salary_raw` | Original salary text or reconstructed salary summary |
| `salary_min` | Parsed minimum salary |
| `salary_max` | Parsed maximum salary |
| `salary_currency` | Normalized salary currency when valid |
| `salary_period` | Normalized salary period such as `annual`, `daily`, or `hourly` |
| `salary_is_disclosed` | `true` or `false` based on whether usable salary information is present |
| `date_posted` | Source posting date |
| `date_updated` | Source update date when available |
| `valid_through` | Closing date or last application date when available |
| `raw_record` | Full original source row serialized as JSON |

## job_skills.csv

This output stores one row per job-skill pair.

| Column | Description |
| --- | --- |
| `job_uid` | Foreign key to `jobs.job_uid` |
| `skill_raw` | Original extracted skill value |
| `skill_normalized` | Cleaned lowercase skill value |
| `skill_source` | Source field used to extract the skill |

## Source Mapping Summary

Direct mappings:

- `source_job_id`: Dice `id`, Naukri `jobId`, Reed `id`
- `job_url`: Dice `url`, Naukri `jdURL`, Reed `url`
- `title`: all three sources
- `company_name`: all three sources
- `description_text`: Dice `description`, Naukri `jobDescription`, Reed `descriptionText`
- `location_raw`: Dice `location`, Naukri `location`, Reed `jobLocation`
- `experience_min_years` / `experience_max_years`: Naukri numeric experience columns
- `industry`: Reed `industry`

Derived fields:

- `workplace_type`: Dice flags, Naukri `location`, Reed `jobLocationType`
- `employment_type`: Dice `positionSchedule` / `contractType`, Naukri `jobType`, Reed `employmentType`
- `seniority`: inferred from title, with Naukri experience fallback
- `city` and `region`: parsed from Dice `locationDetail`, Naukri single-city values, and Reed location fields
- `salary_*`: parsed from Dice salary text, Naukri `salaryDetail` with text fallback, and Reed structured salary fields

Skills:

- Dice: parsed from `skills`
- Naukri: parsed from `tagsAndSkills`
- Reed: not extracted in the current MVP because there is no dedicated skills field

## Coverage Notes

- `industry` is only populated from Reed because Dice and Naukri do not expose a strong equivalent field in these files.
- `source_company_id` is only populated for Naukri because Dice and Reed do not provide one in these datasets.
- `raw_record` preserves the full original source row so source-specific fields are not lost.
