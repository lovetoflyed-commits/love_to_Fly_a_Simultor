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
        cx = self.width / 2
        cy = self.height / 2
        center = (cx, cy)
        radius = min(self.width, self.height) // 2 - 10

        # Standard-rate tick marks (±27° from top ≈ ±3 °/s at cruise)
        for direction in (-1, 1):
            tick_angle = math.radians(90 - direction * 27)
            ox = cx + math.cos(tick_angle) * radius
            oy = cy - math.sin(tick_angle) * radius
            ix = cx + math.cos(tick_angle) * (radius - 16)
            iy = cy - math.sin(tick_angle) * (radius - 16)
            pygame.draw.line(self.surface, (255, 255, 255), (ox, oy), (ix, iy), 3)
            # "L" / "R" labels
            label_txt = "L" if direction == -1 else "R"
            lbl = self.small_font.render(label_txt, True, (200, 200, 200))
            lx = cx + math.cos(tick_angle) * (radius - 28) - lbl.get_width() / 2
            ly = cy - math.sin(tick_angle) * (radius - 28) - lbl.get_height() / 2
            self.surface.blit(lbl, (lx, ly))

        # "2 MIN TURN" annotation
        label_2min = self.small_font.render("2 MIN TURN", True, (160, 160, 160))
        self.surface.blit(
            label_2min,
            label_2min.get_rect(center=(int(cx), int(cy) + radius - 22)),
        )

        # Miniature airplane — bank angle is 1.5× roll (standard-rate at ~18°)
        tc_bank = max(-35.0, min(35.0, -self.roll_deg * 1.5))
        airplane_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ac_cx = int(self.width / 2)
        ac_cy = int(self.height / 2) - 4

        # Fuselage (thicker nose-to-tail line)
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx - 5, ac_cy), (ac_cx + 5, ac_cy), 2)

        # Wings with notch (more airplane-like shape)
        wing_half = 32
        # Outer wing segments
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx - wing_half, ac_cy + 4), (ac_cx - 8, ac_cy), 3)
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx + 8, ac_cy), (ac_cx + wing_half, ac_cy + 4), 3)
        # Wing root fill
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx - 8, ac_cy), (ac_cx + 8, ac_cy), 3)
        # Tail
        tail_half = 12
        pygame.draw.line(airplane_surf, (255, 255, 255),
                         (ac_cx - tail_half, ac_cy - 9),
                         (ac_cx + tail_half, ac_cy - 9), 2)
        # Fuselage centre dot
        pygame.draw.circle(airplane_surf, (255, 255, 255), (ac_cx, ac_cy), 3)

        rotated = self._rotate_surface(airplane_surf, tc_bank)
        self.surface.blit(rotated, rotated.get_rect(center=(int(cx), int(cy))))

        # Reference centre tick (yellow) at top of arc
        pygame.draw.polygon(
            self.surface, (255, 200, 0),
            [(int(cx), int(cy) - radius + 2),
             (int(cx) - 4, int(cy) - radius + 12),
             (int(cx) + 4, int(cy) - radius + 12)],
        )

        # Inclinometer (ball) strip at bottom
        strip_y = int(self.height - 20)
        strip_rect = pygame.Rect(int(cx) - 32, strip_y - 10, 64, 20)
        pygame.draw.rect(self.surface, (18, 18, 18), strip_rect, border_radius=10)
        pygame.draw.rect(self.surface, (90, 90, 90), strip_rect, 1, border_radius=10)
        # Centre index lines
        for dx in (-16, 0, 16):
            pygame.draw.line(
                self.surface, (80, 80, 80),
                (int(cx) + dx, strip_y - 8),
                (int(cx) + dx, strip_y + 8), 1,
            )
        # Ball (centred — realistic lateral-accel not modelled)
        ball_x = int(cx)
        pygame.draw.circle(self.surface, (30, 30, 30), (ball_x, strip_y), 8)
        pygame.draw.circle(self.surface, (140, 140, 140), (ball_x, strip_y), 8, 1)
        # Ball highlight
        pygame.draw.circle(self.surface, (80, 80, 80), (ball_x - 2, strip_y - 2), 3)

        return self.surface

