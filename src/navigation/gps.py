from __future__ import annotations

import math

from ..models.flight_plan import FlightPlan
from ..models.position import Position


class GPS:
    def __init__(self) -> None:
        self.distance_to_next_nm = 0.0
        self.bearing_to_next_deg = 0.0
        self.cross_track_error_nm = 0.0
        self.ete_min = 0.0
        self._last_position: Position | None = None
        self._groundspeed_kts = 0.0

    def update(self, position: Position, flight_plan: FlightPlan, dt: float) -> None:
        active = flight_plan.active_waypoint()
        if active is None:
            self.distance_to_next_nm = 0.0
            self.bearing_to_next_deg = 0.0
            self.cross_track_error_nm = 0.0
            self.ete_min = 0.0
            return
        target = active.as_position()
        self.distance_to_next_nm = position.distance_nm(target)
        self.bearing_to_next_deg = position.bearing_to(target)
        if self._last_position is not None and dt > 0:
            moved_nm = self._last_position.distance_nm(position)
            self._groundspeed_kts = moved_nm / dt * 3600.0
        self._last_position = Position(position.latitude_deg, position.longitude_deg, position.altitude_ft)
        self.ete_min = (self.distance_to_next_nm / max(1.0, self._groundspeed_kts)) * 60.0 if self.distance_to_next_nm else 0.0
        if flight_plan.active_leg > 0:
            start = flight_plan.waypoints[flight_plan.active_leg - 1].as_position()
            end = target
            self.cross_track_error_nm = self._cross_track_nm(start, end, position)
        else:
            self.cross_track_error_nm = 0.0
        if self.distance_to_next_nm < 1.0:
            self.sequence_waypoint(flight_plan)

    def sequence_waypoint(self, flight_plan: FlightPlan) -> None:
        flight_plan.next_waypoint()

    @staticmethod
    def _cross_track_nm(start: Position, end: Position, current: Position) -> float:
        lat0 = math.radians((start.latitude_deg + end.latitude_deg + current.latitude_deg) / 3.0)
        sx = start.longitude_deg * 60.0 * math.cos(lat0)
        sy = start.latitude_deg * 60.0
        ex = end.longitude_deg * 60.0 * math.cos(lat0)
        ey = end.latitude_deg * 60.0
        cx = current.longitude_deg * 60.0 * math.cos(lat0)
        cy = current.latitude_deg * 60.0
        dx = ex - sx
        dy = ey - sy
        mag = math.hypot(dx, dy)
        if mag < 1e-6:
            return 0.0
        return ((cx - sx) * dy - (cy - sy) * dx) / mag
