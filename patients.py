"""Patient identity: lookup by name and date of birth, and registration."""

from __future__ import annotations

import re
from datetime import date, datetime

import data


def _norm(name: str) -> str:
    return " ".join(name.lower().split())


def parse_date(text: str) -> date | None:
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def age_on(born: date, today: date | None = None) -> int:
    today = today or date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def find_patient(patient_name: str, date_of_birth: str) -> dict | None:
    for patient in data.PATIENTS.values():
        if _norm(patient["name"]) == _norm(patient_name) and patient["date_of_birth"] == date_of_birth:
            return patient
    return None


def public_appointment(appointment: dict) -> dict:
    provider = data.PROVIDERS[appointment["provider_id"]]
    return {
        "id": appointment["id"],
        "provider_id": provider["id"],
        "provider": provider["name"],
        "specialty": provider["specialty"],
        "date": appointment["date"],
        "time": appointment["time"],
        "appointment_type": appointment["appointment_type"],
        "duration_minutes": appointment["duration_minutes"],
        "reason": appointment["reason"],
    }


def upcoming_appointments(patient_id: str) -> list[dict]:
    now = datetime.now()
    mine = [
        a
        for a in data.APPOINTMENTS.values()
        if a["patient_id"] == patient_id and datetime.fromisoformat(f"{a['date']}T{a['time']}") > now
    ]
    mine.sort(key=lambda a: (a["date"], a["time"]))
    return [public_appointment(a) for a in mine]


def lookup_patient(patient_name: str, date_of_birth: str) -> dict:
    if parse_date(date_of_birth) is None:
        return {"ok": False, "error": "date_of_birth must be YYYY-MM-DD"}
    with data.LOCK:
        patient = find_patient(patient_name, date_of_birth)
        if patient is None:
            return {"ok": True, "found": False}
        return {
            "ok": True,
            "found": True,
            "patient": {
                "id": patient["id"],
                "name": patient["name"],
                "date_of_birth": patient["date_of_birth"],
                "phone": patient["phone"],
                "insurance_plan": patient["insurance_plan"],
                "member_id": patient["member_id"],
            },
            "appointments": upcoming_appointments(patient["id"]),
        }


def register_patient(
    patient_name: str,
    date_of_birth: str,
    phone: str,
    insurance_plan: str = "SELF_PAY",
    member_id: str = "",
) -> dict:
    born = parse_date(date_of_birth)
    if born is None:
        return {"ok": False, "error": "date_of_birth must be YYYY-MM-DD"}
    if born > date.today():
        return {"ok": False, "error": "date_of_birth is in the future"}
    if len(patient_name.split()) < 2:
        return {"ok": False, "error": "patient_name must be a first and last name"}
    digits = re.sub(r"\D", "", phone)
    if not 7 <= len(digits) <= 11:
        return {"ok": False, "error": "phone must have 7 to 11 digits"}
    plan = insurance_plan.upper()
    if plan != "SELF_PAY" and plan not in data.PLANS:
        return {"ok": False, "error": f"unknown insurance_plan; use one of {sorted(data.PLANS)} or SELF_PAY"}
    if plan != "SELF_PAY" and not member_id:
        return {"ok": False, "error": "member_id is required for an insured patient"}
    with data.LOCK:
        if find_patient(patient_name, date_of_birth) is not None:
            return {"ok": False, "error": "this patient is already registered"}
        patient = {
            "id": f"P{len(data.PATIENTS) + 1:03d}",
            "name": " ".join(patient_name.split()),
            "date_of_birth": date_of_birth,
            "phone": digits,
            "insurance_plan": plan,
            "member_id": member_id if plan != "SELF_PAY" else "",
        }
        data.PATIENTS[patient["id"]] = patient
    return {"ok": True, "patient": patient}
