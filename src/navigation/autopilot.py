from __future__ import annotations

from enum import Enum, auto
import math

from .vor import ILSLocalizer, VORReceiver
from .gps import GPS
from ..models.flight_plan import FlightPlan

# ILS approach configuration for SBGR RW10R
SBGR_ILS_10R = ILSLocalizer(
    vor_lat=-23.4356,
    vor_lon=-46.4731,
    course_deg=100.0,
    runway_threshold_lat=-23.4250,
    runway_threshold_lon=-46.4850,
)


class APMode(Enum):
    OFF = auto()
    HDG = auto()
    ALT = auto()
    VS = auto()
    LNAV = auto()
    VNAV = auto()
    APP = auto()


class Autopilot:
    # Gain constants
    _LOC_BANK_GAIN = 35.0     # degrees bank per unit of LOC deviation
    _LOC_TRACK_GAIN = 0.04    # integrator gain for localizer
    _GS_VS_GAIN = 1200.0      # fpm per unit of GS deviation
    _GS_CAPTURE_VS = -700.0   # fpm target once GS captured

    def __init__(self) -> None:
        self.lateral_mode = APMode.OFF
        self.vertical_mode = APMode.OFF
        self.target_heading = 0.0
        self.target_altitude = 0.0
        self.target_vs = 0.0
        self.target_course = 0.0
        self._heading_integrator = 0.0
        self._altitude_integrator = 0.0
        self._loc_integrator = 0.0
        self.ils: ILSLocalizer | None = SBGR_ILS_10R

    def engage(self, mode: APMode) -> None:
        if mode == APMode.OFF:
            self.lateral_mode = APMode.OFF
            self.vertical_mode = APMode.OFF
            self._loc_integrator = 0.0
        elif mode in {APMode.HDG, APMode.LNAV, APMode.APP}:
            self.lateral_mode = mode
            if mode == APMode.APP:
                self.vertical_mode = APMode.APP
                self._loc_integrator = 0.0
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
        from ..models.position import Position

        dt = max(dt, 1e-3)
        roll = float(state.get("roll_deg", 0.0))
        heading = float(state.get("heading_deg", 0.0))
        altitude = float(state.get("altitude_ft", 0.0))
        vertical_speed = float(state.get("vertical_speed_fpm", 0.0))

        # ── Lateral channel ───────────────────────────────────────────────────
        desired_heading = self.target_heading

        if self.lateral_mode == APMode.LNAV and gps is not None:
            desired_heading = gps.bearing_to_next_deg - gps.cross_track_error_nm * 8.0

        elif self.lateral_mode == APMode.APP and self.ils is not None:
            pos = state.get("position")
            if pos is not None:
                loc_dev = self.ils.get_localizer_deviation(pos)
                self._loc_integrator += loc_dev * dt
                desired_bank = max(-25.0, min(25.0,
                    -loc_dev * self._LOC_BANK_GAIN
                    - self._loc_integrator * self._LOC_TRACK_GAIN
                ))
                aileron = max(-1.0, min(1.0, (desired_bank - roll) / 20.0))
                # skip heading channel below; jump to vertical
                elevator = self._compute_vertical(
                    altitude, vertical_speed, flight_plan, state, dt
                )
                return {"elevator": elevator, "aileron": aileron, "rudder": max(-0.3, min(0.3, -roll / 45.0))}

        heading_error = ((desired_heading - heading + 540.0) % 360.0) - 180.0
        self._heading_integrator += heading_error * dt
        desired_bank = max(-25.0, min(25.0, 0.6 * heading_error + 0.02 * self._heading_integrator))
        aileron = 0.0 if self.lateral_mode == APMode.OFF else max(-1.0, min(1.0, (desired_bank - roll) / 20.0))

        elevator = self._compute_vertical(altitude, vertical_speed, flight_plan, state, dt)
        return {"elevator": elevator, "aileron": aileron, "rudder": max(-0.3, min(0.3, -roll / 45.0))}

    def _compute_vertical(
        self,
        altitude: float,
        vertical_speed: float,
        flight_plan: FlightPlan | None,
        state: dict,
        dt: float,
    ) -> float:
        if self.vertical_mode == APMode.ALT:
            alt_error = self.target_altitude - altitude
            self.target_vs = max(-700.0, min(700.0, alt_error * 0.5))
        elif self.vertical_mode == APMode.VNAV and flight_plan is not None and flight_plan.active_waypoint() is not None:
            target_altitude = flight_plan.active_waypoint().altitude_ft or self.target_altitude
            self.target_vs = max(-800.0, min(800.0, (target_altitude - altitude) * 0.4))
        elif self.vertical_mode == APMode.APP and self.ils is not None:
            pos = state.get("position")
            if pos is not None:
                gs_dev = self.ils.get_glideslope_deviation(pos, altitude)
                # Positive GS dev → above glidepath → increase descent rate
                self.target_vs = max(-1500.0, min(200.0,
                    self._GS_CAPTURE_VS - gs_dev * self._GS_VS_GAIN
                ))

        if self.vertical_mode == APMode.OFF:
            return 0.0
        vs_error = self.target_vs - vertical_speed
        self._altitude_integrator += vs_error * dt
        return max(-1.0, min(1.0, vs_error / 1200.0 + self._altitude_integrator / 8000.0))
