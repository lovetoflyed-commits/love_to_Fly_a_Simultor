from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(slots=True)
class Wind:
    speed_kts: float
    direction_deg: float
    gust_kts: float = 0.0


class Weather:
    def __init__(self, base_wind: Wind | None = None, visibility_sm: float = 10.0, ceiling_ft: int | None = None) -> None:
        self.base_wind = base_wind or Wind(12.0, 270.0, 5.0)
        self.visibility_sm = visibility_sm
        self.ceiling_ft = ceiling_ft

    def wind_at_altitude(self, altitude_ft: float) -> Wind:
        shear = min(20.0, altitude_ft / 1000.0 * 2.0)
        return Wind(self.base_wind.speed_kts + shear, (self.base_wind.direction_deg + altitude_ft / 5000.0 * 10.0) % 360.0, self.base_wind.gust_kts)

    def turbulence_intensity(self, altitude_ft: float) -> str:
        if altitude_ft < 2000:
            return "light"
        if altitude_ft < 12000:
            return "moderate"
        return "severe" if self.base_wind.gust_kts > 15 else "light"

    @staticmethod
    def get_turbulence_acceleration(intensity: str, dt: float) -> tuple[float, float, float]:
        scale = {"light": 0.3, "moderate": 0.8, "severe": 1.5}.get(intensity, 0.0)
        return tuple(random.uniform(-scale, scale) * dt for _ in range(3))

    def icing_severity(self, altitude_ft: float, oat_c: float) -> str:
        in_cloud = self.ceiling_ft is not None and altitude_ft <= self.ceiling_ft + 2000
        if not in_cloud or oat_c > 5 or oat_c < -20:
            return "none"
        if oat_c > 0:
            return "trace"
        if oat_c > -5:
            return "light"
        if oat_c > -10:
            return "moderate"
        return "severe"
