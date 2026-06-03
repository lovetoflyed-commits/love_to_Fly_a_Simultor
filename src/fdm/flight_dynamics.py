from __future__ import annotations

from dataclasses import dataclass, field
import math

from ..environment.weather import Weather
from ..models.attitude import Attitude
from ..models.position import Position
from .aerodynamics import Aerodynamics
from .atmosphere import ISAAtmosphere
from .engine import Engine
from ..models.aircraft import Aircraft

FT_TO_M = 0.3048
M_TO_FT = 1.0 / FT_TO_M
MPS_TO_KTS = 1.94384449
MPS_TO_FPM = 196.850394


@dataclass
class FlightDynamics:
    position: Position = field(default_factory=lambda: Position(-23.4356, -46.4731, 2459.0))
    attitude: Attitude = field(default_factory=Attitude)
    velocity_body_ms: list[float] = field(default_factory=lambda: [35.0, 0.0, 0.0])
    climb_rate_ms: float = 0.0
    airspeed_kts: float = 68.0
    vertical_speed_fpm: float = 0.0
    alpha_deg: float = 0.0
    g_load: float = 1.0

    def update(
        self,
        dt: float,
        controls: dict[str, float],
        aircraft: Aircraft,
        atmosphere: ISAAtmosphere,
        aerodynamics: Aerodynamics,
        engine: Engine,
        weather: Weather | None = None,
    ) -> dict[str, float]:
        dt = max(dt, 1e-3)
        engine.max_thrust_N = aircraft.max_thrust_N
        throttle = float(controls.get("throttle_pct", controls.get("throttle", 0.0)))
        elevator = float(controls.get("elevator_deflection", controls.get("elevator", 0.0)))
        aileron = float(controls.get("aileron_deflection", controls.get("aileron", 0.0)))
        rudder = float(controls.get("rudder_deflection", controls.get("rudder", 0.0)))

        conditions = atmosphere.get_conditions(self.position.altitude_ft)
        rho = conditions["density_kg_m3"]
        tas = max(1.0, math.sqrt(sum(component * component for component in self.velocity_body_ms)))
        flight_path_deg = math.degrees(math.atan2(self.climb_rate_ms, max(1.0, self.velocity_body_ms[0])))
        self.alpha_deg = max(-20.0, min(20.0, self.attitude.pitch_deg - flight_path_deg + elevator * 8.0))

        cl = aerodynamics.compute_cl(self.alpha_deg)
        cd = aerodynamics.compute_cd(cl)
        lift = aerodynamics.compute_lift(rho, tas, cl, aircraft.wing_area_m2)
        drag = aerodynamics.compute_drag(rho, tas, cd, aircraft.wing_area_m2)
        thrust = engine.compute_thrust(throttle, self.position.altitude_ft, atmosphere)
        weight = aircraft.mass_kg * 9.80665
        bank_rad = math.radians(self.attitude.roll_deg)
        gamma = math.radians(flight_path_deg)

        longitudinal_accel = (thrust - drag - weight * math.sin(gamma)) / aircraft.mass_kg
        vertical_accel = ((lift * math.cos(bank_rad)) - weight * math.cos(gamma)) / aircraft.mass_kg

        if weather is not None:
            wind = weather.wind_at_altitude(self.position.altitude_ft)
            intensity = weather.turbulence_intensity(self.position.altitude_ft)
            turb_ax, _, turb_az = weather.get_turbulence_acceleration(intensity, dt)
            longitudinal_accel += turb_ax
            vertical_accel += turb_az
        else:
            wind = None

        self.velocity_body_ms[0] = max(12.0, self.velocity_body_ms[0] + longitudinal_accel * dt)
        self.velocity_body_ms[1] += rudder * 0.5 * dt
        self.climb_rate_ms += vertical_accel * dt
        self.climb_rate_ms *= 0.995

        pitch_rate = elevator * 18.0 - self.attitude.pitch_deg * 0.25
        roll_rate = aileron * 45.0 - self.attitude.roll_deg * 0.65
        coordinated_turn_rate = math.degrees(9.80665 * math.tan(bank_rad) / max(20.0, self.velocity_body_ms[0]))
        yaw_rate = rudder * 8.0 + coordinated_turn_rate

        self.attitude.pitch_deg = max(-20.0, min(25.0, self.attitude.pitch_deg + pitch_rate * dt))
        self.attitude.roll_deg = max(-60.0, min(60.0, self.attitude.roll_deg + roll_rate * dt))
        self.attitude.yaw_deg = (self.attitude.yaw_deg + yaw_rate * dt) % 360.0

        altitude_change_ft = self.climb_rate_ms * dt * M_TO_FT
        self.position.altitude_ft = max(0.0, self.position.altitude_ft + altitude_change_ft)

        heading_rad = math.radians(self.attitude.yaw_deg)
        north_ms = math.cos(heading_rad) * self.velocity_body_ms[0]
        east_ms = math.sin(heading_rad) * self.velocity_body_ms[0]
        if wind is not None:
            wind_dir_rad = math.radians(wind.direction_deg)
            east_ms += -math.sin(wind_dir_rad) * (wind.speed_kts / MPS_TO_KTS)
            north_ms += -math.cos(wind_dir_rad) * (wind.speed_kts / MPS_TO_KTS)

        lat_scale = 111_320.0
        lon_scale = max(1.0, 111_320.0 * math.cos(math.radians(self.position.latitude_deg)))
        self.position.latitude_deg += (north_ms * dt) / lat_scale
        self.position.longitude_deg += (east_ms * dt) / lon_scale

        self.airspeed_kts = max(0.0, self.velocity_body_ms[0] * MPS_TO_KTS)
        self.vertical_speed_fpm = self.climb_rate_ms * MPS_TO_FPM
        self.g_load = (lift / max(weight, 1.0)) if weight else 1.0

        fuel_burn = engine.compute_fuel_burn_kgs(thrust, dt)
        aircraft.fuel_kg = max(0.0, aircraft.fuel_kg - fuel_burn)

        return {
            "thrust_N": thrust,
            "lift_N": lift,
            "drag_N": drag,
            "alpha_deg": self.alpha_deg,
            "airspeed_kts": self.airspeed_kts,
            "vertical_speed_fpm": self.vertical_speed_fpm,
            "pitch_deg": self.attitude.pitch_deg,
            "roll_deg": self.attitude.roll_deg,
            "heading_deg": self.attitude.yaw_deg,
            "altitude_ft": self.position.altitude_ft,
            "fuel_kg": aircraft.fuel_kg,
            "g_load": self.g_load,
        }
