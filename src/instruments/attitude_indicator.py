from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class AttitudeIndicator(Instrument):
    def __init__(self, width: int = 220, height: int = 220) -> None:
        super().__init__(width, height)
        self.pitch_deg = 0.0
        self.roll_deg = 0.0

    def update(self, state: dict) -> None:
        self.pitch_deg = float(state.get("pitch_deg", 0.0))
        self.roll_deg = float(state.get("roll_deg", 0.0))

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        radius = min(self.width, self.height) // 2 - 10
        center = pygame.Vector2(self.width / 2, self.height / 2)

        horizon = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
        horizon.fill((88, 161, 219), pygame.Rect(0, 0, horizon.get_width(), horizon.get_height() // 2))
        horizon.fill((120, 80, 50), pygame.Rect(0, horizon.get_height() // 2, horizon.get_width(), horizon.get_height() // 2))
        pitch_offset = self.pitch_deg * 4.0
        pygame.draw.line(horizon, (240, 240, 240), (0, horizon.get_height() // 2 + pitch_offset), (horizon.get_width(), horizon.get_height() // 2 + pitch_offset), 3)
        for pitch in range(-30, 35, 5):
            if pitch == 0:
                continue
            y = horizon.get_height() // 2 + pitch_offset - pitch * 4.0
            length = 80 if pitch % 10 == 0 else 45
            pygame.draw.line(horizon, (250, 250, 250), (horizon.get_width() / 2 - length / 2, y), (horizon.get_width() / 2 + length / 2, y), 2)
            if pitch % 10 == 0:
                text = self.small_font.render(str(abs(pitch)), True, (255, 255, 255))
                horizon.blit(text, (horizon.get_width() / 2 + length / 2 + 6, y - 8))
                horizon.blit(text, (horizon.get_width() / 2 - length / 2 - text.get_width() - 6, y - 8))

        rotated = self._rotate_surface(horizon, self.roll_deg)
        rect = rotated.get_rect(center=(center.x, center.y + pitch_offset))
        mask = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255), center, radius)
        temp = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        temp.blit(rotated, rect)
        temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.surface.blit(temp, (0, 0))

        pygame.draw.circle(self.surface, (160, 160, 160), center, radius, 2)
        arc_radius = radius - 8
        for angle in (10, 20, 30, 45, 60):
            for direction in (-1, 1):
                tick_angle = math.radians(270 - direction * angle)
                inner = (center.x + math.cos(tick_angle) * (arc_radius - 10), center.y + math.sin(tick_angle) * (arc_radius - 10))
                outer = (center.x + math.cos(tick_angle) * arc_radius, center.y + math.sin(tick_angle) * arc_radius)
                pygame.draw.line(self.surface, (255, 255, 255), inner, outer, 2)
        pygame.draw.arc(self.surface, (220, 220, 220), (center.x - arc_radius, center.y - arc_radius, arc_radius * 2, arc_radius * 2), math.radians(210), math.radians(330), 2)
        pygame.draw.polygon(self.surface, (255, 200, 0), [(center.x, center.y - arc_radius - 2), (center.x - 6, center.y - arc_radius + 10), (center.x + 6, center.y - arc_radius + 10)])
        pygame.draw.line(self.surface, (255, 200, 0), (center.x - 40, center.y), (center.x - 10, center.y), 4)
        pygame.draw.line(self.surface, (255, 200, 0), (center.x + 10, center.y), (center.x + 40, center.y), 4)
        pygame.draw.line(self.surface, (255, 200, 0), (center.x - 10, center.y), (center.x + 10, center.y), 2)
        return self.surface
