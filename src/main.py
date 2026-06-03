from __future__ import annotations

import json
from math import radians, sin, cos, atan2, sqrt as _haversine_sqrt
from pathlib import Path
import sys

import pygame

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from src.chairflight.checklist import ENGINE_START_RUNUP, Checklist
    from src.chairflight.logbook import Logbook, LogEntry
    from src.chairflight.procedure_viewer import ProcedureViewer
    from src.environment.airport import AirportDatabase
    from src.environment.terrain import Terrain
    from src.environment.weather import Weather
    from src.fdm.aerodynamics import Aerodynamics
    from src.fdm.atmosphere import ISAAtmosphere
    from src.fdm.engine import Engine
    from src.fdm.flight_dynamics import FlightDynamics
    from src.models.aircraft import Aircraft, FLAP_POSITIONS
    from src.models.flight_plan import FlightPlan, Waypoint
    from src.navigation.autopilot import APMode, Autopilot, SBGR_ILS_10R
    from src.navigation.gps import GPS
    from src.navigation.procedures import ProcedureDatabase
    from src.navigation.vor import VOR, VORReceiver
    from src.scenarios.atc import ATCController
    from src.scenarios.failures import FailureManager
    from src.scenarios.scenario_engine import ScenarioEngine
    from src.scenarios.training_scenarios import (
        ILS_APPROACH, ENGINE_FAILURE_SCENARIO, HOLDING_PATTERN,
        PARTIAL_PANEL, MISSED_APPROACH, DIVERSION,
    )
    from src.ui.cockpit_view import CockpitView
    from src.ui.hud import HUD
    from src.ui.main_menu import MainMenu
    from src.ui.settings import Settings
else:
    from .chairflight.checklist import ENGINE_START_RUNUP, Checklist
    from .chairflight.logbook import Logbook, LogEntry
    from .chairflight.procedure_viewer import ProcedureViewer
    from .environment.airport import AirportDatabase
    from .environment.terrain import Terrain
    from .environment.weather import Weather
    from .fdm.aerodynamics import Aerodynamics
    from .fdm.atmosphere import ISAAtmosphere
    from .fdm.engine import Engine
    from .fdm.flight_dynamics import FlightDynamics
    from .models.aircraft import Aircraft, FLAP_POSITIONS
    from .models.flight_plan import FlightPlan, Waypoint
    from .navigation.autopilot import APMode, Autopilot, SBGR_ILS_10R
    from .navigation.gps import GPS
    from .navigation.procedures import ProcedureDatabase
    from .navigation.vor import VOR, VORReceiver
    from .scenarios.atc import ATCController
    from .scenarios.failures import FailureManager
    from .scenarios.scenario_engine import ScenarioEngine
    from .scenarios.training_scenarios import (
        ILS_APPROACH, ENGINE_FAILURE_SCENARIO, HOLDING_PATTERN,
        PARTIAL_PANEL, MISSED_APPROACH, DIVERSION,
    )
    from .ui.cockpit_view import CockpitView
    from .ui.hud import HUD
    from .ui.main_menu import MainMenu
    from .ui.settings import Settings

DG_FOLLOW_GAIN = 0.7
DG_DRIFT_DEG_PER_SEC = 0.03
HEADING_WRAP_OFFSET_DEG = 540.0
DG_MINIMUM_SUCTION_INHG = 3.5
FULL_CIRCLE_DEG = 360.0
HALF_CIRCLE_DEG = 180.0

_SCENARIO_MAP = {
    "ILS_APPROACH": ILS_APPROACH,
    "ENGINE_FAILURE_SCENARIO": ENGINE_FAILURE_SCENARIO,
    "HOLDING_PATTERN": HOLDING_PATTERN,
    "PARTIAL_PANEL": PARTIAL_PANEL,
    "MISSED_APPROACH": MISSED_APPROACH,
    "DIVERSION": DIVERSION,
}

# Radio tuning step sizes
_COM_STEP = 0.025
_NAV_STEP = 0.05
_COM_MIN, _COM_MAX = 118.000, 136.975
_NAV_MIN, _NAV_MAX = 108.000, 117.950
_SQUAWK_CODES = [1200, 2000, 7700, 7600, 7500]


