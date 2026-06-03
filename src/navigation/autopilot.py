from __future__ import annotations

from enum import Enum, auto
import math

from .vor import VORReceiver
from .gps import GPS
from ..models.flight_plan import FlightPlan


class APMode(Enum):
    OFF = auto()
    HDG = auto()
    ALT = auto()
    VS = auto()
    LNAV = auto()
    VNAV = auto()
    APP = auto()


class Autopilot:
    def __init__(self) -> None:
        self.lateral_mode = APMode.OFF
        self.vertical_mode = APMode.OFF
        self.target_heading = 0.0
        self.target_altitude = 0.0
        self.target_vs = 0.0
        self.target_course = 0.0
        self._heading_integrator = 0.0
        self._altitude_integrator = 0.0

    def engage(self, mode: APMode) -> None:
        if mode == APMode.OFF:
            self.lateral_mode = APMode.OFF
            self.vertical_mode = APMode.OFF
        elif mode in {APMode.HDG, APMode.LNAV, APMode.APP}:
            self.lateral_mode = mode
            if mode == APMode.APP:
                self.vertical_mode = APMode.APP
        else:
            self.vertical_mode = mode

    def set_target(self, heading: float | None = None, altitude: float | None = None, vs: float | None = None) -> None:
        if heading is not None:
            self.target_heading = heading % 360.0
        if altitude is not None:
            self.target_altitude = altitude
        if vs is not None:
            self.target_vs = vs

    @property
    def active_modes(self) -> list[str]:
        modes = []
        if self.lateral_mode != APMode.OFF:
            modes.append(self.lateral_mode.name)
        if self.vertical_mode != APMode.OFF and self.vertical_mode != self.lateral_mode:
            modes.append(self.vertical_mode.name)
        return modes or ["OFF"]

    def compute_controls(
        self,
        state: dict,
        flight_plan: FlightPlan | None,
        gps: GPS | None,
        _vor_receiver: VORReceiver | None,
        dt: float,
    ) -> dict[str, float]:
        dt = max(dt, 1e-3)
        roll = float(state.get("roll_deg", 0.0))
        heading = float(state.get("heading_deg", 0.0))
        altitude = float(state.get("altitude_ft", 0.0))
        vertical_speed = float(state.get("vertical_speed_fpm", 0.0))

        desired_heading = self.target_heading
        if self.lateral_mode == APMode.LNAV and gps is not None:
            desired_heading = gps.bearing_to_next_deg - gps.cross_track_error_nm * 8.0
        heading_error = ((desired_heading - heading + 540.0) % 360.0) - 180.0
        self._heading_integrator += heading_error * dt
        desired_bank = max(-25.0, min(25.0, 0.6 * heading_error + 0.02 * self._heading_integrator))
        aileron = 0.0 if self.lateral_mode == APMode.OFF else max(-1.0, min(1.0, (desired_bank - roll) / 20.0))

        if self.vertical_mode == APMode.ALT:
            alt_error = self.target_altitude - altitude
            self.target_vs = max(-700.0, min(700.0, alt_error * 0.5))
        elif self.vertical_mode == APMode.VNAV and flight_plan is not None and flight_plan.active_waypoint() is not None:
            target_altitude = flight_plan.active_waypoint().altitude_ft or self.target_altitude
            self.target_vs = max(-800.0, min(800.0, (target_altitude - altitude) * 0.4))
        elevator = 0.0
        if self.vertical_mode != APMode.OFF:
            vs_error = self.target_vs - vertical_speed
            self._altitude_integrator += vs_error * dt
            elevator = max(-1.0, min(1.0, vs_error / 1200.0 + self._altitude_integrator / 8000.0))
        return {"elevator": elevator, "aileron": aileron, "rudder": max(-0.3, min(0.3, -roll / 45.0))}
