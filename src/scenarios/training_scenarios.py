ILS_APPROACH = {
    "name": "ILS 28L KSFO",
    "events": [
        {"trigger_time_sec": 1, "event_type": "atc_message", "params": {"text": "Expect ILS runway 28L, ceiling 500 feet, visibility 1 mile."}},
        {"trigger_time_sec": 15, "event_type": "heading", "params": {"heading": 280}},
        {"trigger_time_sec": 30, "event_type": "atc_message", "params": {"text": "Maintain 3000 until established, cleared ILS 28L."}},
    ],
}

ENGINE_FAILURE_SCENARIO = {
    "name": "Engine Failure Diversion",
    "events": [
        {"trigger_time_sec": 20, "event_type": "failure", "params": {"failure": "ENGINE_FAILURE", "severity": 1.0}},
        {"trigger_time_sec": 21, "event_type": "atc_message", "params": {"text": "Engine failure reported. Nearest suitable airport available for diversion."}},
    ],
}

HOLDING_PATTERN = {
    "name": "Holding Partial Panel",
    "events": [
        {"trigger_time_sec": 5, "event_type": "atc_message", "params": {"text": "Hold east of SFO VOR on the 090 radial, right turns."}},
        {"trigger_time_sec": 10, "event_type": "failure", "params": {"failure": "VACUUM", "severity": 0.7}},
    ],
}

PARTIAL_PANEL = {
    "name": "Partial Panel Recovery",
    "events": [
        {"trigger_time_sec": 5, "event_type": "failure", "params": {"failure": "VACUUM", "severity": 1.0}},
        {"trigger_time_sec": 8, "event_type": "atc_message", "params": {"text": "Vacuum system failure. Continue partial panel and maintain control."}},
    ],
}
