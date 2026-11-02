# Maple Street Clinic front-desk agent

A text-chat agent for a small clinic front desk, written in plain Python with the standard library
only (no framework). It started from the
[fix-my-agent-e2e](https://github.com/NVJKKartik/fix-my-agent-e2e) sample agent and keeps its HTTP
contract.

It can:

- look up a patient by full name and date of birth, and register new patients
- check insurance eligibility against seeded plans: co-pay, and whether a referral is needed
- list providers by specialty and show free slots per provider and visit type
- book, reschedule and cancel appointments (cancelling inside 24 hours costs a fee)
- put callers on a waitlist for a fully booked day
- answer clinic questions: hours, location, what to bring, parking, cancellation policy

Opening hours: Monday to Friday 08:00-18:00, Saturday 09:00-13:00, closed on Sunday.
Visit types: consult (30 min), physical (60 min), follow-up (15 min).

## Layout

| File | Purpose |
| --- | --- |
| `agent.py` | HTTP server and the model/tool loop |
| `instructions.md` | System prompt and clinic policies |
| `tools.py` | Tool names, descriptions, argument schemas and argument checks |
| `scheduling.py`, `patients.py`, `insurance.py`, `faq.py` | Tool logic |
| `data.py`, `seed.py` | Providers, plans and the seeded in-memory data |
| `config.py` | Settings: model temperature, tool rounds, history window, hours, fee |

## Tools

`get_clinic_info`, `list_providers`, `lookup_patient`, `register_patient`, `check_insurance`,
`check_availability`, `book_appointment`, `reschedule_appointment`, `cancel_appointment`, `join_waitlist`.

## Run

```
export LLM_BASE_URL=https://api.openai.com/v1   # any OpenAI-compatible endpoint
export LLM_API_KEY=...
export LLM_MODEL=...                            # a model that supports tool calling
python agent.py
```

Python 3.10 or newer. No packages to install.

The agent serves `POST /v1/chat/completions` (also `/chat/completions`; OpenAI chat format, full
message history in each request, no streaming) and `GET /health`. Each reply also lists the tools it
ran in `completed_tools`: one object per call with `id`, `name`, `arguments`, `result` and `error`.

## Environment variables

| Name | Required | Purpose |
| --- | --- | --- |
| `LLM_BASE_URL` | yes | Base URL of the OpenAI-compatible API, ending in `/v1` |
| `LLM_API_KEY` | yes | API key for that endpoint |
| `LLM_MODEL` | yes | Model name |
| `PORT` | no | Listen port, default `8080` |

## Seeded data (for manual testing)

Providers: D1 Dr. Anita Rao and D2 Dr. Marcus Lee (Family Medicine), D3 Dr. Elena Petrova
(Pediatrics, under 18), D4 Dr. James Okafor (Cardiology, adults), D5 Dr. Sofia Mendes (Dermatology).

Plans: BLUE_PPO, SILVER_HMO, GOLD_EPO, MEDICARE_ADV, and OLDCARE_LEGACY (inactive), or SELF_PAY.

| Patient | Date of birth | Plan | Member id |
| --- | --- | --- | --- |
| Priya Sharma | 1988-03-14 | BLUE_PPO | BSP123456 |
| Daniel Okoye | 1975-11-02 | SILVER_HMO | SHM204455 |
| Maria Gonzalez | 1992-07-21 | SELF_PAY | |
| Tom Becker | 2016-05-09 | GOLD_EPO | GEP778899 |
| Lena Fischer | 1951-01-30 | MEDICARE_ADV | MCA330011 |

Appointments are placed relative to today. Priya has two upcoming appointments, Maria has one less
than 24 hours away, and some provider days are fully booked. State is in memory and resets when the
server restarts.
