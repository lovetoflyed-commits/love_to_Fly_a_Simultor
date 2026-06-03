from __future__ import annotations

from enum import Enum, auto


class SystemFailure(Enum):
    VACUUM = auto()
    PITOT_STATIC = auto()
    ENGINE_FAILURE = auto()
    ALTERNATOR = auto()
    GEAR_WARNING = auto()


class FailureManager:
    def __init__(self) -> None:
        self.active_failures: dict[SystemFailure, float] = {}

    def inject(self, failure: SystemFailure, severity: float = 1.0) -> None:
        self.active_failures[failure] = severity

    def clear(self, failure: SystemFailure) -> None:
        self.active_failures.pop(failure, None)

    def is_active(self, failure: SystemFailure) -> bool:
        return failure in self.active_failures

    def modify_instrument_reading(self, instrument_name: str, value: float) -> float:
        if instrument_name in {"attitude_indicator", "heading_indicator"} and self.is_active(SystemFailure.VACUUM):
            return value * 0.0
        if instrument_name in {"airspeed_indicator", "altimeter", "vsi"} and self.is_active(SystemFailure.PITOT_STATIC):
            return value * 0.9
        if instrument_name == "engine" and self.is_active(SystemFailure.ENGINE_FAILURE):
            return value * 0.1
        return value
