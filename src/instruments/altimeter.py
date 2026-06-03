from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class Altimeter(Instrument):
    def __init__(self, width: int = 180, height: int = 180) -> None:
        super().__init__(width, height)
        self.altitude_ft = 0.0
        self.baro_inhg = 29.92

    def update(self, state: dict) -> None:
        self.altitude_ft = float(state.get("altitude_ft", 0.0))
        self.baro_inhg = float(state.get("baro_inhg", 29.92))

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        center = pygame.Vector2(self.width / 2, self.height / 2)
        radius = min(self.width, self.height) // 2 - 14
        for value in range(0, 1000, 100):
            angle = math.radians(90 - value * 0.36)
            inner = (center.x + math.cos(angle) * (radius - 12), center.y - math.sin(angle) * (radius - 12))
            outer = (center.x + math.cos(angle) * radius, center.y - math.sin(angle) * radius)
            pygame.draw.line(self.surface, (255, 255, 255), inner, outer, 2)
        hundreds = self.altitude_ft % 1000.0
        angle = math.radians(90 - hundreds * 0.36)
        tip = (center.x + math.cos(angle) * (radius - 18), center.y - math.sin(angle) * (radius - 18))
        pygame.draw.line(self.surface, (255, 255, 255), center, tip, 3)
        drum_rect = pygame.Rect(self.width / 2 - 44, self.height / 2 + 16, 88, 34)
        pygame.draw.rect(self.surface, (20, 20, 20), drum_rect, border_radius=4)
        pygame.draw.rect(self.surface, (130, 130, 130), drum_rect, 1, border_radius=4)
        digits = self.large_font.render(f"{int(self.altitude_ft):05d}", True, (250, 250, 250))
        self.surface.blit(digits, digits.get_rect(center=drum_rect.center))
        baro_rect = pygame.Rect(self.width / 2 - 34, self.height - 34, 68, 20)
        pygame.draw.rect(self.surface, (20, 20, 20), baro_rect)
        baro_text = self.small_font.render(f"{self.baro_inhg:0.2f}", True, (200, 220, 255))
        self.surface.blit(baro_text, baro_text.get_rect(center=baro_rect.center))
        return self.surface
