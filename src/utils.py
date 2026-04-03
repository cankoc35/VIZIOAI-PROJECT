"""Shared helpers for parsing and cleanup."""

from __future__ import annotations

import ast
import re
from typing import Dict, List


WHITESPACE_PATTERN = re.compile(r"\s+")
NUMBER_PATTERN = re.compile(r"\d[\d,]*\.?\d*")

EMPLOYMENT_TYPE_MAP = {
    "full_time": "full_time",
    "part_time": "part_time",
    "permanent": "permanent",
    "contract": "contract",
    "walk in": "walk_in",
    "internship": "internship",
}

DICE_CONTRACT_TYPE_MAP = {
    "direct_hire": "permanent",
    "contract": "contract",
    "direct_hire_contract": "contract_to_hire",
}

WORKPLACE_TYPE_PATTERNS = (
    ("hybrid", "hybrid"),
    ("remote", "remote"),
    ("on-site", "onsite"),
    ("onsite", "onsite"),
    ("on site", "onsite"),
)

DICE_WORKPLACE_COMBINATION_MAP = {
    (False, False, False): "",
    (False, False, True): "hybrid",
    (False, True, False): "onsite",
    (False, True, True): "hybrid",
    (True, False, False): "remote",
    (True, False, True): "hybrid",
    (True, True, False): "hybrid",
    (True, True, True): "hybrid",
}

SENIORITY_RULES = (
    ("intern", re.compile(r"\b(intern|internship|trainee|apprentice|graduate)\b")),
    ("principal", re.compile(r"\b(principal|head|chief|director)\b")),
    ("manager", re.compile(r"\b(manager|mgr)\b")),
    ("lead", re.compile(r"\b(lead|leader)\b")),
    ("senior", re.compile(r"\b(senior|sr\.?|staff)\b")),
    ("junior", re.compile(r"\b(junior|jr\.?|entry[- ]level)\b")),
)

SALARY_PERIOD_MAP = {
    "annual": "annual",
    "annually": "annual",
    "per annum": "annual",
    "per year": "annual",
    "yearly": "annual",
    "pa": "annual",
    "annual": "annual",
    "hourly": "hourly",
    "per hour": "hourly",
    "daily": "daily",
    "per day": "daily",
    "monthly": "monthly",
    "per month": "monthly",
}


def normalize_skill_name(skill: str) -> str:
    """Normalize a skill string for downstream matching and deduplication."""
    cleaned = WHITESPACE_PATTERN.sub(" ", skill.strip())
    return cleaned.lower()


def parse_dice_skills(raw_skills: str) -> List[str]:
    """Parse Dice's serialized list of skill dictionaries into skill names."""
    if not raw_skills.strip():
        return []

    try:
        parsed = ast.literal_eval(raw_skills)
    except (SyntaxError, ValueError):
        return []

    skills: List[str] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if name:
            skills.append(name)
    return skills


def parse_naukri_skills(raw_skills: str) -> List[str]:
    """Split Naukri's comma-separated skill string into individual entries."""
    if not raw_skills.strip():
        return []

    return [skill.strip() for skill in raw_skills.split(",") if skill.strip()]


def parse_dice_location_detail(raw_location_detail: str) -> Dict[str, str]:
    """Parse Dice's serialized location detail payload into simple fields."""
    if not raw_location_detail.strip():
        return {}

    try:
        parsed = ast.literal_eval(raw_location_detail)
    except (SyntaxError, ValueError):
        return {}

    if not isinstance(parsed, dict):
        return {}

    return {
        "city": str(parsed.get("city") or "").strip(),
        "region": str(parsed.get("state") or "").strip(),
        "country": str(parsed.get("country") or "").strip(),
    }


def normalize_workplace_type(value: str) -> str:
    """Normalize source-specific workplace labels into a shared set."""
    cleaned = value.strip().lower()
    if not cleaned:
        return ""

    for pattern, normalized_value in WORKPLACE_TYPE_PATTERNS:
        if pattern in cleaned:
            return normalized_value

    return ""


def derive_dice_workplace_type(remote: str, onsite: str, hybrid: str) -> str:
    """Derive workplace type from Dice's boolean-like flags."""
    flags = (
        remote.strip().lower() == "true",
        onsite.strip().lower() == "true",
        hybrid.strip().lower() == "true",
    )
    return DICE_WORKPLACE_COMBINATION_MAP.get(flags, "")


