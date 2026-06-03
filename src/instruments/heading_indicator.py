from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class HeadingIndicator(Instrument):
    def __init__(self, width: int = 180, height: int = 180) -> None:
        super().__init__(width, height)
        self.heading_deg = 0.0

    def update(self, state: dict) -> None:
        self.heading_deg = float(state.get("heading_deg", 0.0))

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        center = pygame.Vector2(self.width / 2, self.height / 2)
        radius = min(self.width, self.height) // 2 - 14
        card = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for heading in range(0, 360, 10):
            angle = math.radians(90 - heading)
            inner_len = radius - (18 if heading % 30 == 0 else 10)
            inner = (center.x + math.cos(angle) * inner_len, center.y - math.sin(angle) * inner_len)
            outer = (center.x + math.cos(angle) * radius, center.y - math.sin(angle) * radius)
            pygame.draw.line(card, (255, 255, 255), inner, outer, 2)
            if heading % 30 == 0:
                label = {0: "N", 90: "E", 180: "S", 270: "W"}.get(heading, str(heading // 10))
                text = self.font.render(label, True, (240, 240, 240))
                tx = center.x + math.cos(angle) * (radius - 32) - text.get_width() / 2
                ty = center.y - math.sin(angle) * (radius - 32) - text.get_height() / 2
                card.blit(text, (tx, ty))
        rotated = self._rotate_surface(card, self.heading_deg)
        self.surface.blit(rotated, rotated.get_rect(center=center))
        pygame.draw.polygon(self.surface, (255, 200, 0), [(center.x, 14), (center.x - 7, 28), (center.x + 7, 28)])
        pygame.draw.rect(self.surface, (15, 15, 15), pygame.Rect(center.x - 24, self.height - 34, 48, 22))
        text = self.large_font.render(f"{self.heading_deg:03.0f}", True, (255, 255, 255))
        self.surface.blit(text, text.get_rect(center=(center.x, self.height - 23)))
        return self.surface