def _load_aircraft(config_name: str) -> Aircraft:
    assets = Path(__file__).resolve().parent.parent / "assets" / "data" / "aircraft_configs.json"
    data = json.loads(assets.read_text())
    return Aircraft.from_config(data[config_name])


def _build_default_flight_plan() -> FlightPlan:
    plan = FlightPlan([
        Waypoint("KUBOG", -23.121, -46.888, 7000),
        Waypoint("MOPAR", -23.239, -46.732, 5000),
        Waypoint("FF10R", -23.370, -46.560, 3500),
        Waypoint("RW10R", -23.4250, -46.4850, 2459),
    ])
    return plan


def _nearby_runway_dicts(airport_db: AirportDatabase, fdm: FlightDynamics, max_nm: float = 15.0) -> list[dict]:
    """Return runway data dicts for airports within max_nm."""
    result = []
    for airport in airport_db.airports.values():
        if fdm.position.distance_nm(airport.as_position()) <= max_nm:
            for rwy in airport.runways:
                result.append({
                    "heading_deg": rwy.heading_deg,
                    "threshold_lat": rwy.threshold_lat,
                    "threshold_lon": rwy.threshold_lon,
                    "length_ft": rwy.length_ft,
                    "elevation_ft": rwy.elevation_ft,
                })
    return result


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("IFR Flight Simulator")
    clock = pygame.time.Clock()

    # ── Main Menu ─────────────────────────────────────────────────────────────
    menu = MainMenu(1280, 720)
    while not menu.done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            menu.handle_event(event)
        menu.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    selected_aircraft = menu.selected_aircraft
    selected_scenario_key = menu.selected_scenario

    # ── Sim setup ─────────────────────────────────────────────────────────────
    settings = Settings.load(Path(__file__).resolve().parent.parent / "settings.json")
    aircraft = _load_aircraft(selected_aircraft)
    atmosphere = ISAAtmosphere()
    aerodynamics = Aerodynamics(aircraft)
    engine = Engine(aircraft.max_thrust_N)
    fdm = FlightDynamics()
    autopilot = Autopilot()
    weather = Weather(visibility_sm=1.0, ceiling_ft=500)
    terrain = Terrain()
    airport_db = AirportDatabase()
    failure_manager = FailureManager()
    logbook = Logbook()
    checklist = Checklist("Engine Start & Run-up", ENGINE_START_RUNUP)
    cockpit = CockpitView(1280, 720)
    hud = HUD()
    gps = GPS()
    flight_plan = _build_default_flight_plan()
    procedures = ProcedureDatabase()
    procedure_viewer = ProcedureViewer()
    ils_approaches = procedures.get_approaches("SBGR")
    if ils_approaches:
        procedure_viewer.load_procedure(ils_approaches[0])
    vor_receiver = VORReceiver()
    gru_vor = VOR("GRU", -23.4356, -46.4731, 116.9)
    vor_receiver.tune(116.9)
    atc = ATCController()
    scenario_engine = ScenarioEngine(atc, failure_manager)
    scenario_dict = _SCENARIO_MAP.get(selected_scenario_key, ILS_APPROACH)
    scenario_engine.load_scenario(scenario_dict)
    atc.generate_clearance(flight_plan)
    procedures.get_approaches("SBGR")

    # ── Sim state ────────────────────────────────────────────────────────────
    throttle_pct = 0.0
    master_on = False
    avionics_on = False
    mixture_pct = 100.0
    carb_heat_on = False
    magneto_positions = ["OFF", "R", "L", "BOTH"]
    magneto_index = 0
    starter_time_remaining = 0.0
    dg_heading_deg = fdm.attitude.yaw_deg
    user_controls = {"elevator": 0.0, "aileron": 0.0, "rudder": 0.0}
    flap_index = 0   # index into FLAP_POSITIONS

    # Radio / comms state
    com1_mhz = 122.800
    nav1_mhz = 110.30
    squawk_index = 0  # index into _SQUAWK_CODES
    squawk = _SQUAWK_CODES[squawk_index]

    # UI state
    paused = False
    show_procedure = False
    show_debrief = False
    debrief_text: str | None = None

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        if paused:
            dt = 0.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # ── Autopilot ─────────────────────────────────────────────
                if event.key == pygame.K_h:
                    autopilot.engage(APMode.HDG)
                    autopilot.set_target(heading=fdm.attitude.yaw_deg)
                elif event.key == pygame.K_l:
                    autopilot.engage(APMode.LNAV)
                elif event.key == pygame.K_v:
                    autopilot.engage(APMode.VS)
                    autopilot.set_target(vs=500)
                elif event.key == pygame.K_a:
                    autopilot.engage(APMode.ALT)
                    autopilot.set_target(altitude=fdm.position.altitude_ft)
                elif event.key == pygame.K_i:
                    autopilot.engage(APMode.APP)
                    atc.issue_approach_clearance("ILS 10R")
                elif event.key == pygame.K_o:
                    autopilot.engage(APMode.OFF)
                # ── Checklist ─────────────────────────────────────────────
                elif event.key == pygame.K_SPACE:
                    checklist.advance()
                # ── Engine controls ───────────────────────────────────────
                elif event.key == pygame.K_m:
                    master_on = not master_on
                    if not master_on:
                        avionics_on = False
                elif event.key == pygame.K_n:
                    if master_on:
                        avionics_on = not avionics_on
                elif event.key == pygame.K_r:
                    magneto_index = (magneto_index + 1) % len(magneto_positions)
                elif event.key == pygame.K_s:
                    starter_time_remaining = 0.8
                elif event.key == pygame.K_PERIOD:
                    mixture_pct = min(100.0, mixture_pct + 10.0)
                elif event.key == pygame.K_COMMA:
                    mixture_pct = max(0.0, mixture_pct - 10.0)
                elif event.key == pygame.K_c:
                    carb_heat_on = not carb_heat_on
                # ── Flaps ─────────────────────────────────────────────────
                elif event.key == pygame.K_f:
                    flap_index = min(flap_index + 1, len(FLAP_POSITIONS) - 1)
                elif event.key == pygame.K_g:
                    flap_index = max(flap_index - 1, 0)
                # ── Radio ─────────────────────────────────────────────────
                elif event.key == pygame.K_LEFTBRACKET:
                    nav1_mhz = round(max(_NAV_MIN, nav1_mhz - _NAV_STEP), 2)
                    vor_receiver.tune(nav1_mhz)
                elif event.key == pygame.K_RIGHTBRACKET:
                    nav1_mhz = round(min(_NAV_MAX, nav1_mhz + _NAV_STEP), 2)
                    vor_receiver.tune(nav1_mhz)
                elif event.key == pygame.K_SEMICOLON:
                    com1_mhz = round(max(_COM_MIN, com1_mhz - _COM_STEP), 3)
                elif event.key == pygame.K_QUOTE:
                    com1_mhz = round(min(_COM_MAX, com1_mhz + _COM_STEP), 3)
                elif event.key == pygame.K_t:
                    squawk_index = (squawk_index + 1) % len(_SQUAWK_CODES)
                    squawk = _SQUAWK_CODES[squawk_index]
                # ── UI ────────────────────────────────────────────────────
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_b:
                    show_procedure = not show_procedure
                elif event.key == pygame.K_d:
                    show_debrief = not show_debrief
                    if show_debrief:
                        debrief_text = scenario_engine.get_grade_report()
                    else:
                        debrief_text = None
                # ── Main menu (ESC) ───────────────────────────────────────
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not paused:
            keys = pygame.key.get_pressed()
            user_controls["elevator"] = float(keys[pygame.K_DOWN]) - float(keys[pygame.K_UP])
            user_controls["aileron"] = float(keys[pygame.K_RIGHT]) - float(keys[pygame.K_LEFT])
            user_controls["rudder"] = float(keys[pygame.K_x]) - float(keys[pygame.K_z])
            throttle_pct = min(100.0, max(0.0, throttle_pct + (float(keys[pygame.K_EQUALS]) - float(keys[pygame.K_MINUS])) * 25.0 * dt))
            if not master_on:
                avionics_on = False
            starter_time_remaining = max(0.0, starter_time_remaining - dt)

            engine.set_controls(
                master_on=master_on,
                avionics_on=avionics_on,
                magneto_position=magneto_positions[magneto_index],
                mixture_pct=mixture_pct,
                carb_heat_on=carb_heat_on,
                starter_engaged=starter_time_remaining > 0.0,
            )
            engine.update_system_state(aircraft.fuel_kg)

            flaps_deg = float(FLAP_POSITIONS[flap_index])
            state = {
                "heading_deg": fdm.attitude.yaw_deg,
                "roll_deg": fdm.attitude.roll_deg,
                "pitch_deg": fdm.attitude.pitch_deg,
                "altitude_ft": fdm.position.altitude_ft,
                "vertical_speed_fpm": fdm.vertical_speed_fpm,
                "position": fdm.position,
            }
            ap_controls = autopilot.compute_controls(state, flight_plan, gps, vor_receiver, dt)
            controls = {
                "throttle_pct": throttle_pct,
                "elevator": ap_controls["elevator"] if autopilot.vertical_mode != APMode.OFF else user_controls["elevator"],
                "aileron": ap_controls["aileron"] if autopilot.lateral_mode != APMode.OFF else user_controls["aileron"],
                "rudder": ap_controls["rudder"] if autopilot.lateral_mode != APMode.OFF else user_controls["rudder"],
                "flaps_deg": flaps_deg,
            }

            fdm_state = fdm.update(dt, controls, aircraft, atmosphere, aerodynamics, engine, weather)
            gps.update(fdm.position, flight_plan, dt)
            scenario_engine.update(fdm_state, dt)
            if engine.suction_inhg >= DG_MINIMUM_SUCTION_INHG:
                heading_error = (
                    (fdm.attitude.yaw_deg - dg_heading_deg + HEADING_WRAP_OFFSET_DEG)
                    % FULL_CIRCLE_DEG
                ) - HALF_CIRCLE_DEG
                dg_heading_deg = (
                    dg_heading_deg
                    + heading_error * min(1.0, dt * DG_FOLLOW_GAIN)
                    + dt * DG_DRIFT_DEG_PER_SEC
                ) % FULL_CIRCLE_DEG

        next_waypoint = flight_plan.active_waypoint().name if flight_plan.active_waypoint() else "---"
        nearest = airport_db.nearest_airport(fdm.position, 30.0)
        instrument_heading = failure_manager.modify_instrument_reading("heading_indicator", dg_heading_deg)
        attitude_scale = failure_manager.modify_instrument_reading("attitude_indicator", 1.0)
        instrument_pitch = fdm_state["pitch_deg"] * attitude_scale
        instrument_roll = fdm_state["roll_deg"] * attitude_scale
        instrument_airspeed = failure_manager.modify_instrument_reading("airspeed_indicator", fdm_state["airspeed_kts"])
        instrument_altitude = failure_manager.modify_instrument_reading("altimeter", fdm_state["altitude_ft"])
        instrument_vsi = failure_manager.modify_instrument_reading("vsi", fdm_state["vertical_speed_fpm"])

        # ILS deviation for CDI
        loc_dev, gs_dev, loc_valid, gs_valid = 0.0, 0.0, False, False
        if engine.avionics_powered:
            loc_dev = SBGR_ILS_10R.get_localizer_deviation(fdm.position)
            gs_dev = SBGR_ILS_10R.get_glideslope_deviation(fdm.position, fdm.position.altitude_ft)
            lat1 = radians(fdm.position.latitude_deg)
            lon1 = radians(fdm.position.longitude_deg)
            lat2 = radians(SBGR_ILS_10R.runway_threshold_lat)
            lon2 = radians(SBGR_ILS_10R.runway_threshold_lon)
            _a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
            dist_nm = (6_371_000.0 * 2.0 * atan2(_haversine_sqrt(_a), _haversine_sqrt(max(1e-12, 1.0 - _a)))) / 1852.0
            loc_valid = dist_nm < 25.0
            gs_valid = dist_nm < 12.0 and fdm.position.altitude_ft < 5000.0

        state = {
            **fdm_state,
            "heading_deg": instrument_heading,
            "pitch_deg": instrument_pitch,
            "roll_deg": instrument_roll,
            "airspeed_kts": instrument_airspeed,
            "altitude_ft": instrument_altitude,
            "vertical_speed_fpm": instrument_vsi,
            "position": fdm.position,
            "waypoints": flight_plan.waypoints,
            "active_leg": flight_plan.active_leg,
            "distance_to_next_nm": gps.distance_to_next_nm,
            "bearing_to_next_deg": gps.bearing_to_next_deg,
            "cross_track_error_nm": gps.cross_track_error_nm,
            "ete_min": gps.ete_min,
            "n1_pct": failure_manager.modify_instrument_reading("engine", engine.n1_pct),
            "rpm": engine.rpm,
            "fuel_kg": aircraft.fuel_kg,
            "max_fuel_kg": aircraft.max_fuel_kg,
            "oil_pressure_psi": 55.0 + (engine.rpm / engine.MAX_RPM) * 28.0 if engine.engine_running else 10.0,
            "oil_temp_c": 45.0 + engine.rpm / engine.MAX_RPM * 80.0 if engine.engine_running else 35.0,
            "egt_c": 500.0 + engine.n1_pct * 2.0,
            "suction_inhg": engine.suction_inhg,
            "bus_voltage_v": engine.bus_voltage_v,
            "master_on": master_on,
            "avionics_on": avionics_on,
            "avionics_powered": engine.avionics_powered,
            "engine_running": engine.engine_running,
            "magneto_position": magneto_positions[magneto_index],
            "mixture_pct": mixture_pct,
            "carb_heat_on": carb_heat_on,
            "baro_inhg": 29.92,
            "next_waypoint": next_waypoint,
            "atc_messages": scenario_engine.get_active_messages(),
            "checklist_status": f"{checklist.name}: {'COMPLETE' if checklist.is_complete else checklist.items[min(checklist.current_item_index, len(checklist.items)-1)].text}",
            "nearest_airport": nearest.icao if nearest else "---",
            # Phase 1: ILS CDI
            "loc_deviation": loc_dev,
            "gs_deviation": gs_dev,
            "loc_valid": loc_valid,
            "gs_valid": gs_valid,
            "ils_course_deg": 100.0,
            # Phase 2: visual
            "weather_ceiling_ft": weather.ceiling_ft,
            "nearby_runways": _nearby_runway_dicts(airport_db, fdm),
            # Phase 4: radio
            "com1_mhz": com1_mhz,
            "nav1_mhz": nav1_mhz,
            "squawk": squawk,
            # Phase 5: flaps / stall
            "flaps_deg": fdm_state.get("flaps_deg", 0.0),
            "stall_warning": fdm_state.get("stall_warning", False),
            # Phase 6: pause
            "paused": paused,
            # Phase 3: debrief
            "debrief_text": debrief_text if show_debrief else None,
        }

        screen.fill((20, 20, 20))
        cockpit.update(state)
        cockpit.draw(screen)
        hud.draw(screen, state, autopilot)

        # Phase 6: procedure viewer overlay
        if show_procedure:
            procedure_viewer.draw(screen)

        info_font = pygame.font.SysFont("arial", 14)
        info = info_font.render(
            f"Nearest: {state['nearest_airport']}  "
            f"Terrain: {terrain.get_elevation_ft(fdm.position.latitude_deg, fdm.position.longitude_deg):.0f}ft  "
            f"[I]=APP  [F/G]=FLAPS  [B]=PROC  [P]=PAUSE  [D]=DEBRIEF  [ESC]=MENU",
            True, (180, 180, 180)
        )
        screen.blit(info, (20, 700 - info.get_height()))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
