from __future__ import annotations

from dataclasses import dataclass, field

from .position import Position


@dataclass(slots=True)
class Waypoint:
    name: str
    lat: float
    lon: float
    altitude_ft: float | None = None

    def as_position(self) -> Position:
        return Position(self.lat, self.lon, self.altitude_ft or 0.0)


@dataclass(slots=True)
class FlightPlan:
    waypoints: list[Waypoint] = field(default_factory=list)
    active_leg: int = 0

    def add_waypoint(self, waypoint: Waypoint) -> None:
        self.waypoints.append(waypoint)

    def next_waypoint(self) -> Waypoint | None:
        if self.active_leg + 1 < len(self.waypoints):
            self.active_leg += 1
            return self.waypoints[self.active_leg]
        return None

    def active_waypoint(self) -> Waypoint | None:
        if 0 <= self.active_leg < len(self.waypoints):
            return self.waypoints[self.active_leg]
        return None

    def distance_to_next(self, position: Position) -> float:
        waypoint = self.active_waypoint()
        if waypoint is None:
            return 0.0
        return position.distance_nm(waypoint.as_position())
