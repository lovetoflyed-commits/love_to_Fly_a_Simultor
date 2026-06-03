from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from ..models.flight_plan import Waypoint


@dataclass()
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
                name="ILS RWY 10R",
                type="APPROACH",
                airport_icao="SBGR",
                waypoints=[
                    Waypoint("MOPAR", -23.239, -46.732, 5000),
                    Waypoint("FF10R", -23.370, -46.560, 3500),
                    Waypoint("RW10R", -23.4250, -46.4850, 2459),
                ],
                transitions={"GRU": ["MOPAR", "FF10R", "RW10R"]},
            )
        ]
