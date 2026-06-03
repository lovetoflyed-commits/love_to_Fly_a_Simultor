from __future__ import annotations

from dataclasses import dataclass
import math

from ..models.position import Position


@dataclass(slots=True)
class VOR:
    name: str
    lat: float
    lon: float
    frequency_mhz: float
    range_nm: float = 100.0

    def as_position(self) -> Position:
        return Position(self.lat, self.lon, 0.0)


class VORReceiver:
    def __init__(self) -> None:
        self.frequency_mhz: float | None = None

    def tune(self, frequency: float) -> None:
        self.frequency_mhz = frequency

    @staticmethod
    def get_radial(aircraft_position: Position, vor: VOR) -> float:
        return vor.as_position().bearing_to(aircraft_position)

    @staticmethod
    def get_distance_nm(aircraft_position: Position, vor: VOR) -> float:
        return aircraft_position.distance_nm(vor.as_position())

    def get_cdi(self, aircraft_position: Position, vor: VOR, selected_course: float) -> float:
        radial = self.get_radial(aircraft_position, vor)
        error = ((selected_course - radial + 540.0) % 360.0) - 180.0
        return max(-127.0, min(127.0, (error / 10.0) * 127.0))

    def is_in_range(self, aircraft_position: Position, vor: VOR) -> bool:
        return self.get_distance_nm(aircraft_position, vor) <= vor.range_nm and self.frequency_mhz == vor.frequency_mhz


@dataclass(slots=True)
class ILSLocalizer:
    vor_lat: float
    vor_lon: float
    course_deg: float
    runway_threshold_lat: float
    runway_threshold_lon: float

    def get_localizer_deviation(self, position: Position) -> float:
        threshold = Position(self.runway_threshold_lat, self.runway_threshold_lon, 0.0)
        bearing = position.bearing_to(threshold)
        error = ((self.course_deg - bearing + 540.0) % 360.0) - 180.0
        return max(-1.0, min(1.0, error / 2.5))

    def get_glideslope_deviation(self, position: Position, altitude_ft: float) -> float:
        threshold = Position(self.runway_threshold_lat, self.runway_threshold_lon, 0.0)
        distance_ft = max(100.0, position.distance_nm(threshold) * 6076.12)
        desired_alt_ft = math.tan(math.radians(3.0)) * distance_ft
        actual_angle = math.degrees(math.atan2(max(0.0, altitude_ft), distance_ft))
        error = actual_angle - 3.0
        if altitude_ft < 0:
            error = -3.0
        return max(-1.0, min(1.0, error / 0.7))
