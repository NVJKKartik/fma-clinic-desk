"""Settings for the Maple Street Clinic front-desk agent."""

TEMPERATURE = 0.2
MAX_TOOL_ROUNDS = 4
HISTORY_MESSAGES = 6
LLM_TIMEOUT_SECONDS = 90

SLOT_MINUTES = 15
APPOINTMENT_MINUTES = {"consult": 30, "physical": 60, "follow_up": 15}

CANCELLATION_WINDOW_HOURS = 24
CANCELLATION_FEE = 40

# weekday() -> (opens, closes); Sunday is closed.
HOURS = {
    0: ("08:00", "18:00"),
    1: ("08:00", "18:00"),
    2: ("08:00", "18:00"),
    3: ("08:00", "18:00"),
    4: ("08:00", "18:00"),
    5: ("09:00", "13:00"),
}
HOURS_TEXT = "Monday to Friday 08:00-18:00, Saturday 09:00-13:00, closed on Sunday."

ADDRESS = "214 Maple Street, Suite 3, Springfield"
PHONE = "555-0100"
