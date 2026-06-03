ILS_APPROACH = {
    "name": "ILS 10R SBGR",
    "events": [
        {"trigger_time_sec": 1, "event_type": "atc_message", "params": {"text": "Expect ILS runway 10R, ceiling 500 feet, visibility 1 mile."}},
        {"trigger_time_sec": 15, "event_type": "heading", "params": {"heading": 100}},
        {"trigger_time_sec": 30, "event_type": "atc_message", "params": {"text": "Maintain 5000 until established, cleared ILS 10R."}},
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
        {"trigger_time_sec": 5, "event_type": "atc_message", "params": {"text": "Hold east of GRU VOR on the 090 radial, right turns."}},
        {"trigger_time_sec": 10, "event_type": "failure", "params": {"failure": "VACUUM", "severity": 0.7}},
        {"trigger_time_sec": 10, "event_type": "grade_hold", "params": {}},
    ],
}

PARTIAL_PANEL = {
    "name": "Partial Panel Recovery",
    "events": [
        {"trigger_time_sec": 5, "event_type": "failure", "params": {"failure": "VACUUM", "severity": 1.0}},
        {"trigger_time_sec": 8, "event_type": "atc_message", "params": {"text": "Vacuum system failure. Continue partial panel and maintain control."}},
    ],
}

MISSED_APPROACH = {
    "name": "Missed Approach SBGR",
    "events": [
        {"trigger_time_sec": 2, "event_type": "atc_message", "params": {"text": "Cleared ILS 10R. Missed approach: fly runway heading, climb 3000."}},
        {"trigger_time_sec": 10, "event_type": "atc_message", "params": {"text": "Go around. Fly runway heading, climb and maintain 3000 feet."}},
        {"trigger_time_sec": 12, "event_type": "heading", "params": {"heading": 100}},
        {"trigger_time_sec": 12, "event_type": "altitude", "params": {"altitude": 3000}},
        {"trigger_time_sec": 12, "event_type": "grade_approach", "params": {}},
        {"trigger_time_sec": 40, "event_type": "atc_message", "params": {"text": "Radar contact. Expect vectors for another ILS. Maintain 3000."}},
    ],
}

DIVERSION = {
    "name": "Weather Diversion",
    "events": [
        {"trigger_time_sec": 5, "event_type": "atc_message", "params": {"text": "SBGR is below minimums. Suggest diversion to SBSP. Distance approx 18 NM."}},
        {"trigger_time_sec": 10, "event_type": "heading", "params": {"heading": 220}},
        {"trigger_time_sec": 10, "event_type": "altitude", "params": {"altitude": 4000}},
        {"trigger_time_sec": 30, "event_type": "atc_message", "params": {"text": "Cleared direct SBSP, ILS 17R. Descend to 3500 feet."}},
    ],
}
