import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.instruments.airspeed_indicator import AirspeedIndicator
from src.instruments.altimeter import Altimeter
from src.instruments.attitude_indicator import AttitudeIndicator
from src.instruments.base_instrument import Instrument
from src.instruments.engine_instruments import EngineInstruments
from src.instruments.heading_indicator import HeadingIndicator
from src.instruments.nav_display import NavDisplay
from src.instruments.tachometer import Tachometer
from src.instruments.turn_coordinator import TurnCoordinator
from src.instruments.vsi import VSI
from src.models.flight_plan import Waypoint
from src.models.position import Position
from src.ui.cockpit_view import CockpitView


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


def test_turn_coordinator_uses_right_turn_sign_convention() -> None:
    turn_coordinator = TurnCoordinator()
    captured: dict[str, float] = {}

    def capture_rotation(surf: pygame.Surface, angle: float) -> pygame.Surface:
        captured["angle"] = angle
        return surf

    turn_coordinator._rotate_surface = capture_rotation  # type: ignore[method-assign]
    turn_coordinator.update({"roll_deg": 10.0})
    turn_coordinator.draw()

    assert captured["angle"] < 0.0


def test_cockpit_horizon_roll_sign_matches_right_bank() -> None:
    cockpit = CockpitView(1280, 720)
    left, right = cockpit._horizon_line_endpoints(1280, 130.0, 10.0)
    assert right[1] < left[1]


def test_cockpit_blanks_nav_display_when_avionics_unpowered() -> None:
    cockpit = CockpitView(1280, 720)
    cockpit.update(
        {
            "position": Position(37.6, -122.3, 2450),
            "waypoints": [Waypoint("A", 37.61, -122.25)],
            "active_leg": 0,
            "bearing_to_next_deg": 90,
            "distance_to_next_nm": 4.2,
            "avionics_powered": False,
        }
    )
    assert cockpit.nav_display.waypoints == []


# ── New tests for improved rendering helpers ──────────────────────────────────

def test_altimeter_three_needles_at_zero() -> None:
    """At 0 ft all three needle angles should be the same (pointing to 12-o'clock)."""
    alt = Altimeter(150, 150)
    alt.update({"altitude_ft": 0.0, "baro_inhg": 29.92})
    # 0 ft → angle = radians(90°) for all three pointers
    expected = math.radians(90.0)
    assert abs(alt._alt_to_angle(0.0, 1_000.0) - expected) < 1e-9
    assert abs(alt._alt_to_angle(0.0, 10_000.0) - expected) < 1e-9
    assert abs(alt._alt_to_angle(0.0, 100_000.0) - expected) < 1e-9


def test_altimeter_hundreds_needle_full_revolution_at_1000ft() -> None:
    """The hundreds needle should complete one full revolution every 1 000 ft."""
    alt = Altimeter(150, 150)
    angle_0 = alt._alt_to_angle(0.0, 1_000.0)
    angle_1000 = alt._alt_to_angle(1_000.0, 1_000.0)
    # Both map to the same angle since 1000 mod 1000 == 0
    assert abs(angle_0 - angle_1000) < 1e-9


def test_altimeter_hundreds_needle_at_500ft() -> None:
    """At 500 ft the hundreds needle should be at 180° from the 0-ft position."""
    alt = Altimeter(150, 150)
    angle_0 = alt._alt_to_angle(0.0, 1_000.0)
    angle_500 = alt._alt_to_angle(500.0, 1_000.0)
    diff = abs(angle_0 - angle_500) % (2 * math.pi)
    assert abs(diff - math.pi) < 1e-9


def test_altimeter_draws_surface() -> None:
    alt = Altimeter(150, 150)
    alt.update({"altitude_ft": 3500.0, "baro_inhg": 29.82})
    surf = alt.draw()
    assert isinstance(surf, pygame.Surface)
    assert surf.get_size() == (150, 150)


def test_vsi_angle_zero_at_zero_fpm() -> None:
    """0 fpm should map to 0 radians (9-o'clock / horizontal-right)."""
    vsi = VSI(150, 150)
    assert vsi._fpm_to_angle(0.0) == 0.0


