"""Clinic FAQ answers."""

from __future__ import annotations

import config

TOPICS = ["hours", "location", "what_to_bring", "cancellation_policy", "parking", "contact"]


def get_clinic_info(topic: str) -> dict:
    answers = {
        "hours": config.HOURS_TEXT,
        "location": f"Maple Street Clinic, {config.ADDRESS}. We are on the ground floor, next to the pharmacy.",
        "what_to_bring": (
            "Photo ID, your insurance card, and a list of the medicines you take. Bring the referral letter "
            "if your plan requires one for the visit. New patients should arrive 15 minutes early."
        ),
        "cancellation_policy": (
            f"Cancelling more than {config.CANCELLATION_WINDOW_HOURS} hours ahead is free. Cancelling inside "
            f"{config.CANCELLATION_WINDOW_HOURS} hours of the appointment costs ${config.CANCELLATION_FEE}. "
            "Rescheduling is free."
        ),
        "parking": "Free parking in the lot behind the building. Street parking nearby is limited to 2 hours.",
        "contact": f"Phone {config.PHONE}. Staff are available during opening hours.",
    }
    if topic not in answers:
        return {"ok": False, "error": f"unknown topic; use one of {TOPICS}"}
    return {"ok": True, "topic": topic, "answer": answers[topic]}
