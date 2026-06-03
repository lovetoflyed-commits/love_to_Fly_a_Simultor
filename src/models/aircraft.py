from __future__ import annotations

from dataclasses import dataclass


# Valid flap positions in degrees for a typical trainer
FLAP_POSITIONS = [0, 10, 20, 30]


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
    # Flap-induced CD penalty per degree of flap extension
    flap_cd_per_deg: float = 0.0010

    @classmethod
    def from_config(cls, data: dict) -> "Aircraft":
        payload = dict(data)
        payload.setdefault("fuel_kg", payload.get("max_fuel_kg", 0.0))
        # Ignore unknown keys for forward-compat
        valid = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        payload = {k: v for k, v in payload.items() if k in valid}
        return cls(**payload)
