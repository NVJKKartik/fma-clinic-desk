"""Providers, availability, booking, rescheduling, cancellation and the waitlist."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import config
import data
import patients

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _start(day_text: str, time_text: str) -> datetime:
    return datetime.fromisoformat(f"{day_text}T{time_text}")


def _end(appointment: dict) -> datetime:
    start = _start(appointment["date"], appointment["time"])
    return start + timedelta(minutes=appointment.get("minutes", config.APPOINTMENT_MINUTES["consult"]))


def _overlaps(appointment: dict, start: datetime, end: datetime) -> bool:
    return _start(appointment["date"], appointment["time"]) < end and start < _end(appointment)


def _clash(start: datetime, minutes: int, *, provider_id: str = "", patient_id: str = "", ignore_id: str = "") -> bool:
    end = start + timedelta(minutes=minutes)
    for other in data.APPOINTMENTS.values():
        if other["id"] == ignore_id or other["date"] != start.date().isoformat():
            continue
        if provider_id and other["provider_id"] != provider_id:
            continue
        if patient_id and other["patient_id"] != patient_id:
            continue
        if _overlaps(other, start, end):
            return True
    return False


def _parse_day(day_text: str) -> date | None:
    try:
        return date.fromisoformat(day_text)
    except (TypeError, ValueError):
        return None


def _parse_time(time_text: str) -> datetime | None:
    try:
        return datetime.strptime(time_text, "%H:%M")
    except (TypeError, ValueError):
        return None


def _window(provider: dict, day: date) -> tuple[str, str] | str:
    """The provider's working window on a day, or the reason there is none."""
    hours = config.HOURS.get(day.weekday())
    if hours is None:
        return "the clinic is closed on Sundays"
    if day.weekday() not in provider["works"]:
        days = ", ".join(DAY_NAMES[d] for d in provider["works"])
        return f"{provider['name']} does not see patients on {DAY_NAMES[day.weekday()]}; works {days}"
    return hours


def _free_starts(provider: dict, day: date, minutes: int) -> list[str]:
    window = _window(provider, day)
    if isinstance(window, str):
        return []
    opens, closes = (datetime.combine(day, datetime.strptime(t, "%H:%M").time()) for t in window)
    now = datetime.now()
    starts = []
    cursor = opens
    while cursor + timedelta(minutes=minutes) <= closes:
        if cursor > now and not _clash(cursor, minutes, provider_id=provider["id"]):
            starts.append(cursor.strftime("%H:%M"))
        cursor += timedelta(minutes=config.SLOT_MINUTES)
    return starts


def _next_day_with_slots(provider: dict, after: date, minutes: int) -> str | None:
    for offset in range(1, 29):
        day = after + timedelta(days=offset)
        if _free_starts(provider, day, minutes):
            return day.isoformat()
    return None


def list_providers(specialty: str = "") -> dict:
    found = [
        {
            "id": p["id"],
            "name": p["name"],
            "specialty": p["specialty"],
            "works_on": [DAY_NAMES[d] for d in p["works"]],
            "patients": {"all": "all ages", "under18": "under 18 only", "adult": "18 and over"}[p["ages"]],
        }
        for p in data.PROVIDERS.values()
        if not specialty or specialty.lower() in p["specialty"].lower()
    ]
    return {"ok": True, "providers": found, "appointment_minutes": config.APPOINTMENT_MINUTES}


def check_availability(provider_id: str, date: str, appointment_type: str) -> dict:  # noqa: A002
    provider = data.PROVIDERS.get(provider_id)
    if provider is None:
        return {"ok": False, "error": f"unknown provider_id {provider_id}"}
    day = _parse_day(date)
    if day is None:
        return {"ok": False, "error": "date must be YYYY-MM-DD"}
    minutes = config.APPOINTMENT_MINUTES[appointment_type]
    with data.LOCK:
        window = _window(provider, day)
        slots = _free_starts(provider, day, minutes)
        result = {
            "ok": True,
            "provider": provider["name"],
            "date": day.isoformat(),
            "appointment_type": appointment_type,
            "duration_minutes": minutes,
            "slots": slots,
            "fully_booked": not slots and not isinstance(window, str) and day >= date_today(),
        }
        if isinstance(window, str):
            result["unavailable_reason"] = window
        if not slots:
            result["next_date_with_slots"] = _next_day_with_slots(provider, max(day, date_today()), minutes)
        return result


def date_today() -> date:
    return datetime.now().date()


def _check_booking(
    patient: dict, provider: dict, day_text: str, time_text: str, appointment_type: str, ignore_id: str = ""
) -> str | None:
    day = _parse_day(day_text)
    clock = _parse_time(time_text)
    if day is None or clock is None:
        return "date must be YYYY-MM-DD and time must be HH:MM (24h)"
    minutes = config.APPOINTMENT_MINUTES[appointment_type]
    start = datetime.combine(day, clock.time())
    if start <= datetime.now():
        return "that time has already passed"
    window = _window(provider, day)
    if isinstance(window, str):
        return window
    opens = datetime.combine(day, datetime.strptime(window[0], "%H:%M").time())
    closes = datetime.combine(day, datetime.strptime(window[1], "%H:%M").time())
    if start < opens or start + timedelta(minutes=minutes) > closes:
        return f"a {minutes}-minute {appointment_type.replace('_', ' ')} must fit between {window[0]} and {window[1]} that day"
    if clock.minute % config.SLOT_MINUTES:
        return f"appointments start on a {config.SLOT_MINUTES}-minute mark"
    age = patients.age_on(date.fromisoformat(patient["date_of_birth"]))
    if provider["ages"] == "under18" and age >= 18:
        return f"{provider['name']} sees patients under 18 only"
    if provider["ages"] == "adult" and age < 18:
        return f"{provider['name']} sees patients 18 and over only"
    if _clash(start, minutes, provider_id=provider["id"], ignore_id=ignore_id):
        return "that time is not free with this provider"
    if _clash(start, minutes, patient_id=patient["id"], ignore_id=ignore_id):
        return "the patient already has an appointment at that time"
    return None


