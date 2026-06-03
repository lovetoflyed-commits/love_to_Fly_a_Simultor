from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(slots=True)
class Attitude:
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    yaw_deg: float = 0.0

    @property
    def pitch_rad(self) -> float:
        return math.radians(self.pitch_deg)

    @property
    def roll_rad(self) -> float:
        return math.radians(self.roll_deg)

    @property
    def yaw_rad(self) -> float:
        return math.radians(self.yaw_deg)
