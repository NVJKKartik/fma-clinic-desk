"""Tool schemas shown to the model, argument validation, and the dispatch table."""

from __future__ import annotations

import config
import faq
import insurance
import patients
import scheduling

ALL_TYPES = list(config.APPOINTMENT_MINUTES)
BOOKABLE_TYPES = ["consult", "physical"]
PLAN_IDS = ["BLUE_PPO", "SILVER_HMO", "GOLD_EPO", "MEDICARE_ADV", "OLDCARE_LEGACY", "SELF_PAY"]

_NAME = {"type": "string", "description": "The patient's full name, first and last"}
_DOB = {"type": "string", "description": "Patient date of birth as YYYY-MM-DD"}
_DATE = {"type": "string", "description": "Calendar date as YYYY-MM-DD"}
_TIME = {"type": "string", "description": "Start time as HH:MM, 24-hour clock"}
_PROVIDER = {"type": "string", "description": "Provider id from list_providers, for example D1"}


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOLS = [
    _tool(
        "get_clinic_info",
        "Answer a clinic FAQ: opening hours, location, what to bring, cancellation policy, parking or contact.",
        {"topic": {"type": "string", "enum": faq.TOPICS, "description": "The FAQ topic"}},
        ["topic"],
    ),
    _tool(
        "list_providers",
        "List the clinic's providers with id, specialty, the weekdays they work and the ages they see. "
        "Optionally filter by specialty.",
        {"specialty": {"type": "string", "description": "Specialty to filter by, for example cardiology"}},
        [],
    ),
    _tool(
        "lookup_patient",
        "Verify a patient by full name and date of birth. Returns the patient record and their upcoming "
        "appointments with ids.",
        {"patient_name": _NAME, "date_of_birth": _DOB},
        ["patient_name", "date_of_birth"],
    ),
    _tool(
        "register_patient",
        "Register a new patient. Use only after lookup_patient found no match.",
        {
            "patient_name": _NAME,
            "date_of_birth": _DOB,
            "phone": {"type": "string", "description": "Contact phone number"},
            "insurance_plan": {"type": "string", "enum": PLAN_IDS, "description": "Plan id, or SELF_PAY"},
            "member_id": {"type": "string", "description": "Insurance member id; leave out for SELF_PAY"},
        },
        ["patient_name", "date_of_birth", "phone"],
    ),
    _tool(
        "check_insurance",
        "Check insurance eligibility for one visit: whether the plan is active and the member id is valid, "
        "the co-pay in dollars, and whether a referral is required for this provider.",
        {
            "plan_id": {"type": "string", "enum": PLAN_IDS, "description": "Plan id, or SELF_PAY"},
            "member_id": {"type": "string", "description": "Insurance member id; empty for SELF_PAY"},
            "provider_id": _PROVIDER,
            "appointment_type": {"type": "string", "enum": ALL_TYPES, "description": "Type of visit"},
        },
        ["plan_id", "member_id", "provider_id", "appointment_type"],
    ),
    _tool(
        "check_availability",
        "List the free start times for a provider on one date and appointment type. Also says whether the "
        "day is fully booked and the next date with free slots.",
        {
            "provider_id": _PROVIDER,
            "date": _DATE,
            "appointment_type": {
                "type": "string",
                "enum": BOOKABLE_TYPES,
                "description": "consult is 30 minutes, physical is 60 minutes, follow_up is 15 minutes",
            },
        },
        ["provider_id", "date", "appointment_type"],
    ),
    _tool(
        "book_appointment",
        "Book a new appointment for a registered patient. Fails if the slot is not free.",
        {
            "patient_name": _NAME,
            "date_of_birth": _DOB,
            "provider_id": _PROVIDER,
            "date": _DATE,
            "time": _TIME,
            "appointment_type": {
                "type": "string",
                "enum": BOOKABLE_TYPES,
                "description": "consult is 30 minutes, physical is 60 minutes, follow_up is 15 minutes",
            },
            "reason": {"type": "string", "description": "Short reason for the visit"},
        },
        ["patient_name", "date_of_birth", "provider_id", "date", "time", "appointment_type", "reason"],
    ),
    _tool(
        "reschedule_appointment",
        "Move an existing appointment to a new date and time with the same provider. Free of charge.",
        {
            "appointment_id": {"type": "string", "description": "Appointment id from lookup_patient, for example A001"},
            "patient_name": _NAME,
            "date_of_birth": _DOB,
            "new_date": _DATE,
            "new_time": _TIME,
        },
        ["appointment_id", "patient_name", "date_of_birth", "new_date", "new_time"],
    ),
    _tool(
        "cancel_appointment",
        "Cancel an existing appointment. The result includes the cancellation fee charged, which is 0 outside "
        "the cancellation window.",
        {
            "appointment_id": {"type": "string", "description": "Appointment id from lookup_patient, for example A001"},
            "patient_name": _NAME,
            "date_of_birth": _DOB,
        },
        ["appointment_id", "patient_name", "date_of_birth"],
    ),
    _tool(
        "join_waitlist",
        "Put a patient on the waitlist for a provider's fully booked day. Fails if the day still has free slots.",
        {
            "patient_name": _NAME,
            "date_of_birth": _DOB,
            "provider_id": _PROVIDER,
            "date": _DATE,
            "appointment_type": {"type": "string", "enum": BOOKABLE_TYPES, "description": "Type of visit wanted"},
        },
        ["patient_name", "date_of_birth", "provider_id", "date", "appointment_type"],
    ),
]

HANDLERS = {
    "get_clinic_info": faq.get_clinic_info,
    "list_providers": scheduling.list_providers,
    "lookup_patient": patients.lookup_patient,
    "register_patient": patients.register_patient,
    "check_insurance": insurance.check_insurance,
    "check_availability": scheduling.check_availability,
    "book_appointment": scheduling.book_appointment,
    "reschedule_appointment": scheduling.reschedule_appointment,
    "cancel_appointment": scheduling.cancel_appointment,
    "join_waitlist": scheduling.join_waitlist,
}

_SCHEMAS = {t["function"]["name"]: t["function"]["parameters"] for t in TOOLS}


def validate(name: str, arguments: object) -> str | None:
    """Return a message when the arguments do not match the tool's schema."""
    schema = _SCHEMAS.get(name)
    if schema is None:
        return f"unknown tool {name}"
    if not isinstance(arguments, dict):
        return "arguments must be a JSON object"
    for key in schema["required"]:
        if arguments.get(key) in (None, ""):
            if not (key == "member_id" and arguments.get("plan_id") == "SELF_PAY"):
                return f"missing required argument {key}"
    for key, value in arguments.items():
        spec = schema["properties"].get(key)
        if spec is None:
            return f"unexpected argument {key}"
        if not isinstance(value, str):
            return f"{key} must be a string"
        if "enum" in spec and value not in spec["enum"]:
            return f"{key} must be one of {spec['enum']}"
    return None


def run_tool(name: str, arguments: object) -> dict:
    problem = validate(name, arguments)
    if problem:
        return {"ok": False, "error": problem}
    return HANDLERS[name](**arguments)
