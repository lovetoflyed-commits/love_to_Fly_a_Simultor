from src.environment.airport import AirportDatabase
from src.fdm.flight_dynamics import FlightDynamics
from src.models.flight_plan import FlightPlan, Waypoint
from src.models.position import Position
from src.navigation.procedures import ProcedureDatabase
from src.navigation.autopilot import APMode, Autopilot
from src.navigation.gps import GPS
from src.navigation.vor import VOR, VORReceiver
from src.main import _build_default_flight_plan


def test_vor_radial_east_of_station() -> None:
    vor = VOR("TEST", 37.0, -122.0, 113.0)
    aircraft_position = Position(37.0, -121.8, 3000)
    radial = VORReceiver.get_radial(aircraft_position, vor)
    assert 85 <= radial <= 95


def test_gps_cross_track_error_nonzero_off_course() -> None:
    flight_plan = FlightPlan([Waypoint("A", 37.0, -122.0), Waypoint("B", 37.0, -121.0)])
    flight_plan.active_leg = 1
    gps = GPS()
    gps.update(Position(36.9, -121.5, 3000), flight_plan, 1.0)
    assert abs(gps.cross_track_error_nm) > 0.1


def test_autopilot_heading_mode_commands_bank() -> None:
    autopilot = Autopilot()
    autopilot.engage(APMode.HDG)
    autopilot.set_target(heading=90)
    controls = autopilot.compute_controls({"heading_deg": 0, "roll_deg": 0, "altitude_ft": 1000, "vertical_speed_fpm": 0}, None, None, None, 0.1)
    assert controls["aileron"] > 0


def test_default_start_position_is_in_brazil() -> None:
    fdm = FlightDynamics()
    assert -34.0 <= fdm.position.latitude_deg <= 6.0
    assert -74.0 <= fdm.position.longitude_deg <= -34.0


def test_default_start_nearest_airport_is_sbgr() -> None:
    fdm = FlightDynamics()
    nearest = AirportDatabase().nearest_airport(fdm.position, 30.0)
    assert nearest is not None
    assert nearest.icao == "SBGR"


def test_default_flight_plan_targets_sbgr_runway_10r() -> None:
    plan = _build_default_flight_plan()
    assert plan.waypoints[-1].name == "RW10R"
    assert plan.waypoints[-1].altitude_ft == 2459


def test_default_approach_procedure_is_sbgr_ils_10r() -> None:
    approaches = ProcedureDatabase().get_approaches("SBGR")
    assert approaches
    procedure = next((item for item in approaches if item.name == "ILS RWY 10R"), None)
    assert procedure is not None
    assert procedure.name == "ILS RWY 10R"
    assert procedure.waypoints[-1].name == "RW10R"
