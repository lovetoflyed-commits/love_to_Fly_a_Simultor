from __future__ import annotations

from .atmosphere import ISAAtmosphere


class Engine:
    def __init__(self, max_thrust_N: float = 10_000.0) -> None:
        self.max_thrust_N = max_thrust_N
        self._last_throttle_pct = 0.0
        self.master_on = True
        self.avionics_on = True
        self.magneto_position = "BOTH"
        self.mixture_pct = 100.0
        self.carb_heat_on = False
        self.starter_engaged = False
        self.engine_running = True

    def set_controls(
        self,
        *,
        master_on: bool,
        avionics_on: bool,
        magneto_position: str,
        mixture_pct: float,
        carb_heat_on: bool,
        starter_engaged: bool,
    ) -> None:
        self.master_on = bool(master_on)
        self.avionics_on = bool(avionics_on)
        self.magneto_position = str(magneto_position).upper()
        self.mixture_pct = max(0.0, min(100.0, float(mixture_pct)))
        self.carb_heat_on = bool(carb_heat_on)
        self.starter_engaged = bool(starter_engaged)

    def update_system_state(self, fuel_kg: float) -> None:
        fuel_available = fuel_kg > 0.0
        ignition_available = self.magneto_position in {"L", "R", "BOTH"}
        can_run = self.master_on and fuel_available and ignition_available and self.mixture_pct > 5.0
        if self.starter_engaged and can_run and self.mixture_pct >= 20.0:
            self.engine_running = True
        if not can_run:
            self.engine_running = False

    def _mixture_power_factor(self) -> float:
        if self.mixture_pct <= 5.0:
            return 0.0
        if self.mixture_pct < 35.0:
            return 0.45 + (self.mixture_pct - 5.0) / 30.0 * 0.45
        if self.mixture_pct <= 85.0:
            return 0.9 + (self.mixture_pct - 35.0) / 50.0 * 0.1
        if self.mixture_pct <= 100.0:
            return 1.0 - (self.mixture_pct - 85.0) / 15.0 * 0.04
        return 0.96

    def _magneto_power_factor(self) -> float:
        if self.magneto_position in {"L", "R"}:
            return 0.93
        if self.magneto_position == "BOTH":
            return 1.0
        return 0.0

    def compute_thrust(self, throttle_pct: float, altitude_ft: float, atmosphere: ISAAtmosphere) -> float:
        self._last_throttle_pct = max(0.0, min(100.0, throttle_pct))
        if not self.engine_running:
            return 0.0
        conditions = atmosphere.get_conditions(altitude_ft)
        density_ratio = conditions["density_kg_m3"] / 1.225
        available = self.max_thrust_N * max(0.2, density_ratio ** 0.7)
        carb_heat_factor = 0.9 if self.carb_heat_on else 1.0
        power_factor = (
            (self._last_throttle_pct / 100.0)
            * self._mixture_power_factor()
            * self._magneto_power_factor()
            * carb_heat_factor
        )
        return available * max(0.0, min(1.0, power_factor))

    def compute_fuel_burn_kgs(self, thrust_N: float, dt: float) -> float:
        if not self.engine_running:
            return 0.0
        richness = 0.7 + (self.mixture_pct / 100.0) * 0.4
        return max(0.0, thrust_N) * 0.00008 * richness * max(dt, 0.0)

    @property
    def n1_pct(self) -> float:
        if not self.engine_running:
            return 0.0
        return (self.rpm / 2750.0) * 100.0

    @property
    def rpm(self) -> float:
        """Piston engine RPM (Lycoming O-235: idle ~800, full power 2750)."""
        if not self.engine_running:
            if self.starter_engaged and self.master_on and self.magneto_position in {"L", "R", "BOTH"}:
                return 220.0
            return 0.0
        idle = 700.0
        max_power = 2750.0
        return idle + (self._last_throttle_pct / 100.0) * (max_power - idle) * self._mixture_power_factor() * self._magneto_power_factor() * (0.9 if self.carb_heat_on else 1.0)

    @property
    def suction_inhg(self) -> float:
        if not self.engine_running:
            return 0.0
        return min(6.0, max(2.0, 2.0 + (self.rpm - 700.0) / 2050.0 * 3.6))

    @property
    def bus_voltage_v(self) -> float:
        if not self.master_on:
            return 0.0
        if self.engine_running and self.rpm >= 1000.0:
            return 13.8
        return 12.3

    @property
    def avionics_powered(self) -> bool:
        return self.master_on and self.avionics_on and self.bus_voltage_v >= 10.5
