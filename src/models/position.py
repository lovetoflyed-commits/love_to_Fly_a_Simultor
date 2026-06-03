from __future__ import annotations

from dataclasses import dataclass
import math

FT_TO_M = 0.3048
EARTH_RADIUS_M = 6_371_000.0
M_PER_NM = 1852.0


@dataclass()
class Position:
    latitude_deg: float
    longitude_deg: float
    altitude_ft: float

    def to_xyz(self) -> tuple[float, float, float]:
        lat_rad = math.radians(self.latitude_deg)
        x = self.longitude_deg * 111_320.0 * math.cos(lat_rad)
        y = self.latitude_deg * 111_320.0
        z = self.altitude_ft * FT_TO_M
        return x, y, z

    def distance_nm(self, other: "Position") -> float:
        lat1 = math.radians(self.latitude_deg)
        lon1 = math.radians(self.longitude_deg)
        lat2 = math.radians(other.latitude_deg)
        lon2 = math.radians(other.longitude_deg)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(1e-12, 1.0 - a)))
        return (EARTH_RADIUS_M * c) / M_PER_NM

    def bearing_to(self, other: "Position") -> float:
        lat1 = math.radians(self.latitude_deg)
        lat2 = math.radians(other.latitude_deg)
        dlon = math.radians(other.longitude_deg - self.longitude_deg)
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0
