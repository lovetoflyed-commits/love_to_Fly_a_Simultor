from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class GradeReport:
    scenario_name: str
    duration_sec: float
    track_rms_nm: float
    altitude_rms_ft: float
    checklist_pct: float
    approaches_flown: int
    holds_flown: int
    grade: str
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"── Debrief: {self.scenario_name} ──",
            f"Duration     : {self.duration_sec / 60:.1f} min",
            f"Track error  : {self.track_rms_nm:.2f} NM RMS",
            f"Alt error    : {self.altitude_rms_ft:.0f} ft RMS",
            f"Checklist    : {self.checklist_pct:.0f}%",
            f"Approaches   : {self.approaches_flown}",
            f"Grade        : {self.grade}",
        ]
        for note in self.notes:
            lines.append(f"  • {note}")
        return "\n".join(lines)


class FlightGrader:
    """Accumulates flight performance metrics and produces a GradeReport."""

    _MAX_SAMPLES = 18_000  # 5 minutes at 60 Hz

    def __init__(self, scenario_name: str = "Free Flight") -> None:
        self.scenario_name = scenario_name
        self._track_errors: list[float] = []
        self._altitude_errors: list[float] = []
        self._target_altitude: float | None = None
        self._checklist_items_total = 0
        self._checklist_items_done = 0
        self.approaches_flown = 0
        self.holds_flown = 0
        self._time_sec = 0.0
        self._notes: list[str] = []

    def set_target_altitude(self, altitude_ft: float) -> None:
        self._target_altitude = altitude_ft

    def record_approach(self) -> None:
        self.approaches_flown += 1

    def record_hold(self) -> None:
        self.holds_flown += 1

    def add_note(self, note: str) -> None:
        if note not in self._notes:
            self._notes.append(note)

    def update(self, state: dict, dt: float) -> None:
        self._time_sec += dt
        xte = float(state.get("cross_track_error_nm", 0.0))
        if len(self._track_errors) < self._MAX_SAMPLES:
            self._track_errors.append(xte ** 2)

        if self._target_altitude is not None:
            alt_err = float(state.get("altitude_ft", self._target_altitude)) - self._target_altitude
            if len(self._altitude_errors) < self._MAX_SAMPLES:
                self._altitude_errors.append(alt_err ** 2)

        # Stall detection
        if bool(state.get("stall_warning", False)):
            self.add_note("Stall warning activated during flight")

        # Low altitude
        if float(state.get("altitude_ft", 9999.0)) < 200.0:
            self.add_note("Altitude below 200 ft AGL")

    def set_checklist_progress(self, done: int, total: int) -> None:
        self._checklist_items_done = done
        self._checklist_items_total = total

    def generate_report(self) -> GradeReport:
        track_rms = math.sqrt(sum(self._track_errors) / max(1, len(self._track_errors)))
        alt_rms = math.sqrt(sum(self._altitude_errors) / max(1, len(self._altitude_errors))) if self._altitude_errors else 0.0
        checklist_pct = (self._checklist_items_done / max(1, self._checklist_items_total)) * 100.0

        grade = self._compute_grade(track_rms, alt_rms, checklist_pct)

        return GradeReport(
            scenario_name=self.scenario_name,
            duration_sec=self._time_sec,
            track_rms_nm=track_rms,
            altitude_rms_ft=alt_rms,
            checklist_pct=checklist_pct,
            approaches_flown=self.approaches_flown,
            holds_flown=self.holds_flown,
            grade=grade,
            notes=list(self._notes),
        )

    @staticmethod
    def _compute_grade(track_rms: float, alt_rms: float, checklist_pct: float) -> str:
        score = 100.0
        # Track error penalties (per NM RMS)
        if track_rms > 2.0:
            score -= 30.0
        elif track_rms > 1.0:
            score -= 15.0
        elif track_rms > 0.5:
            score -= 5.0
        # Altitude error penalties
        if alt_rms > 300.0:
            score -= 25.0
        elif alt_rms > 150.0:
            score -= 10.0
        elif alt_rms > 50.0:
            score -= 3.0
        # Checklist bonus/penalty
        score += (checklist_pct - 50.0) * 0.2

        score = max(0.0, min(100.0, score))
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 50:
            return "D"
        return "F"
