"""Insurance eligibility against the seeded plans."""

from __future__ import annotations

import re

import config
import data


def check_insurance(plan_id: str, member_id: str, provider_id: str, appointment_type: str) -> dict:
    provider = data.PROVIDERS.get(provider_id)
    if provider is None:
        return {"ok": False, "error": f"unknown provider_id {provider_id}"}
    if appointment_type not in config.APPOINTMENT_MINUTES:
        return {"ok": False, "error": f"unknown appointment_type {appointment_type}"}
    plan_id = plan_id.upper()
    if plan_id == "SELF_PAY":
        return {
            "ok": True,
            "eligible": False,
            "reason": "self-pay: no insurance on file",
            "self_pay_price": data.SELF_PAY_PRICES[appointment_type],
            "referral_required": False,
        }
    plan = data.PLANS.get(plan_id)
    if plan is None:
        return {"ok": False, "error": f"unknown plan_id {plan_id}"}
    if not plan["active"]:
        return {"ok": True, "eligible": False, "plan": plan["name"], "reason": "this plan is no longer active"}
    if not re.fullmatch(plan["prefix"] + r"\d{6}", member_id.upper()):
        return {"ok": True, "eligible": False, "plan": plan["name"], "reason": "member id is not valid for this plan"}
    is_specialist = provider["specialty"].lower() in data.SPECIALIST_SPECIALTIES
    copay = plan["specialist_copay"] if is_specialist else plan["copay"][appointment_type]
    referral = provider["specialty"] in plan["referral_specialties"]
    return {
        "ok": True,
        "eligible": True,
        "plan": plan["name"],
        "copay": copay,
        "referral_required": referral,
        "provider": provider["name"],
        "appointment_type": appointment_type,
    }