def _patient_or_error(patient_name: str, date_of_birth: str) -> tuple[dict | None, dict | None]:
    patient = patients.find_patient(patient_name, date_of_birth)
    if patient is None:
        return None, {"ok": False, "error": "no patient found with that name and date of birth"}
    return patient, None


def book_appointment(
    patient_name: str, date_of_birth: str, provider_id: str, date: str, time: str, appointment_type: str, reason: str
) -> dict:  # noqa: A002
    provider = data.PROVIDERS.get(provider_id)
    if provider is None:
        return {"ok": False, "error": f"unknown provider_id {provider_id}"}
    with data.LOCK:
        patient, error = _patient_or_error(patient_name, date_of_birth)
        if error:
            return error
        problem = _check_booking(patient, provider, date, time, appointment_type)
        if problem:
            return {"ok": False, "error": problem}
        appointment = {
            "id": f"A{len(data.APPOINTMENTS) + 1:03d}",
            "patient_id": patient["id"],
            "provider_id": provider_id,
            "date": date,
            "time": time,
            "appointment_type": appointment_type,
            "duration_minutes": config.APPOINTMENT_MINUTES[appointment_type],
            "reason": reason,
        }
        data.APPOINTMENTS[appointment["id"]] = appointment
        return {"ok": True, "appointment": patients.public_appointment(appointment)}


def _owned(appointment_id: str, patient: dict) -> dict | None:
    found = data.APPOINTMENTS.get(appointment_id)
    return found if found and found["patient_id"] == patient["id"] else None


def reschedule_appointment(
    appointment_id: str, patient_name: str, date_of_birth: str, new_date: str, new_time: str
) -> dict:
    with data.LOCK:
        patient, error = _patient_or_error(patient_name, date_of_birth)
        if error:
            return error
        found = _owned(appointment_id, patient)
        if found is None:
            return {"ok": False, "error": "no such appointment for this patient"}
        problem = _check_booking(
            patient,
            data.PROVIDERS[found["provider_id"]],
            new_date,
            new_time,
            found["appointment_type"],
            ignore_id=appointment_id,
        )
        if problem:
            return {"ok": False, "error": problem}
        found["date"], found["time"] = new_date, new_time
        return {"ok": True, "appointment": patients.public_appointment(found), "fee": 0}


def cancel_appointment(appointment_id: str, patient_name: str, date_of_birth: str) -> dict:
    with data.LOCK:
        patient, error = _patient_or_error(patient_name, date_of_birth)
        if error:
            return error
        found = _owned(appointment_id, patient)
        if found is None:
            return {"ok": False, "error": "no such appointment for this patient"}
        until = _start(found["date"], found["time"]) - datetime.now()
        if until <= timedelta(0):
            return {"ok": False, "error": "that appointment has already started or passed"}
        hours_until = until.total_seconds() / 3600
        fee = config.CANCELLATION_FEE if hours_until < config.CANCELLATION_WINDOW_HOURS else 0
        del data.APPOINTMENTS[appointment_id]
        return {"ok": True, "cancelled": patients.public_appointment(found), "fee": fee}


def join_waitlist(patient_name: str, date_of_birth: str, provider_id: str, date: str, appointment_type: str) -> dict:  # noqa: A002
    provider = data.PROVIDERS.get(provider_id)
    if provider is None:
        return {"ok": False, "error": f"unknown provider_id {provider_id}"}
    day = _parse_day(date)
    if day is None:
        return {"ok": False, "error": "date must be YYYY-MM-DD"}
    with data.LOCK:
        patient, error = _patient_or_error(patient_name, date_of_birth)
        if error:
            return error
        if day <= date_today():
            return {"ok": False, "error": "the waitlist is for future dates only"}
        window = _window(provider, day)
        if isinstance(window, str):
            return {"ok": False, "error": window}
        minutes = config.APPOINTMENT_MINUTES[appointment_type]
        if _free_starts(provider, day, minutes):
            return {"ok": False, "error": "that day still has free slots; book one instead"}
        queue = [w for w in data.WAITLIST if w["provider_id"] == provider_id and w["date"] == day.isoformat()]
        if any(w["patient_id"] == patient["id"] for w in queue):
            return {"ok": False, "error": "the patient is already on this waitlist"}
        entry = {
            "id": f"W{len(data.WAITLIST) + 1:03d}",
            "patient_id": patient["id"],
            "provider_id": provider_id,
            "date": day.isoformat(),
            "appointment_type": appointment_type,
        }
        data.WAITLIST.append(entry)
        return {"ok": True, "waitlist": {**entry, "provider": provider["name"], "position": len(queue) + 1}}
