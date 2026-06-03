from src.fdm.aerodynamics import Aerodynamics
from src.models.aircraft import Aircraft


aero = Aerodynamics(Aircraft("Test", 10000, 1100, 16.2, 180, 180))


def test_cl_computation_increases_with_alpha() -> None:
    assert aero.compute_cl(2) < aero.compute_cl(8)


def test_stall_detection() -> None:
    assert aero.is_stalled(17)
    assert not aero.is_stalled(10)


def test_lift_and_drag_positive() -> None:
    cl = aero.compute_cl(6)
    cd = aero.compute_cd(cl)
    lift = aero.compute_lift(1.225, 50, cl, 16.2)
    drag = aero.compute_drag(1.225, 50, cd, 16.2)
    assert lift > 0
    assert drag > 0
