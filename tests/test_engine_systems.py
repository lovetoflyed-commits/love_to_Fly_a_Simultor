from src.fdm.atmosphere import ISAAtmosphere
from src.fdm.engine import Engine


def test_engine_requires_valid_start_configuration_for_thrust() -> None:
    engine = Engine(10_000)
    atmosphere = ISAAtmosphere()
    engine.set_controls(
        master_on=True,
        avionics_on=False,
        magneto_position="BOTH",
        mixture_pct=100.0,
        carb_heat_on=False,
        starter_engaged=False,
    )
    engine.engine_running = False
    engine.update_system_state(40.0)
    assert engine.compute_thrust(80.0, 2000.0, atmosphere) == 0.0

    engine.set_controls(
        master_on=True,
        avionics_on=True,
        magneto_position="BOTH",
        mixture_pct=100.0,
        carb_heat_on=False,
        starter_engaged=True,
    )
    engine.update_system_state(40.0)
    assert engine.engine_running
    assert engine.compute_thrust(80.0, 2000.0, atmosphere) > 0.0
    assert engine.avionics_powered


def test_mixture_and_carb_heat_reduce_available_thrust() -> None:
    engine = Engine(10_000)
    atmosphere = ISAAtmosphere()

    engine.set_controls(
        master_on=True,
        avionics_on=True,
        magneto_position="BOTH",
        mixture_pct=100.0,
        carb_heat_on=False,
        starter_engaged=True,
    )
    engine.update_system_state(40.0)
    baseline_thrust = engine.compute_thrust(85.0, 3000.0, atmosphere)

    engine.set_controls(
        master_on=True,
        avionics_on=True,
        magneto_position="BOTH",
        mixture_pct=25.0,
        carb_heat_on=True,
        starter_engaged=False,
    )
    engine.update_system_state(40.0)
    degraded_thrust = engine.compute_thrust(85.0, 3000.0, atmosphere)

    assert degraded_thrust < baseline_thrust


def test_engine_instrument_power_indications_follow_system_state() -> None:
    engine = Engine(10_000)
    atmosphere = ISAAtmosphere()

    engine.set_controls(
        master_on=False,
        avionics_on=False,
        magneto_position="OFF",
        mixture_pct=0.0,
        carb_heat_on=False,
        starter_engaged=False,
    )
    engine.update_system_state(40.0)
    assert engine.bus_voltage_v == 0.0
    assert engine.suction_inhg == 0.0

    engine.set_controls(
        master_on=True,
        avionics_on=True,
        magneto_position="BOTH",
        mixture_pct=100.0,
        carb_heat_on=False,
        starter_engaged=True,
    )
    engine.update_system_state(40.0)
    engine.compute_thrust(65.0, 2000.0, atmosphere)
    assert engine.bus_voltage_v > 12.0
    assert engine.suction_inhg > 2.0
