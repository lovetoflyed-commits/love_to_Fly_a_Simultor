from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from ..models.flight_plan import Waypoint


@dataclass(slots=True)
class Procedure:
    name: str
    type: str
    waypoints: list[Waypoint]
    transitions: dict[str, list[str]] = field(default_factory=dict)
    airport_icao: str = ""


class ProcedureDatabase:
    def __init__(self) -> None:
        self.procedures = self._built_in_procedures()

    def load_from_file(self, path: str | Path) -> None:
        raw = json.loads(Path(path).read_text())
        self.procedures = []
        for item in raw:
            wpts = [Waypoint(**waypoint) for waypoint in item.get("waypoints", [])]
            self.procedures.append(Procedure(item["name"], item["type"], wpts, item.get("transitions", {}), item.get("airport_icao", "")))

    def get_approaches(self, airport_icao: str) -> list[Procedure]:
        return [p for p in self.procedures if p.airport_icao == airport_icao and p.type == "APPROACH"]

    def get_sids(self, airport_icao: str) -> list[Procedure]:
        return [p for p in self.procedures if p.airport_icao == airport_icao and p.type == "SID"]

    def get_stars(self, airport_icao: str) -> list[Procedure]:
        return [p for p in self.procedures if p.airport_icao == airport_icao and p.type == "STAR"]

    @staticmethod
    def _built_in_procedures() -> list[Procedure]:
        return [
            Procedure(
                name="ILS RWY 28L",
                type="APPROACH",
                airport_icao="KSFO",
                waypoints=[
                    Waypoint("CEDES", 37.756, -122.470, 4000),
                    Waypoint("FF28L", 37.683, -122.444, 3000),
                    Waypoint("RW28L", 37.6136, -122.3572, 0),
                ],
                transitions={"SFO": ["CEDES", "FF28L", "RW28L"]},
            )
        ]
