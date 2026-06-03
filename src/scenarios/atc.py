from __future__ import annotations

from dataclasses import dataclass

from ..models.flight_plan import FlightPlan


@dataclass(slots=True)
class ATCMessage:
    time_sec: float
    sender: str
    text: str


class ATCController:
    def __init__(self) -> None:
        self.time_sec = 0.0
        self.messages: list[ATCMessage] = []
        self._last_auto_message = -999.0

    def _push(self, text: str, sender: str = "ATC") -> ATCMessage:
        message = ATCMessage(self.time_sec, sender, text)
        self.messages.append(message)
        self.messages = self.messages[-8:]
        return message

    def generate_clearance(self, flight_plan: FlightPlan) -> ATCMessage:
        route = " ".join(waypoint.name for waypoint in flight_plan.waypoints[:5]) or "as filed"
        return self._push(f"Cleared IFR route {route}. Climb and maintain 3000.")

    def issue_heading(self, heading: int) -> ATCMessage:
        return self._push(f"Fly heading {heading:03d}.")

    def issue_altitude(self, altitude: int) -> ATCMessage:
        return self._push(f"Maintain {altitude} feet.")

    def issue_approach_clearance(self, ils: str) -> ATCMessage:
        return self._push(f"Cleared {ils} approach.")

    def update(self, state: dict, dt: float) -> list[ATCMessage]:
        self.time_sec += dt
        if self.time_sec - self._last_auto_message > 20.0:
            altitude = int(state.get("altitude_ft", 0.0))
            heading = int(state.get("heading_deg", 0.0))
            self._push(f"Radar contact. Say altitude. We show {altitude} feet, heading {heading:03d}.")
            self._last_auto_message = self.time_sec
        return list(self.messages)
