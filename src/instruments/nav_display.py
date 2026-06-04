from __future__ import annotations

import math
import pygame

from ..models.position import Position
from .base_instrument import Instrument


class NavDisplay(Instrument):
    def __init__(self, width: int = 360, height: int = 240) -> None:
        super().__init__(width, height)
        self.position = Position(0.0, 0.0, 0.0)
        self.waypoints = []
        self.active_leg = 0
        self.bearing = 0.0
        self.distance = 0.0
        self.terrain_objects: list = []

    def update(self, state: dict) -> None:
        self.position = state.get("position", self.position)
        self.waypoints = state.get("waypoints", [])
        self.active_leg = int(state.get("active_leg", 0))
        self.bearing = float(state.get("bearing_to_next_deg", 0.0))
        self.distance = float(state.get("distance_to_next_nm", 0.0))
        self.terrain_objects = state.get("terrain_objects", [])

    def draw(self) -> pygame.Surface:
        self.surface.fill((26, 26, 26))
        for x in range(0, self.width, 40):
            pygame.draw.line(self.surface, (45, 45, 45), (x, 0), (x, self.height))
        for y in range(0, self.height, 40):
            pygame.draw.line(self.surface, (45, 45, 45), (0, y), (self.width, y))
        center = pygame.Vector2(self.width / 2, self.height / 2)
        scale = 8.0

        # ── Terrain objects ───────────────────────────────────────────────────
        for obj in self.terrain_objects:
            dlat = (obj.lat - self.position.latitude_deg) * 60.0
            dlon = (obj.lon - self.position.longitude_deg) * 60.0 * math.cos(math.radians(self.position.latitude_deg))
            px = center.x + dlon * scale
            py = center.y - dlat * scale
            if 0 <= px <= self.width and 0 <= py <= self.height:
                if obj.object_type == "hill":
                    # Brown triangle for hills
                    pygame.draw.polygon(self.surface, (140, 110, 60), [
                        (int(px), int(py) - 5),
                        (int(px) - 4, int(py) + 3),
                        (int(px) + 4, int(py) + 3),
                    ])
                elif obj.object_type == "tower":
                    pygame.draw.line(self.surface, (255, 80, 80), (int(px), int(py) - 5), (int(px), int(py) + 3), 2)
                    pygame.draw.circle(self.surface, (255, 60, 60), (int(px), int(py) - 5), 2)
                else:
                    pygame.draw.rect(self.surface, (180, 180, 80), pygame.Rect(int(px) - 2, int(py) - 2, 5, 5))
                lbl = self.small_font.render(obj.name, True, (160, 150, 120))
                self.surface.blit(lbl, (int(px) + 6, int(py) - 4))

        # ── Waypoints ─────────────────────────────────────────────────────────
        for idx, waypoint in enumerate(self.waypoints):
            dlat = (waypoint.lat - self.position.latitude_deg) * 60.0
            dlon = (waypoint.lon - self.position.longitude_deg) * 60.0 * math.cos(math.radians(self.position.latitude_deg))
            px = center.x + dlon * scale
            py = center.y - dlat * scale
            if 0 <= px <= self.width and 0 <= py <= self.height:
                color = (255, 0, 255) if idx == self.active_leg else (0, 255, 255)
                pygame.draw.circle(self.surface, color, (int(px), int(py)), 4)
                label = self.small_font.render(waypoint.name, True, color)
                self.surface.blit(label, (px + 6, py - 6))
        if self.waypoints and self.active_leg < len(self.waypoints):
            wp = self.waypoints[self.active_leg]
            dlat = (wp.lat - self.position.latitude_deg) * 60.0
            dlon = (wp.lon - self.position.longitude_deg) * 60.0 * math.cos(math.radians(self.position.latitude_deg))
            pygame.draw.line(self.surface, (255, 0, 255), center, (center.x + dlon * scale, center.y - dlat * scale), 2)
        pygame.draw.polygon(self.surface, (255, 255, 255), [(center.x, center.y - 12), (center.x - 8, center.y + 10), (center.x + 8, center.y + 10)])
        info = self.font.render(f"BRG {self.bearing:03.0f}  DIS {self.distance:05.1f}NM", True, (220, 220, 220))
        self.surface.blit(info, (10, self.height - 24))
        return self.surface
