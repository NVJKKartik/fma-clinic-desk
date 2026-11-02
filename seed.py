"""Deterministic starting data, placed relative to today's date."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import config
import data


def _next_working_day(provider_id: str, earliest: date) -> date:
    works = data.PROVIDERS[provider_id]["works"]
    day = earliest
    while day.weekday() not in works:
        day += timedelta(days=1)
    return day


def _patient(name: str, dob: str, phone: str, plan: str, member_id: str) -> None:
    patient_id = f"P{len(data.PATIENTS) + 1:03d}"
    data.PATIENTS[patient_id] = {
        "id": patient_id,
        "name": name,
        "date_of_birth": dob,
        "phone": phone,
        "insurance_plan": plan,
        "member_id": member_id,
    }


def _appointment(patient_id: str, provider_id: str, day: date, time: str, kind: str, reason: str) -> None:
    appointment_id = f"A{len(data.APPOINTMENTS) + 1:03d}"
    data.APPOINTMENTS[appointment_id] = {
        "id": appointment_id,
        "patient_id": patient_id,
        "provider_id": provider_id,
        "date": day.isoformat(),
        "time": time,
        "appointment_type": kind,
        "duration_minutes": config.APPOINTMENT_MINUTES[kind],
        "reason": reason,
    }


def _fill_day(provider_id: str, day: date) -> None:
    opens, closes = config.HOURS[day.weekday()]
    cursor = datetime.combine(day, datetime.strptime(opens, "%H:%M").time())
    end = datetime.combine(day, datetime.strptime(closes, "%H:%M").time())
    while cursor + timedelta(minutes=30) <= end:
        _appointment("P000", provider_id, day, cursor.strftime("%H:%M"), "consult", "booked")
        cursor += timedelta(minutes=30)


def seed() -> None:
    data.PATIENTS.clear()
    data.APPOINTMENTS.clear()
    data.WAITLIST.clear()
    today = date.today()

    _patient("Priya Sharma", "1988-03-14", "5550101", "BLUE_PPO", "BSP123456")
    _patient("Daniel Okoye", "1975-11-02", "5550102", "SILVER_HMO", "SHM204455")
    _patient("Maria Gonzalez", "1992-07-21", "5550103", "SELF_PAY", "")
    _patient("Tom Becker", "2016-05-09", "5550104", "GOLD_EPO", "GEP778899")
    _patient("Lena Fischer", "1951-01-30", "5550105", "MEDICARE_ADV", "MCA330011")

    rao_day = _next_working_day("D1", today + timedelta(days=2))
    _appointment("P001", "D1", rao_day, "10:00", "consult", "persistent cough")
    _appointment("P005", "D1", rao_day, "11:00", "physical", "annual physical")
    _appointment("P001", "D5", _next_working_day("D5", today + timedelta(days=9)), "09:30", "follow_up", "skin check")
    _appointment("P002", "D4", _next_working_day("D4", today + timedelta(days=3)), "14:00", "physical", "heart screening")
    _appointment("P004", "D3", _next_working_day("D3", today + timedelta(days=2)), "09:30", "follow_up", "ear infection")

    soon = datetime.now() + timedelta(hours=14)
    soon = soon.replace(hour=min(max(soon.hour, 8), 17), minute=0, second=0, microsecond=0)
    _appointment("P003", "D2", soon.date(), soon.strftime("%H:%M"), "consult", "back pain")

    _fill_day("D4", _next_working_day("D4", today + timedelta(days=8)))
    _fill_day("D5", _first_weekday(5, today + timedelta(days=3)))


def _first_weekday(weekday: int, earliest: date) -> date:
    day = earliest
    while day.weekday() != weekday:
        day += timedelta(days=1)
    return day
