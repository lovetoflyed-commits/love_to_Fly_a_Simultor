from __future__ import annotations

import math

FT_TO_M = 0.3048
G0 = 9.80665
R = 287.05287
GAMMA = 1.4


class ISAAtmosphere:
    def get_conditions(self, altitude_ft: float) -> dict[str, float]:
        altitude_m = max(0.0, altitude_ft * FT_TO_M)
        t0 = 288.15
        p0 = 101325.0
        lapse = -0.0065
        tropopause_m = 11_000.0

        if altitude_m <= tropopause_m:
            temperature = t0 + lapse * altitude_m
            pressure = p0 * (temperature / t0) ** (-G0 / (lapse * R))
        else:
            temperature = 216.65
            p11 = p0 * (temperature / t0) ** (-G0 / (lapse * R))
            pressure = p11 * math.exp(-G0 * (altitude_m - tropopause_m) / (R * temperature))

        density = pressure / (R * temperature)
        speed_of_sound = math.sqrt(GAMMA * R * temperature)
        return {
            "temperature_K": temperature,
            "pressure_Pa": pressure,
            "density_kg_m3": density,
            "speed_of_sound_ms": speed_of_sound,
        }
