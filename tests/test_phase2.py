"""Tests for new Phase 2 features: grader, scenarios, CDI, main_menu."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.scenarios.grader import FlightGrader, GradeReport
from src.scenarios.training_scenarios import (
    MISSED_APPROACH,
    DIVERSION,
    HOLDING_PATTERN,
    ILS_APPROACH,
)
from src.navigation.autopilot import APMode, Autopilot, SBGR_ILS_10R
from src.models.position import Position
from src.ui.main_menu import MainMenu


# ── Grader tests ─────────────────────────────────────────────────────────────

def test_grader_perfect_score():
    grader = FlightGrader(scenario_name="Test")
    grader.set_target_altitude(3000.0)
    for _ in range(60):
        grader.update({"altitude_ft": 3000.0, "cross_track_error_nm": 0.0}, dt=1.0)
    report = grader.generate_report()
    assert report.grade == "A"
    assert report.altitude_rms_ft < 1.0
    assert report.track_rms_nm < 0.1


def test_grader_large_deviations_fail():
    grader = FlightGrader(scenario_name="Test")
    grader.set_target_altitude(3000.0)
    for _ in range(60):
        grader.update({"altitude_ft": 4500.0, "cross_track_error_nm": 5.0}, dt=1.0)
    report = grader.generate_report()
    assert report.grade in {"D", "F"}
    assert report.altitude_rms_ft > 100.0


def test_grader_report_contains_fields():
    grader = FlightGrader(scenario_name="Test")
    grader.set_target_altitude(5000.0)
    grader.update({"altitude_ft": 5050.0, "cross_track_error_nm": 0.1}, dt=1.0)
    report = grader.generate_report()
    assert hasattr(report, "grade")
    assert hasattr(report, "altitude_rms_ft")
    assert hasattr(report, "track_rms_nm")
    assert hasattr(report, "checklist_pct")
    assert isinstance(report.summary(), str)


# ── Scenario structure tests ──────────────────────────────────────────────────

def test_missed_approach_scenario_has_events():
    assert len(MISSED_APPROACH["events"]) > 0


def test_diversion_scenario_has_events():
    assert len(DIVERSION["events"]) > 0


def test_missed_approach_scenario_has_grade_event():
    grade_events = [e for e in MISSED_APPROACH["events"] if e.get("event_type") == "grade_approach"]
    assert len(grade_events) > 0, "MISSED_APPROACH must contain a grade_approach event"


def test_holding_pattern_scenario_loads():
    assert HOLDING_PATTERN["name"]
    assert len(HOLDING_PATTERN["events"]) > 0


# ── Autopilot APP mode ────────────────────────────────────────────────────────

def test_autopilot_app_mode_engages():
    ap = Autopilot()
    ap.engage(APMode.APP)
    assert "APP" in ap.active_modes


def test_autopilot_ils_provides_roll_command():
    ap = Autopilot()
    ap.engage(APMode.APP)

    pos = Position(-23.30, -46.50, 2500.0)
    state = {
        "heading_deg": 80.0,
        "roll_deg": 0.0,
        "pitch_deg": 0.0,
        "altitude_ft": 2500.0,
        "vertical_speed_fpm": 0.0,
        "position": pos,
    }

    class _FakeGPS:
        bearing_to_next_deg = 100.0
        cross_track_error_nm = 0.0

    class _FakePlan:
        active_leg: int = 0
        def __init__(self): self.waypoints = []
        def active_waypoint(self):
            return None

    class _FakeVOR:
        def get_bearing_to(self, p):
            return 0.0

    controls = ap.compute_controls(state, _FakePlan(), _FakeGPS(), _FakeVOR(), 0.016)
    assert "aileron" in controls
    assert "elevator" in controls


# ── ILSLocalizer tests ────────────────────────────────────────────────────────

def test_ils_localizer_on_centreline():
    # Position 5 NM on final approach (280 deg bearing from threshold = on localizer course)
    pos = Position(-23.4105, -46.5744, 3000.0)
    dev = SBGR_ILS_10R.get_localizer_deviation(pos)
    assert abs(dev) < 0.1


def test_ils_glideslope_above_path():
    pos = Position(-23.37, -46.56, 8000.0)
    dev = SBGR_ILS_10R.get_glideslope_deviation(pos, altitude_ft=8000.0)
    assert dev > 0.0


# ── MainMenu tests ────────────────────────────────────────────────────────────

def test_main_menu_defaults():
    menu = MainMenu(1280, 720)
    assert not menu.done
    assert menu.selected_aircraft == "C152"
    assert menu.selected_scenario == "RUNWAY_START"


def test_main_menu_scenario_options_include_all():
    import pygame
    pygame.init()
    menu = MainMenu(1280, 720)
    scenario_names = [opt[0] for opt in menu._SCENARIO_OPTIONS]
    assert "RUNWAY_START" in scenario_names
    assert "ILS_APPROACH" in scenario_names
    assert "MISSED_APPROACH" in scenario_names
    assert "DIVERSION" in scenario_names
    pygame.quit()
