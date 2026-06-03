from __future__ import annotations

from dataclasses import dataclass


@dataclass()
class ChecklistItem:
    text: str
    action_required: bool = True


class Checklist:
    def __init__(self, name: str, items: list[ChecklistItem]) -> None:
        self.name = name
        self.items = items
        self.current_item_index = 0

    def advance(self) -> None:
        if self.current_item_index < len(self.items):
            self.current_item_index += 1

    def reset(self) -> None:
        self.current_item_index = 0

    @property
    def is_complete(self) -> bool:
        return self.current_item_index >= len(self.items)


BEFORE_TAKEOFF = [
    ChecklistItem("Parking brake set"),
    ChecklistItem("Fuel shutoff valve in"),
    ChecklistItem("Master switch ON"),
    ChecklistItem("Mixture RICH"),
    ChecklistItem("Magnetos BOTH"),
    ChecklistItem("Starter engage, then release"),
    ChecklistItem("Oil pressure check"),
    ChecklistItem("Avionics switch ON"),
    ChecklistItem("Run-up 1700 RPM, mags checked"),
    ChecklistItem("Flight controls free and correct"),
    ChecklistItem("Instruments set and checked"),
    ChecklistItem("Departure briefing complete"),
]
CRUISE = [ChecklistItem("Power set"), ChecklistItem("Mixture adjusted"), ChecklistItem("Fuel balance checked")]
APPROACH = [ChecklistItem("ATIS / weather reviewed"), ChecklistItem("Approach briefed"), ChecklistItem("Nav radios identified")]
BEFORE_LANDING = [ChecklistItem("Fuel selector fullest tank"), ChecklistItem("Mixture rich"), ChecklistItem("Landing light on")]
AFTER_LANDING = [ChecklistItem("Flaps up"), ChecklistItem("Transponder standby"), ChecklistItem("Strobe lights off")]