def infer_naukri_workplace_type(location: str) -> str:
    """Infer workplace type from Naukri's free-text location field."""
    return normalize_workplace_type(location)


def infer_naukri_city(location: str) -> str:
    """Extract a city from Naukri location text only when it is clearly singular."""
    cleaned = location.strip()
    if not cleaned:
        return ""

    for prefix in ("Hybrid - ", "Remote - ", "Onsite - ", "On-site - "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
            break

    if not cleaned or cleaned.lower() == "remote":
        return ""

    if "," in cleaned:
        return ""

    return cleaned


def derive_dice_employment_type(contract_type: str, position_schedule: str) -> str:
    """Normalize Dice employment signals into a single employment type field."""
    normalized_schedule = normalize_employment_type(position_schedule)
    if normalized_schedule:
        return normalized_schedule

    cleaned_contract_type = contract_type.strip().lower()
    return DICE_CONTRACT_TYPE_MAP.get(cleaned_contract_type, "")


def normalize_employment_type(value: str) -> str:
    """Normalize source-specific employment labels into a shared set."""
    cleaned = value.strip().lower()
    if not cleaned:
        return ""
    return EMPLOYMENT_TYPE_MAP.get(cleaned, cleaned.replace(" ", "_"))


def infer_seniority_from_experience(min_years: str, max_years: str) -> str:
    """Infer seniority from an experience range when the title gives no signal."""
    values = []
    for value in (min_years, max_years):
        cleaned = value.strip()
        if not cleaned:
            continue
        try:
            values.append(float(cleaned))
        except ValueError:
            continue

    if not values:
        return ""

    highest_years = max(values)
    if highest_years <= 1:
        return "intern"
    if highest_years <= 3:
        return "junior"
    if highest_years <= 7:
        return "mid"
    return "senior"


def infer_seniority(title: str, min_years: str = "", max_years: str = "") -> str:
    """Infer seniority from title first, then fallback to experience range."""
    cleaned_title = title.strip().lower()
    if cleaned_title:
        for normalized_value, pattern in SENIORITY_RULES:
            if pattern.search(cleaned_title):
                return normalized_value

    return infer_seniority_from_experience(min_years, max_years)


def normalize_salary_currency(value: str) -> str:
    """Keep only plausible 3-letter currency codes."""
    cleaned = value.strip().upper()
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned
    return ""


def normalize_salary_period(value: str) -> str:
    """Normalize salary period labels into a shared set."""
    cleaned = value.strip().lower()
    if not cleaned:
        return ""
    return SALARY_PERIOD_MAP.get(cleaned, "")


def parse_salary_numbers(value: str) -> List[float]:
    """Extract numeric salary values from free-text salary fields."""
    numbers = []
    for match in NUMBER_PATTERN.findall(value):
        cleaned = match.replace(",", "")
        try:
            numbers.append(float(cleaned))
        except ValueError:
            continue
    return numbers


def format_salary_number(value: float) -> str:
    """Format parsed salary numbers for CSV output."""
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def parse_dice_salary(raw_salary: str, raw_unit: str) -> Dict[str, str]:
    """Parse Dice salary text into structured fields."""
    cleaned_salary = raw_salary.strip()
    if not cleaned_salary:
        return {
            "salary_raw": "",
            "salary_min": "",
            "salary_max": "",
            "salary_currency": "",
            "salary_period": normalize_salary_period(raw_unit),
            "salary_is_disclosed": "",
        }

    numbers = parse_salary_numbers(cleaned_salary)
    currency = ""
    if cleaned_salary.upper().startswith("USD"):
        currency = "USD"

    salary_min = ""
    salary_max = ""
    if len(numbers) >= 2:
        salary_min = format_salary_number(numbers[0])
        salary_max = format_salary_number(numbers[1])
    elif len(numbers) == 1:
        salary_min = format_salary_number(numbers[0])
        salary_max = format_salary_number(numbers[0])

    salary_period = normalize_salary_period(raw_unit)
    if not salary_period:
        lowered = cleaned_salary.lower()
        if "per year" in lowered:
            salary_period = "annual"
        elif "per hour" in lowered:
            salary_period = "hourly"

    disclosed = ""
    if cleaned_salary:
        disclosed = "true" if salary_min or salary_max else "false"

    return {
        "salary_raw": cleaned_salary,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": currency,
        "salary_period": salary_period,
        "salary_is_disclosed": disclosed,
    }


def parse_naukri_salary_detail(raw_salary_detail: str) -> Dict[str, str]:
    """Parse Naukri's serialized salary detail payload."""
    if not raw_salary_detail.strip():
        return {}

    try:
        parsed = ast.literal_eval(raw_salary_detail)
    except (SyntaxError, ValueError):
        return {}

    if not isinstance(parsed, dict):
        return {}

    minimum_salary = parsed.get("minimumSalary")
    maximum_salary = parsed.get("maximumSalary")
    currency = normalize_salary_currency(str(parsed.get("currency") or ""))
    hide_salary = parsed.get("hideSalary")

    salary_min = ""
    salary_max = ""
    if isinstance(minimum_salary, (int, float)) and minimum_salary > 0:
        salary_min = format_salary_number(float(minimum_salary))
    if isinstance(maximum_salary, (int, float)) and maximum_salary > 0:
        salary_max = format_salary_number(float(maximum_salary))

    disclosed = ""
    if hide_salary is True:
        disclosed = "false"
    elif salary_min or salary_max:
        disclosed = "true"

    return {
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": currency,
        "salary_is_disclosed": disclosed,
    }


def parse_naukri_salary(raw_salary: str, raw_salary_detail: str, raw_currency: str) -> Dict[str, str]:
    """Parse Naukri salary fields into a shared structured representation."""
    cleaned_salary = raw_salary.strip()
    detail = parse_naukri_salary_detail(raw_salary_detail)

    salary_min = detail.get("salary_min", "")
    salary_max = detail.get("salary_max", "")
    salary_currency = detail.get("salary_currency") or normalize_salary_currency(raw_currency)
    salary_is_disclosed = detail.get("salary_is_disclosed", "")
    salary_period = ""

    lowered = cleaned_salary.lower()
    if " pa" in lowered or lowered.endswith("pa"):
        salary_period = "annual"

    if not salary_is_disclosed and cleaned_salary:
        if lowered == "not disclosed":
            salary_is_disclosed = "false"
        elif salary_min or salary_max:
            salary_is_disclosed = "true"

    if not (salary_min or salary_max) and cleaned_salary and lowered != "not disclosed":
        numbers = parse_salary_numbers(cleaned_salary)
        if "lacs" in lowered:
            numbers = [number * 100000 for number in numbers]
        if len(numbers) >= 2:
            salary_min = format_salary_number(numbers[0])
            salary_max = format_salary_number(numbers[1])
            salary_is_disclosed = "true"
        elif len(numbers) == 1:
            salary_min = format_salary_number(numbers[0])
            salary_max = format_salary_number(numbers[0])
            salary_is_disclosed = "true"

    return {
        "salary_raw": cleaned_salary,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "salary_period": salary_period,
        "salary_is_disclosed": salary_is_disclosed,
    }


def build_reed_salary_raw(salary_min: str, salary_max: str, currency: str, period: str) -> str:
    """Construct a readable raw salary string from Reed's structured fields."""
    if not salary_min and not salary_max:
        return ""

    parts = []
    normalized_currency = normalize_salary_currency(currency)
    if normalized_currency:
        parts.append(normalized_currency)

    if salary_min and salary_max:
        parts.append(f"{salary_min} - {salary_max}")
    else:
        parts.append(salary_min or salary_max)

    if period:
        parts.append(period)

    return " ".join(parts)


def parse_reed_salary(
    salary_exact: str,
    salary_min: str,
    salary_max: str,
    currency: str,
    period: str,
) -> Dict[str, str]:
    """Normalize Reed salary fields and drop placeholder zero values."""

    def positive_numeric_string(value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ""
        try:
            numeric_value = float(cleaned)
        except ValueError:
            return ""
        if numeric_value <= 0:
            return ""
        return format_salary_number(numeric_value)

    normalized_min = positive_numeric_string(salary_min)
    normalized_max = positive_numeric_string(salary_max)
    normalized_exact = positive_numeric_string(salary_exact)

    if normalized_exact and not normalized_min and not normalized_max:
        normalized_min = normalized_exact
        normalized_max = normalized_exact

    normalized_currency = normalize_salary_currency(currency)
    normalized_period = normalize_salary_period(period)
    disclosed = "true" if normalized_min or normalized_max else ""

    return {
        "salary_raw": build_reed_salary_raw(
            normalized_min,
            normalized_max,
            normalized_currency,
            normalized_period,
        ),
        "salary_min": normalized_min,
        "salary_max": normalized_max,
        "salary_currency": normalized_currency,
        "salary_period": normalized_period,
        "salary_is_disclosed": disclosed,
    }
