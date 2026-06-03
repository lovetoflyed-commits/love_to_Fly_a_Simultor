from src.environment.weather import Weather
from src.fdm.aerodynamics import Aerodynamics
from src.fdm.atmosphere import ISAAtmosphere
from src.fdm.engine import Engine
from src.fdm.flight_dynamics import FlightDynamics
from src.models.aircraft import Aircraft


def test_flight_dynamics_thrust_increases_speed() -> None:
    aircraft = Aircraft("Test", 12000, 1100, 16.2, 180, 180)
    fdm = FlightDynamics()
    atmosphere = ISAAtmosphere()
    aero = Aerodynamics(aircraft)
    engine = Engine(aircraft.max_thrust_N)
    initial_speed = fdm.airspeed_kts
    for _ in range(120):
        fdm.update(0.05, {"throttle_pct": 80, "elevator": 0.0, "aileron": 0.0, "rudder": 0.0}, aircraft, atmosphere, aero, engine, Weather())
    assert fdm.airspeed_kts > initial_speed
