from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class VSI(Instrument):
    def __init__(self, width: int = 180, height: int = 180) -> None:
        super().__init__(width, height)
        self.vertical_speed_fpm = 0.0

    def update(self, state: dict) -> None:
        self.vertical_speed_fpm = float(state.get("vertical_speed_fpm", 0.0))

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        center = pygame.Vector2(self.width / 2, self.height / 2)
        radius = min(self.width, self.height) // 2 - 14
        for vsi in (-2000, -1000, -500, 0, 500, 1000, 2000):
            angle = math.radians(-vsi / 2000.0 * 90.0)
            inner = (center.x + math.cos(angle) * (radius - 16), center.y - math.sin(angle) * (radius - 16))
            outer = (center.x + math.cos(angle) * radius, center.y - math.sin(angle) * radius)
            pygame.draw.line(self.surface, (255, 255, 255), inner, outer, 2)
            if vsi:
                label = self.small_font.render(str(abs(vsi) // 100), True, (230, 230, 230))
                lx = center.x + math.cos(angle) * (radius - 30) - label.get_width() / 2
                ly = center.y - math.sin(angle) * (radius - 30) - label.get_height() / 2
                self.surface.blit(label, (lx, ly))
        clamped = max(-2000.0, min(2000.0, self.vertical_speed_fpm))
        angle = math.radians(-clamped / 2000.0 * 90.0)
        tip = (center.x + math.cos(angle) * (radius - 18), center.y - math.sin(angle) * (radius - 18))
        pygame.draw.line(self.surface, (255, 255, 255), center, tip, 3)
        digital = self.font.render(f"{self.vertical_speed_fpm:+.0f}", True, (255, 255, 255))
        self.surface.blit(digital, digital.get_rect(center=(center.x, center.y + 48)))
        return self.surface
