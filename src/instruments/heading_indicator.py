from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class HeadingIndicator(Instrument):
    """Directional Gyro / Heading Indicator for the Cessna 152.

    Compass rose rotates with heading. Cardinal directions highlighted in white,
    10° graduations with labels every 30° (N/E/S/W + numeric), minor ticks
    every 5°.  Fixed lubber line at 12-o'clock.
    """

    def __init__(self, width: int = 150, height: int = 150) -> None:
        super().__init__(width, height)
        self.heading_deg = 0.0

    def update(self, state: dict) -> None:
        self.heading_deg = float(state.get("heading_deg", 0.0))

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        cx = self.width / 2
        cy = self.height / 2
        center = (cx, cy)
        radius = min(self.width, self.height) // 2 - 12

        # ── Rotating compass card ────────────────────────────────────────
        card = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cardinals = {0: "N", 90: "E", 180: "S", 270: "W"}

        for hdg in range(0, 360, 5):
            angle = math.radians(90 - hdg)
            major30 = hdg % 30 == 0
            major10 = hdg % 10 == 0
            inner_len = radius - (20 if major30 else (12 if major10 else 6))
            inner = (cx + math.cos(angle) * inner_len, cy - math.sin(angle) * inner_len)
            outer = (cx + math.cos(angle) * radius, cy - math.sin(angle) * radius)
            lw = 2 if major30 else (1 if major10 else 1)
            color = (255, 255, 255) if major10 else (160, 160, 160)
            pygame.draw.line(card, color, inner, outer, lw)

            if major30:
                label_str = cardinals.get(hdg, str(hdg // 10))
                is_cardinal = hdg in cardinals
                font = self.font if is_cardinal else self.small_font
                txt_color = (255, 255, 255) if is_cardinal else (210, 210, 210)
                text = font.render(label_str, True, txt_color)
                # N is bigger/bolder
                if hdg == 0:
                    big_n = pygame.font.SysFont("arial", 14, bold=True)
                    text = big_n.render("N", True, (255, 60, 60))
                dist = radius - 34 if is_cardinal else radius - 32
                tx = cx + math.cos(angle) * dist - text.get_width() / 2
                ty = cy - math.sin(angle) * dist - text.get_height() / 2
                card.blit(text, (tx, ty))

        rotated = self._rotate_surface(card, self.heading_deg)
        self.surface.blit(rotated, rotated.get_rect(center=(int(cx), int(cy))))

        # ── Fixed lubber line (yellow triangle at top) ───────────────────
        pygame.draw.polygon(
            self.surface, (255, 200, 0),
            [(int(cx), int(cy) - radius + 2),
             (int(cx) - 7, int(cy) - radius + 16),
             (int(cx) + 7, int(cy) - radius + 16)],
        )

        # ── Digital heading box ──────────────────────────────────────────
        box_rect = pygame.Rect(int(cx) - 26, self.height - 30, 52, 22)
        pygame.draw.rect(self.surface, (15, 15, 15), box_rect, border_radius=3)
        pygame.draw.rect(self.surface, (80, 80, 80), box_rect, 1, border_radius=3)
        text = self.large_font.render(f"{self.heading_deg:03.0f}", True, (255, 255, 255))
        self.surface.blit(text, text.get_rect(center=(int(cx), self.height - 19)))

        return self.surface

