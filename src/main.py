from __future__ import annotations

import json
from pathlib import Path
import sys

import pygame

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from src.chairflight.checklist import BEFORE_TAKEOFF, Checklist
    from src.chairflight.logbook import Logbook
    from src.environment.airport import AirportDatabase
    from src.environment.terrain import Terrain
    from src.environment.weather import Weather
    from src.fdm.aerodynamics import Aerodynamics
    from src.fdm.atmosphere import ISAAtmosphere
    from src.fdm.engine import Engine
    from src.fdm.flight_dynamics import FlightDynamics
    from src.models.aircraft import Aircraft
    from src.models.flight_plan import FlightPlan, Waypoint
    from src.navigation.autopilot import APMode, Autopilot
    from src.navigation.gps import GPS
    from src.navigation.procedures import ProcedureDatabase
    from src.navigation.vor import VOR, VORReceiver
    from src.scenarios.atc import ATCController
    from src.scenarios.failures import FailureManager
    from src.scenarios.scenario_engine import ScenarioEngine
    from src.scenarios.training_scenarios import ILS_APPROACH
    from src.ui.cockpit_view import CockpitView
    from src.ui.hud import HUD
    from src.ui.settings import Settings
else:
    from .chairflight.checklist import BEFORE_TAKEOFF, Checklist
    from .chairflight.logbook import Logbook
    from .environment.airport import AirportDatabase
    from .environment.terrain import Terrain
    from .environment.weather import Weather
    from .fdm.aerodynamics import Aerodynamics
    from .fdm.atmosphere import ISAAtmosphere
    from .fdm.engine import Engine
    from .fdm.flight_dynamics import FlightDynamics
    from .models.aircraft import Aircraft
    from .models.flight_plan import FlightPlan, Waypoint
    from .navigation.autopilot import APMode, Autopilot
    from .navigation.gps import GPS
    from .navigation.procedures import ProcedureDatabase
    from .navigation.vor import VOR, VORReceiver
    from .scenarios.atc import ATCController
    from .scenarios.failures import FailureManager
    from .scenarios.scenario_engine import ScenarioEngine
    from .scenarios.training_scenarios import ILS_APPROACH
    from .ui.cockpit_view import CockpitView
    from .ui.hud import HUD
    from .ui.settings import Settings


def _load_aircraft(config_name: str) -> Aircraft:
    assets = Path(__file__).resolve().parent.parent / "assets" / "data" / "aircraft_configs.json"
    data = json.loads(assets.read_text())
    return Aircraft.from_config(data[config_name])


def _build_default_flight_plan() -> FlightPlan:
    plan = FlightPlan([
        Waypoint("PORTE", 37.712, -122.488, 3000),
        Waypoint("CEDES", 37.756, -122.470, 3000),
        Waypoint("FF28L", 37.683, -122.444, 1800),
        Waypoint("RW28L", 37.6136, -122.3572, 13),
    ])
    return plan


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("IFR Flight Simulator")
    clock = pygame.time.Clock()

    settings = Settings.load(Path(__file__).resolve().parent.parent / "settings.json")
    aircraft = _load_aircraft(settings.aircraft_config)
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
    checklist = Checklist("Before Takeoff", BEFORE_TAKEOFF)
    cockpit = CockpitView(1280, 720)
    hud = HUD()
    gps = GPS()
    flight_plan = _build_default_flight_plan()
    procedures = ProcedureDatabase()
    vor_receiver = VORReceiver()
    sfo_vor = VOR("SFO", 37.619, -122.374, 115.8)
    vor_receiver.tune(115.8)
    atc = ATCController()
    scenario_engine = ScenarioEngine(atc, failure_manager)
    scenario_engine.load_scenario(ILS_APPROACH)
    atc.generate_clearance(flight_plan)
    procedures.get_approaches("KSFO")

    throttle_pct = 55.0
    user_controls = {"elevator": 0.0, "aileron": 0.0, "rudder": 0.0}
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
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
                elif event.key == pygame.K_o:
                    autopilot.engage(APMode.OFF)
                elif event.key == pygame.K_SPACE:
                    checklist.advance()

        keys = pygame.key.get_pressed()
        user_controls["elevator"] = float(keys[pygame.K_DOWN]) - float(keys[pygame.K_UP])
        user_controls["aileron"] = float(keys[pygame.K_RIGHT]) - float(keys[pygame.K_LEFT])
        user_controls["rudder"] = float(keys[pygame.K_x]) - float(keys[pygame.K_z])
        throttle_pct = min(100.0, max(0.0, throttle_pct + (float(keys[pygame.K_EQUALS]) - float(keys[pygame.K_MINUS])) * 25.0 * dt))

        state = {
            "heading_deg": fdm.attitude.yaw_deg,
            "roll_deg": fdm.attitude.roll_deg,
            "pitch_deg": fdm.attitude.pitch_deg,
            "altitude_ft": fdm.position.altitude_ft,
            "vertical_speed_fpm": fdm.vertical_speed_fpm,
        }
        ap_controls = autopilot.compute_controls(state, flight_plan, gps, vor_receiver, dt)
        controls = {
            "throttle_pct": throttle_pct,
            "elevator": ap_controls["elevator"] if autopilot.vertical_mode != APMode.OFF else user_controls["elevator"],
            "aileron": ap_controls["aileron"] if autopilot.lateral_mode != APMode.OFF else user_controls["aileron"],
            "rudder": ap_controls["rudder"] if autopilot.lateral_mode != APMode.OFF else user_controls["rudder"],
        }

        fdm_state = fdm.update(dt, controls, aircraft, atmosphere, aerodynamics, engine, weather)
        gps.update(fdm.position, flight_plan, dt)
        scenario_engine.update(fdm_state, dt)

        next_waypoint = flight_plan.active_waypoint().name if flight_plan.active_waypoint() else "---"
        nearest = airport_db.nearest_airport(fdm.position, 30.0)
        state = {
            **fdm_state,
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
            "oil_pressure_psi": 60.0 if aircraft.fuel_kg > 0 else 20.0,
            "oil_temp_c": 60.0 + engine.rpm / 2750.0 * 90.0,
            "egt_c": 500.0 + engine.n1_pct * 2.0,
            "baro_inhg": 29.92,
            "next_waypoint": next_waypoint,
            "atc_messages": scenario_engine.get_active_messages(),
            "checklist_status": f"{checklist.name}: {'COMPLETE' if checklist.is_complete else checklist.items[min(checklist.current_item_index, len(checklist.items)-1)].text}",
            "nearest_airport": nearest.icao if nearest else "---",
        }

        screen.fill((20, 20, 20))
        cockpit.update(state)
        cockpit.draw(screen)
        hud.draw(screen, state, autopilot)
        info_font = pygame.font.SysFont("arial", 14)
        info = info_font.render(f"Nearest: {state['nearest_airport']}  Terrain: {terrain.get_elevation_ft(fdm.position.latitude_deg, fdm.position.longitude_deg):.0f}ft", True, (180, 180, 180))
        screen.blit(info, (20, 700 - info.get_height()))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
