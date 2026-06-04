from src.environment.airport import AirportDatabase
from src.fdm.flight_dynamics import FlightDynamics
from src.models.flight_plan import FlightPlan, Waypoint
from src.models.position import Position
from src.navigation.procedures import ProcedureDatabase
from src.navigation.autopilot import APMode, Autopilot
from src.navigation.gps import GPS
from src.navigation.vor import VOR, VORReceiver
from src.main import _build_default_flight_plan, _spawn_lined_up_on_runway, _step_heading_bug


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


def test_runway_spawn_lines_up_with_sbgr_10r() -> None:
    from src.main import _offset_position, RUNWAY_SPAWN_OFFSET_FT

    fdm = FlightDynamics()
    airport_db = AirportDatabase()
    runway = next(rwy for rwy in airport_db.get_airport("SBGR").runways if rwy.name == "10R")  # type: ignore[union-attr]

    _spawn_lined_up_on_runway(fdm, airport_db, "SBGR", "10R")

    # Aircraft must be ON the runway surface (positive offset from threshold)
    exp_lat, exp_lon = _offset_position(
        runway.threshold_lat, runway.threshold_lon,
        RUNWAY_SPAWN_OFFSET_FT, runway.heading_deg,
    )
    assert RUNWAY_SPAWN_OFFSET_FT > 0, "spawn offset must be positive to place aircraft on the runway"
    expected_pos = Position(exp_lat, exp_lon, runway.elevation_ft)
    assert fdm.position.distance_nm(expected_pos) < 0.01  # within ~60 ft of expected spawn
    assert abs(fdm.attitude.yaw_deg - runway.heading_deg) < 1e-6
    assert fdm.position.altitude_ft == runway.elevation_ft
    assert fdm.airspeed_kts == 0.0
    assert fdm.velocity_body_ms == [0.0, 0.0, 0.0]


def test_step_heading_bug_wraps() -> None:
    assert _step_heading_bug(359.0, 2.0) == 1.0
    assert _step_heading_bug(1.0, -3.0) == 358.0
