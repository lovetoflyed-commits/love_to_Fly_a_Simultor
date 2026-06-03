from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class AirspeedIndicator(Instrument):
    def __init__(self, width: int = 180, height: int = 180) -> None:
        super().__init__(width, height)
        self.airspeed_kts = 0.0

    def update(self, state: dict) -> None:
        self.airspeed_kts = float(state.get("airspeed_kts", 0.0))

    def _value_to_angle(self, value: float) -> float:
        return 225.0 - (max(0.0, min(300.0, value)) / 300.0) * 270.0

    def _draw_arc(self, color: tuple[int, int, int], start: float, end: float, radius: int, width: int = 6) -> None:
        rect = pygame.Rect(self.width / 2 - radius, self.height / 2 - radius, radius * 2, radius * 2)
        pygame.draw.arc(self.surface, color, rect, math.radians(-self._value_to_angle(start)), math.radians(-self._value_to_angle(end)), width)

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        center = pygame.Vector2(self.width / 2, self.height / 2)
        radius = min(self.width, self.height) // 2 - 14
        self._draw_arc((220, 220, 220), 0, 200, radius)
        self._draw_arc((0, 160, 0), 70, 200, radius - 4)
        self._draw_arc((200, 200, 0), 200, 260, radius - 8)
        self._draw_arc((220, 40, 40), 260, 300, radius - 12)
        for speed in range(0, 301, 20):
            angle = math.radians(self._value_to_angle(speed))
            inner = (center.x + math.cos(angle) * (radius - 15), center.y - math.sin(angle) * (radius - 15))
            outer = (center.x + math.cos(angle) * radius, center.y - math.sin(angle) * radius)
            pygame.draw.line(self.surface, (255, 255, 255), inner, outer, 2)
            text = self.small_font.render(str(speed), True, (230, 230, 230))
            tx = center.x + math.cos(angle) * (radius - 30) - text.get_width() / 2
            ty = center.y - math.sin(angle) * (radius - 30) - text.get_height() / 2
            self.surface.blit(text, (tx, ty))
        angle = math.radians(self._value_to_angle(self.airspeed_kts))
        tip = (center.x + math.cos(angle) * (radius - 18), center.y - math.sin(angle) * (radius - 18))
        pygame.draw.line(self.surface, (255, 80, 80), center, tip, 3)
        pygame.draw.circle(self.surface, (255, 80, 80), center, 5)
        digital = self.large_font.render(f"{self.airspeed_kts:03.0f}", True, (255, 255, 255))
        self.surface.blit(digital, digital.get_rect(center=(center.x, center.y + 40)))
        return self.surface
