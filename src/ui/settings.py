from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass()
class Settings:
    aircraft_config: str = "C152"
    graphics_quality: str = "medium"
    key_bindings: dict[str, str] = field(default_factory=lambda: {
        "elevator_up": "K_UP",
        "elevator_down": "K_DOWN",
        "aileron_left": "K_LEFT",
        "aileron_right": "K_RIGHT",
        "rudder_left": "K_z",
        "rudder_right": "K_x",
        "throttle_up": "K_EQUALS",
        "throttle_down": "K_MINUS",
        "autopilot_heading": "K_h",
        "checklist_next": "K_SPACE",
    })
    joystick_enabled: bool = False

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "Settings":
        file_path = Path(path)
        if not file_path.exists():
            return cls()
        return cls(**json.loads(file_path.read_text()))