def test_vsi_angle_positive_for_climb() -> None:
    """Positive fpm should give a positive angle (needle points upward)."""
    vsi = VSI(150, 150)
    assert vsi._fpm_to_angle(500.0) > 0.0


def test_vsi_angle_negative_for_descent() -> None:
    """Negative fpm should give a negative angle (needle points downward)."""
    vsi = VSI(150, 150)
    assert vsi._fpm_to_angle(-500.0) < 0.0


def test_vsi_clamps_at_max_fpm() -> None:
    """Angles beyond ±2000 fpm should be clamped to ±π/2."""
    vsi = VSI(150, 150)
    assert abs(vsi._fpm_to_angle(9999.0) - math.radians(90.0)) < 1e-9
    assert abs(vsi._fpm_to_angle(-9999.0) - math.radians(-90.0)) < 1e-9


def test_airspeed_angle_increases_with_speed() -> None:
    """Higher speeds should produce lower angle values (CW sweep)."""
    asi = AirspeedIndicator(150, 150)
    assert asi._value_to_angle(80.0) < asi._value_to_angle(0.0)


def test_airspeed_angle_clamped() -> None:
    """Angles outside [0, MAX_SPEED] should be clamped to the end-stops."""
    asi = AirspeedIndicator(150, 150)
    assert asi._value_to_angle(-10.0) == asi._value_to_angle(0.0)
    assert asi._value_to_angle(999.0) == asi._value_to_angle(asi.MAX_SPEED)


def test_engine_instruments_oil_temp_color_ranges() -> None:
    eng = EngineInstruments()
    assert eng._oil_temp_color(20.0) == (80, 160, 230)    # cold
    assert eng._oil_temp_color(80.0) == (0, 185, 75)      # normal
    assert eng._oil_temp_color(110.0) == (215, 175, 30)   # warm
    assert eng._oil_temp_color(130.0) == (215, 40, 40)    # hot


def test_engine_instruments_oil_pressure_color_ranges() -> None:
    eng = EngineInstruments()
    assert eng._oil_pressure_color(10.0) == (215, 40, 40)   # low
    assert eng._oil_pressure_color(65.0) == (0, 185, 75)    # normal
    assert eng._oil_pressure_color(95.0) == (215, 175, 30)  # high


def test_engine_instruments_fuel_color_ranges() -> None:
    eng = EngineInstruments()
    assert eng._fuel_color(0.10) == (215, 40, 40)    # low
    assert eng._fuel_color(0.20) == (215, 175, 30)   # caution
    assert eng._fuel_color(0.80) == (0, 185, 75)     # normal


def test_engine_instruments_draws_surface() -> None:
    eng = EngineInstruments(185, 162)
    eng.update({
        "oil_temp_c": 90.0,
        "oil_pressure_psi": 70.0,
        "fuel_kg": 60.0,
        "max_fuel_kg": 83.0,
        "suction_inhg": 4.8,
        "bus_voltage_v": 13.8,
        "master_on": True,
        "avionics_on": True,
        "engine_running": True,
        "magneto_position": "BOTH",
    })
    surf = eng.draw()
    assert isinstance(surf, pygame.Surface)
    assert surf.get_size() == (185, 162)


def test_tachometer_rpm_to_angle_endpoints() -> None:
    tach = Tachometer(150, 150)
    # 0 RPM → 225°, 3000 RPM → -45° (== 315°)
    assert abs(tach._rpm_to_angle_deg(0.0) - 225.0) < 1e-9
    assert abs(tach._rpm_to_angle_deg(3000.0) - (225.0 - 270.0)) < 1e-9


def test_tachometer_redline_is_within_scale() -> None:
    tach = Tachometer(150, 150)
    angle = tach._rpm_to_angle_deg(tach.REDLINE_RPM)
    # Redline (2750 RPM) should produce an angle between the two end-stops
    assert 225.0 - 270.0 < angle < 225.0

