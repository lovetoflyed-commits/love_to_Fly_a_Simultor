from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class AirspeedIndicator(Instrument):
    """Airspeed indicator calibrated for the Cessna 152.

    Speed arcs (knots):
      White arc  40–85  kts  (Vso → Vfe  – flap operating range)
      Green arc  44–111 kts  (Vs  → Vno  – normal operating range)
      Yellow arc 111–149 kts (Vno → Vne  – caution range)
      Red radial     149 kts  (Vne – never exceed)
    Scale: 0–160 kts, 270 ° sweep.
    """

    MAX_SPEED = 160.0

    def __init__(self, width: int = 150, height: int = 150) -> None:
        super().__init__(width, height)
        self.airspeed_kts = 0.0

    def update(self, state: dict) -> None:
        self.airspeed_kts = float(state.get("airspeed_kts", 0.0))

    def _value_to_angle(self, value: float) -> float:
        """Map knots to a display angle in degrees (225 = 0 kts, sweeping CW)."""
        return 225.0 - (max(0.0, min(self.MAX_SPEED, value)) / self.MAX_SPEED) * 270.0

    def _draw_arc(
        self,
        color: tuple[int, int, int],
        start_kts: float,
        end_kts: float,
        arc_radius: int,
        width: int = 6,
    ) -> None:
        rect = pygame.Rect(
            self.width / 2 - arc_radius,
            self.height / 2 - arc_radius,
            arc_radius * 2,
            arc_radius * 2,
        )
        pygame.draw.arc(
            self.surface,
            color,
            rect,
            math.radians(-self._value_to_angle(start_kts)),
            math.radians(-self._value_to_angle(end_kts)),
            width,
        )

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        center = pygame.Vector2(self.width / 2, self.height / 2)
        radius = min(self.width, self.height) // 2 - 12

        # Coloured speed arcs
        self._draw_arc((220, 220, 220), 40, 85, radius, 6)       # white – flap range
        self._draw_arc((0, 175, 65), 44, 111, radius - 7, 6)     # green – normal
        self._draw_arc((215, 195, 30), 111, 149, radius - 14, 5) # yellow – caution

        # Red Vne radial at 149 kts
        vne_angle = math.radians(self._value_to_angle(149.0))
        vne_outer = (
            center.x + math.cos(vne_angle) * radius,
            center.y - math.sin(vne_angle) * radius,
        )
        vne_inner = (
            center.x + math.cos(vne_angle) * (radius - 16),
            center.y - math.sin(vne_angle) * (radius - 16),
        )
        pygame.draw.line(self.surface, (215, 40, 40), vne_inner, vne_outer, 4)

        # Tick marks every 10 kts; labels every 20 kts
        for speed in range(0, int(self.MAX_SPEED) + 1, 10):
            angle = math.radians(self._value_to_angle(speed))
            major = speed % 20 == 0
            inner_r = radius - (15 if major else 7)
            ox = center.x + math.cos(angle) * radius
            oy = center.y - math.sin(angle) * radius
            ix = center.x + math.cos(angle) * inner_r
            iy = center.y - math.sin(angle) * inner_r
            pygame.draw.line(self.surface, (255, 255, 255), (ox, oy), (ix, iy), 2 if major else 1)
            if major and speed > 0:
                lbl = self.small_font.render(str(speed), True, (225, 225, 225))
                lx = center.x + math.cos(angle) * (radius - 28) - lbl.get_width() / 2
                ly = center.y - math.sin(angle) * (radius - 28) - lbl.get_height() / 2
                self.surface.blit(lbl, (lx, ly))

        # Needle
        angle = math.radians(self._value_to_angle(self.airspeed_kts))
        tip = (
            center.x + math.cos(angle) * (radius - 16),
            center.y - math.sin(angle) * (radius - 16),
        )
        pygame.draw.line(self.surface, (255, 80, 80), center, tip, 3)
        pygame.draw.circle(self.surface, (255, 80, 80), center, 5)

        # Digital readout
        digital = self.large_font.render(f"{self.airspeed_kts:03.0f}", True, (255, 255, 255))
        self.surface.blit(digital, digital.get_rect(center=(center.x, center.y + 42)))
        kts_lbl = self.small_font.render("KIAS", True, (175, 175, 175))
        self.surface.blit(kts_lbl, kts_lbl.get_rect(center=(center.x, center.y + 58)))

        return self.surface

