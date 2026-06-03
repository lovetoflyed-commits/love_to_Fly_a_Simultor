from __future__ import annotations

from .atmosphere import ISAAtmosphere


class Engine:
    def __init__(self, max_thrust_N: float = 10_000.0) -> None:
        self.max_thrust_N = max_thrust_N
        self._last_throttle_pct = 0.0

    def compute_thrust(self, throttle_pct: float, altitude_ft: float, atmosphere: ISAAtmosphere) -> float:
        self._last_throttle_pct = max(0.0, min(100.0, throttle_pct))
        conditions = atmosphere.get_conditions(altitude_ft)
        density_ratio = conditions["density_kg_m3"] / 1.225
        available = self.max_thrust_N * max(0.2, density_ratio ** 0.7)
        return available * (self._last_throttle_pct / 100.0)

    def compute_fuel_burn_kgs(self, thrust_N: float, dt: float) -> float:
        return max(0.0, thrust_N) * 0.00008 * max(dt, 0.0)

    @property
    def n1_pct(self) -> float:
        return self._last_throttle_pct * 0.98
