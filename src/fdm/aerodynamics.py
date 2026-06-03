from __future__ import annotations

import math

from ..models.aircraft import Aircraft


class Aerodynamics:
    def __init__(self, aircraft: Aircraft) -> None:
        self.aircraft = aircraft

    def compute_cl(self, alpha_deg: float, flaps_deg: float = 0.0) -> float:
        flap_bonus = 0.01 * max(0.0, flaps_deg)
        if self.is_stalled(alpha_deg):
            excess = abs(alpha_deg) - 16.0
            cl = self.aircraft.cl_max * max(0.4, 1.0 - 0.08 * excess)
            return math.copysign(cl + flap_bonus, alpha_deg)
        cl = 0.1 * alpha_deg + flap_bonus
        return max(-self.aircraft.cl_max, min(self.aircraft.cl_max, cl))

    def compute_cd(self, cl: float) -> float:
        induced = (cl ** 2) / (math.pi * self.aircraft.aspect_ratio * self.aircraft.oswald_efficiency)
        return self.aircraft.cd_zero + induced

    @staticmethod
    def compute_lift(rho: float, v: float, cl: float, wing_area: float) -> float:
        return 0.5 * rho * v * v * cl * wing_area

    @staticmethod
    def compute_drag(rho: float, v: float, cd: float, wing_area: float) -> float:
        return 0.5 * rho * v * v * cd * wing_area

    @staticmethod
    def is_stalled(alpha_deg: float) -> bool:
        return abs(alpha_deg) > 16.0
