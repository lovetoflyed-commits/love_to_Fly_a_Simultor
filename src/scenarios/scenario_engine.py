from __future__ import annotations

from dataclasses import dataclass

from .atc import ATCController, ATCMessage
from .failures import FailureManager, SystemFailure


@dataclass(slots=True)
class ScenarioEvent:
    trigger_time_sec: float
    event_type: str
    params: dict


class ScenarioEngine:
    def __init__(self, atc: ATCController | None = None, failures: FailureManager | None = None) -> None:
        self.atc = atc or ATCController()
        self.failures = failures or FailureManager()
        self.events: list[ScenarioEvent] = []
        self.time_sec = 0.0
        self._fired: set[int] = set()

    def load_scenario(self, scenario_dict: dict) -> None:
        self.time_sec = 0.0
        self._fired.clear()
        self.events = [ScenarioEvent(event["trigger_time_sec"], event["event_type"], event.get("params", {})) for event in scenario_dict.get("events", [])]

    def update(self, state: dict, dt: float) -> None:
        self.time_sec += dt
        self.atc.update(state, dt)
        for index, event in enumerate(self.events):
            if index in self._fired or self.time_sec < event.trigger_time_sec:
                continue
            self._fired.add(index)
            if event.event_type == "atc_message":
                self.atc._push(event.params.get("text", "Scenario message"))
            elif event.event_type == "failure":
                self.failures.inject(SystemFailure[event.params["failure"]], event.params.get("severity", 1.0))
            elif event.event_type == "heading":
                self.atc.issue_heading(int(event.params["heading"]))
            elif event.event_type == "altitude":
                self.atc.issue_altitude(int(event.params["altitude"]))

    def get_active_messages(self) -> list[ATCMessage]:
        return list(self.atc.messages)
