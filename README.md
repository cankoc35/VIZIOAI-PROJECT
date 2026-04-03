# Vizio AI Case Study

This repository contains a local Python pipeline for normalizing job postings from three job boards into a shared schema, plus the Part 2 and Part 3 design notes for the case study.

## Scope

- Part 1: implemented local normalization pipeline
- Part 2: documented data-modeling and system design notes
- Part 3: documented AI / RAG extension notes

## Local Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run

From the project root:

```bash
python run.py
```

This writes:

- `data/processed/jobs.csv`
- `data/processed/job_skills.csv`

## Current Outputs

- Raw input: 3 CSV files, 3,000 total job rows
- Normalized jobs output: 3,000 rows
- Normalized job-skills output: 31,638 rows

## What Is Normalized

- `Location`: `location_raw`, `city`, `region`, `country`
- `Skills`: extracted into `job_skills.csv` for Dice and Naukri
- `Seniority`: inferred from title, with Naukri experience fallback
- `Work type`: `workplace_type` and `employment_type`
- `Industry`: populated where a source provides a structured field
- `Company information`: `company_name`, `company_logo_url`, `company_profile_url`, and `source_company_id` when available
- `Salary`: `salary_raw`, `salary_min`, `salary_max`, `salary_currency`, `salary_period`, `salary_is_disclosed`

## Key Assumptions

- Reed `industry` is used directly because Dice and Naukri do not expose a strong equivalent field in these samples.
- Naukri `minimumExperience` and `maximumExperience` are preferred over `experienceText` because they are already structured.
- Seniority inference is heuristic and title-first.
- Salary parsing is MVP-level and focused on the dominant patterns in the datasets.
- Reed does not have a dedicated skills field, so `job_skills.csv` currently covers Dice and Naukri only.

## Main Limitations

- Company identity resolution across sources is not implemented.
- Industry coverage is source-dependent and sparse outside Reed.
- Multi-location Naukri rows remain only partially structured.
- Seniority and salary parsing rely on practical heuristics, not full ontologies.

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── Vizio Al - Case Study - Applied Data Engineer.pdf
│   ├── schema.md
│   └── design_notes.md
├── src/
│   ├── pipeline.py
│   ├── normalize.py
│   └── utils.py
└── run.py
```

## Notes

- Part 1 schema and mapping notes are in [docs/schema.md](/Users/cankoc/Desktop/VizioAiProject/docs/schema.md).
- Part 2 and Part 3 design notes are in [docs/design_notes.md](/Users/cankoc/Desktop/VizioAiProject/docs/design_notes.md).
