from src.fdm.atmosphere import ISAAtmosphere


atm = ISAAtmosphere()


def test_isa_sea_level_conditions() -> None:
    conditions = atm.get_conditions(0)
    assert abs(conditions["temperature_K"] - 288.15) < 0.2
    assert abs(conditions["pressure_Pa"] - 101325.0) < 150.0
    assert abs(conditions["density_kg_m3"] - 1.225) < 0.02


def test_isa_10000ft_conditions() -> None:
    conditions = atm.get_conditions(10000)
    assert abs(conditions["temperature_K"] - 268.3) < 1.0
    assert abs(conditions["pressure_Pa"] - 69680.0) < 1500.0
    assert abs(conditions["density_kg_m3"] - 0.905) < 0.04


def test_isa_36000ft_conditions() -> None:
    conditions = atm.get_conditions(36000)
    assert abs(conditions["temperature_K"] - 216.65) < 1.0
    assert abs(conditions["pressure_Pa"] - 22700.0) < 2500.0
    assert abs(conditions["density_kg_m3"] - 0.365) < 0.06
