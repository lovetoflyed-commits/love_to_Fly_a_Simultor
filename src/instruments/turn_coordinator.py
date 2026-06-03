from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class TurnCoordinator(Instrument):
    """Turn coordinator for the Cessna 152.

    Shows a miniature-airplane silhouette that banks left/right to indicate
    rate of turn, with standard-rate markers at ±3 °/s (~18 ° of bank at
    cruise), and a simple inclinometer (ball) at the bottom.
    """

    def __init__(self, width: int = 150, height: int = 150) -> None:
        super().__init__(width, height)
        self.roll_deg = 0.0

    def update(self, state: dict) -> None:
        self.roll_deg = float(state.get("roll_deg", 0.0))

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        center = pygame.Vector2(self.width / 2, self.height / 2)
        radius = min(self.width, self.height) // 2 - 10

        # Standard-rate tick marks (±27° from top ≈ ±3 °/s at cruise)
        for direction in (-1, 1):
            tick_angle = math.radians(90 - direction * 27)
            ox = center.x + math.cos(tick_angle) * radius
            oy = center.y - math.sin(tick_angle) * radius
            ix = center.x + math.cos(tick_angle) * (radius - 14)
            iy = center.y - math.sin(tick_angle) * (radius - 14)
            pygame.draw.line(self.surface, (255, 255, 255), (ox, oy), (ix, iy), 3)
            # "L" / "R" labels
            label_txt = "L" if direction == -1 else "R"
            lbl = self.small_font.render(label_txt, True, (200, 200, 200))
            lx = center.x + math.cos(tick_angle) * (radius - 26) - lbl.get_width() / 2
            ly = center.y - math.sin(tick_angle) * (radius - 26) - lbl.get_height() / 2
            self.surface.blit(lbl, (lx, ly))

        # "2 MIN TURN" annotation
        label_2min = self.small_font.render("2 MIN TURN", True, (180, 180, 180))
        self.surface.blit(
            label_2min,
            label_2min.get_rect(center=(center.x, center.y + radius - 20)),
        )

        # Miniature airplane — bank angle is 1.5× roll (standard-rate at ~18°)
        tc_bank = max(-35.0, min(35.0, self.roll_deg * 1.5))
        airplane_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ac_cx = int(self.width / 2)
        ac_cy = int(self.height / 2) - 4
        wing_half = 30
        tail_half = 11
        # Left wing
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx - wing_half, ac_cy), (ac_cx - 6, ac_cy), 3)
        # Right wing
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx + 6, ac_cy), (ac_cx + wing_half, ac_cy), 3)
        # Fuselage centre dot
        pygame.draw.circle(airplane_surf, (255, 255, 255), (ac_cx, ac_cy), 4)
        # Tail
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx - tail_half, ac_cy - 8),
                         (ac_cx + tail_half, ac_cy - 8), 2)
        rotated = self._rotate_surface(airplane_surf, tc_bank)
        self.surface.blit(rotated, rotated.get_rect(center=center))

        # Reference centre tick at top of arc
        pygame.draw.rect(self.surface, (255, 200, 0),
                         pygame.Rect(int(center.x) - 2, int(center.y) - radius + 2, 4, 10))

        # Inclinometer (ball) strip at bottom
        strip_y = int(self.height - 20)
        strip_rect = pygame.Rect(int(center.x) - 30, strip_y - 9, 60, 18)
        pygame.draw.rect(self.surface, (18, 18, 18), strip_rect, border_radius=9)
        pygame.draw.rect(self.surface, (100, 100, 100), strip_rect, 1, border_radius=9)
        # Centre index dots
        for dx in (-14, 0, 14):
            pygame.draw.circle(self.surface, (75, 75, 75),
                               (int(center.x) + dx, strip_y), 2)
        # Ball (simplified — centered; realistic slip requires lateral-accel data)
        ball_x = int(center.x)
        pygame.draw.circle(self.surface, (5, 5, 5), (ball_x, strip_y), 7)
        pygame.draw.circle(self.surface, (160, 160, 160), (ball_x, strip_y), 7, 1)

        return self.surface
