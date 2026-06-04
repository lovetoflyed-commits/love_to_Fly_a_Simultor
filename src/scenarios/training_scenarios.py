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

TERRAIN_AWARENESS_SBGR = {
    "name": "Terrain Awareness – SBGR Area",
    "events": [
        # Initial orientation
        {"trigger_time_sec": 3,  "event_type": "atc_message", "params": {"text": "São Paulo Approach: radar contact. Terrain in your area, highest obstacle 4200 ft MSL SE."}},
        # Clearance to fly northbound toward Serra da Cantareira
        {"trigger_time_sec": 10, "event_type": "heading",     "params": {"heading": 330}},
        {"trigger_time_sec": 10, "event_type": "altitude",    "params": {"altitude": 4500}},
        {"trigger_time_sec": 10, "event_type": "atc_message", "params": {"text": "Turn heading 330, climb maintain 4500. Traffic and terrain – Serra da Cantareira peaks at 3937 ft, 12 o'clock, 15 NM."}},
        # Terrain warning as aircraft approaches hills
        {"trigger_time_sec": 40, "event_type": "atc_message", "params": {"text": "Terrain alert: Serra da Cantareira 3 NM ahead. Climb to 4800 or turn right heading 360."}},
        {"trigger_time_sec": 50, "event_type": "heading",     "params": {"heading": 360}},
        {"trigger_time_sec": 50, "event_type": "altitude",    "params": {"altitude": 4800}},
        # Turn westbound toward Pico do Jaraguá
        {"trigger_time_sec": 80, "event_type": "atc_message", "params": {"text": "Turn left heading 270. Pico do Jaraguá, 3724 ft, 20 NM ahead. Communication towers extend to 3950 ft on that peak."}},
        {"trigger_time_sec": 80, "event_type": "heading",     "params": {"heading": 270}},
        # Low-level pass north of SBSP
        {"trigger_time_sec": 120, "event_type": "atc_message", "params": {"text": "Descend to 3500. Note obstacles: tower at Pico do Jaraguá 3950 ft, maintain terrain separation."}},
        {"trigger_time_sec": 120, "event_type": "altitude",   "params": {"altitude": 3500}},
        # Return to SBGR
        {"trigger_time_sec": 160, "event_type": "atc_message", "params": {"text": "Turn right heading 100. Expect ILS 10R SBGR. Descend to 3000."}},
        {"trigger_time_sec": 160, "event_type": "heading",    "params": {"heading": 100}},
        {"trigger_time_sec": 160, "event_type": "altitude",   "params": {"altitude": 3000}},
        {"trigger_time_sec": 160, "event_type": "grade_approach", "params": {}},
        {"trigger_time_sec": 200, "event_type": "atc_message", "params": {"text": "Cleared ILS 10R SBGR. Minimum safe altitude in sector 3200 ft. Terrain clear on current track."}},
    ],
}
