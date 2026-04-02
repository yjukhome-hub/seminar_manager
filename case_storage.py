import json
import os
from datetime import datetime

CASES_FILE = "cases.json"
CATEGORIES = [
    "줄기세포 - 얼굴",
    "줄기세포 - 주름",
    "줄기세포 - 목",
    "줄기세포 - 혈관주사",
    "실리프팅",
    "콜라겐 주사",
    "밸런톡스",
    "복합 시술",
    "기타",
]


def load_cases() -> list[dict]:
    if not os.path.exists(CASES_FILE):
        return []
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cases(cases: list[dict]) -> None:
    with open(CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)


def add_case(case_data: dict) -> dict:
    cases = load_cases()
    case_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    case_data["id"] = case_id
    case_data["created_at"] = datetime.now().isoformat()
    case_data["status"] = case_data.get("status", "완성")
    cases.append(case_data)
    save_cases(cases)
    return case_data


def update_case(case_id: str, case_data: dict) -> bool:
    cases = load_cases()
    for i, case in enumerate(cases):
        if case["id"] == case_id:
            case_data["id"] = case_id
            case_data["created_at"] = case.get("created_at", datetime.now().isoformat())
            case_data["updated_at"] = datetime.now().isoformat()
            cases[i] = case_data
            save_cases(cases)
            return True
    return False


def delete_case(case_id: str) -> bool:
    cases = load_cases()
    new_cases = [c for c in cases if c["id"] != case_id]
    if len(new_cases) == len(cases):
        return False
    save_cases(new_cases)
    return True
