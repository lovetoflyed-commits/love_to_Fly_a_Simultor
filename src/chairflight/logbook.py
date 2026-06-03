from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass()
class LogEntry:
    date: str
    aircraft: str
    from_icao: str
    to_icao: str
    duration_h: float
    approaches: int
    holds: int
    notes: str


class Logbook:
    def __init__(self) -> None:
        self.entries: list[LogEntry] = []

    def add_entry(self, entry: LogEntry) -> None:
        self.entries.append(entry)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps([asdict(entry) for entry in self.entries], indent=2))

    def load(self, path: str | Path) -> None:
        file_path = Path(path)
        if not file_path.exists():
            self.entries = []
            return
        self.entries = [LogEntry(**item) for item in json.loads(file_path.read_text())]

    def total_time(self) -> float:
        return sum(entry.duration_h for entry in self.entries)

    def total_approaches(self) -> int:
        return sum(entry.approaches for entry in self.entries)

    def total_holds(self) -> int:
        return sum(entry.holds for entry in self.entries)
