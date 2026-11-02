"""Reference data and the in-memory state shared by all requests."""

from __future__ import annotations

import threading

LOCK = threading.RLock()

# works: weekday numbers (Monday = 0) on which the provider sees patients.
PROVIDERS = {
    "D1": {"id": "D1", "name": "Dr. Anita Rao", "specialty": "Family Medicine", "works": [0, 1, 2, 3, 4], "ages": "all"},
    "D2": {"id": "D2", "name": "Dr. Marcus Lee", "specialty": "Family Medicine", "works": [0, 2, 4], "ages": "all"},
    "D3": {"id": "D3", "name": "Dr. Elena Petrova", "specialty": "Pediatrics", "works": [1, 3, 5], "ages": "under18"},
    "D4": {"id": "D4", "name": "Dr. James Okafor", "specialty": "Cardiology", "works": [1, 3], "ages": "adult"},
    "D5": {"id": "D5", "name": "Dr. Sofia Mendes", "specialty": "Dermatology", "works": [0, 2, 5], "ages": "all"},
}

SPECIALIST_SPECIALTIES = {"cardiology", "dermatology"}

# copay: dollars per visit at a primary-care provider. specialist_copay: any visit with a specialist.
PLANS = {
    "BLUE_PPO": {
        "name": "BlueShield PPO", "active": True, "prefix": "BSP",
        "copay": {"consult": 25, "physical": 0, "follow_up": 15}, "specialist_copay": 50,
        "referral_specialties": [],
    },
    "SILVER_HMO": {
        "name": "Silver Health HMO", "active": True, "prefix": "SHM",
        "copay": {"consult": 20, "physical": 0, "follow_up": 10}, "specialist_copay": 40,
        "referral_specialties": ["cardiology", "dermatology"],
    },
    "GOLD_EPO": {
        "name": "Gold Care EPO", "active": True, "prefix": "GEP",
        "copay": {"consult": 15, "physical": 0, "follow_up": 10}, "specialist_copay": 35,
        "referral_specialties": ["cardiology"],
    },
    "MEDICARE_ADV": {
        "name": "Medicare Advantage Plus", "active": True, "prefix": "MCA",
        "copay": {"consult": 10, "physical": 0, "follow_up": 5}, "specialist_copay": 30,
        "referral_specialties": ["cardiology", "dermatology"],
    },
    "OLDCARE_LEGACY": {
        "name": "OldCare Legacy", "active": False, "prefix": "OLC",
        "copay": {"consult": 20, "physical": 0, "follow_up": 10}, "specialist_copay": 40,
        "referral_specialties": [],
    },
}

SELF_PAY_PRICES = {"consult": 90, "physical": 150, "follow_up": 50}

# State
PATIENTS: dict[str, dict] = {}
APPOINTMENTS: dict[str, dict] = {}
WAITLIST: list[dict] = []
