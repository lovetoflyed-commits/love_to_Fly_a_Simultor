from __future__ import annotations

from dataclasses import dataclass, field

from ..models.position import Position


@dataclass()
class Runway:
    name: str
    heading_deg: float
    threshold_lat: float
    threshold_lon: float
    length_ft: int
    elevation_ft: int


@dataclass()
class Airport:
    icao: str
    name: str
    lat: float
    lon: float
    elevation_ft: int
    runways: list[Runway] = field(default_factory=list)

    def as_position(self) -> Position:
        return Position(self.lat, self.lon, self.elevation_ft)


class AirportDatabase:
    def __init__(self) -> None:
        self.airports = {airport.icao: airport for airport in self._build_airports()}

    def get_airport(self, icao: str) -> Airport | None:
        return self.airports.get(icao)

    def nearest_airport(self, position: Position, max_nm: float = 50.0) -> Airport | None:
        closest = None
        best_distance = max_nm
        for airport in self.airports.values():
            distance = position.distance_nm(airport.as_position())
            if distance <= best_distance:
                best_distance = distance
                closest = airport
        return closest

    @staticmethod
    def _build_airports() -> list[Airport]:
        return [
            Airport("SBGR", "Sao Paulo/Guarulhos Intl", -23.4356, -46.4731, 2459, [Runway("10L", 100, -23.4407, -46.4868, 9843, 2459), Runway("10R", 100, -23.4250, -46.4850, 12139, 2459)]),
            Airport("SBSP", "Sao Paulo/Congonhas", -23.6261, -46.6564, 2631, [Runway("17R", 170, -23.6222, -46.6545, 6365, 2631), Runway("17L", 170, -23.6201, -46.6509, 6365, 2631)]),
            Airport("KSFO", "San Francisco Intl", 37.6188056, -122.3754167, 13, [Runway("28L", 284, 37.6136, -122.3572, 11870, 13), Runway("28R", 284, 37.6195, -122.3738, 11870, 13)]),
            Airport("KLAX", "Los Angeles Intl", 33.9425, -118.4081, 125, [Runway("25L", 251, 33.9427, -118.4210, 12091, 125), Runway("25R", 251, 33.9435, -118.4079, 11095, 125)]),
            Airport("KORD", "Chicago O'Hare Intl", 41.9742, -87.9073, 672, [Runway("27C", 271, 41.9786, -87.9048, 11000, 672)]),
            Airport("KJFK", "John F. Kennedy Intl", 40.6413, -73.7781, 13, [Runway("22L", 224, 40.6518, -73.7809, 12079, 13)]),
            Airport("EGLL", "London Heathrow", 51.47, -0.4543, 83, [Runway("27L", 269, 51.4775, -0.4614, 12799, 83)]),
        ]
