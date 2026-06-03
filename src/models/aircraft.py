from __future__ import annotations

from dataclasses import dataclass


@dataclass()
class Aircraft:
    name: str
    max_thrust_N: float
    mass_kg: float
    wing_area_m2: float
    max_fuel_kg: float
    fuel_kg: float
    cl_max: float = 1.5
    cd_zero: float = 0.025
    aspect_ratio: float = 8.0
    oswald_efficiency: float = 0.8

    @classmethod
    def from_config(cls, data: dict) -> "Aircraft":
        payload = dict(data)
        payload.setdefault("fuel_kg", payload.get("max_fuel_kg", 0.0))
        return cls(**payload)
