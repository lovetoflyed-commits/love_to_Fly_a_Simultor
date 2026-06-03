import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.instruments.airspeed_indicator import AirspeedIndicator
from src.instruments.altimeter import Altimeter
from src.instruments.attitude_indicator import AttitudeIndicator
from src.instruments.engine_instruments import EngineInstruments
from src.instruments.heading_indicator import HeadingIndicator
from src.instruments.nav_display import NavDisplay
from src.instruments.tachometer import Tachometer
from src.instruments.turn_coordinator import TurnCoordinator
from src.instruments.vsi import VSI
from src.models.flight_plan import Waypoint
from src.models.position import Position


pygame.init()


def test_instruments_update_and_draw() -> None:
    instruments = [
        AttitudeIndicator(),
        AirspeedIndicator(),
        Altimeter(),
        VSI(),
        HeadingIndicator(),
        NavDisplay(),
        EngineInstruments(),
        Tachometer(),
        TurnCoordinator(),
    ]
    state = {
        "pitch_deg": 5,
        "roll_deg": 10,
        "airspeed_kts": 110,
        "altitude_ft": 2450,
        "baro_inhg": 29.92,
        "vertical_speed_fpm": 500,
        "heading_deg": 180,
        "position": Position(37.6, -122.3, 2450),
        "waypoints": [Waypoint("A", 37.61, -122.25)],
        "active_leg": 0,
        "bearing_to_next_deg": 90,
        "distance_to_next_nm": 4.2,
        "n1_pct": 75,
        "fuel_kg": 100,
        "max_fuel_kg": 83,
        "rpm": 2100,
        "oil_temp_c": 85,
        "oil_pressure_psi": 65,
    }
    for instrument in instruments:
        instrument.update(state)
        surface = instrument.draw()
        assert isinstance(surface, pygame.Surface)

