from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class VSI(Instrument):
    """Vertical Speed Indicator for the Cessna 152.

    Scale: ±2 000 fpm, non-linear (compressed toward ±2 000).
    Tick marks every 100 fpm (minor) and 500 fpm (major).
    """

    MAX_FPM = 2000.0

    def __init__(self, width: int = 150, height: int = 150) -> None:
        super().__init__(width, height)
        self.vertical_speed_fpm = 0.0

    def update(self, state: dict) -> None:
        self.vertical_speed_fpm = float(state.get("vertical_speed_fpm", 0.0))

    def _fpm_to_angle(self, fpm: float) -> float:
        """Map fpm to display angle in radians.

        0 fpm → 0° (9-o'clock / left), +2000 → +90° (12-o'clock), -2000 → -90°.
        """
        clamped = max(-self.MAX_FPM, min(self.MAX_FPM, fpm))
        # Slightly non-linear: sqrt compression for outer range feel
        ratio = clamped / self.MAX_FPM
        return math.radians(ratio * 90.0)

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        cx = self.width / 2
        cy = self.height / 2
        center = (cx, cy)
        radius = min(self.width, self.height) // 2 - 12

        # ── Tick marks ──────────────────────────────────────────────────
        tick_values = [
            -2000, -1500, -1000, -500, -400, -300, -200, -100,
            0,
            100, 200, 300, 400, 500, 1000, 1500, 2000,
        ]
        for fpm in tick_values:
            angle = self._fpm_to_angle(fpm)
            major = abs(fpm) % 500 == 0
            inner_r = radius - (16 if major else 8)
            ox = cx + math.cos(angle) * radius
            oy = cy - math.sin(angle) * radius
            ix = cx + math.cos(angle) * inner_r
            iy = cy - math.sin(angle) * inner_r
            lw = 2 if major else 1
            pygame.draw.line(self.surface, (255, 255, 255), (ox, oy), (ix, iy), lw)

            if major and fpm != 0:
                val = abs(fpm) // 100
                lbl = self.small_font.render(str(val), True, (220, 220, 220))
                lx = cx + math.cos(angle) * (radius - 28) - lbl.get_width() / 2
                ly = cy - math.sin(angle) * (radius - 28) - lbl.get_height() / 2
                self.surface.blit(lbl, (lx, ly))

        # ── UP / DOWN labels ─────────────────────────────────────────────
        up_lbl = self.small_font.render("UP", True, (180, 220, 180))
        dn_lbl = self.small_font.render("DN", True, (220, 180, 180))
        self.surface.blit(up_lbl, up_lbl.get_rect(center=(int(cx), int(cy) - int(radius * 0.52))))
        self.surface.blit(dn_lbl, dn_lbl.get_rect(center=(int(cx), int(cy) + int(radius * 0.52))))

        # ── FPM×100 annotation ────────────────────────────────────────────
        unit_lbl = self.small_font.render("FPM ×100", True, (150, 150, 150))
        self.surface.blit(unit_lbl, unit_lbl.get_rect(center=(int(cx), int(cy) + 32)))

        # ── Needle (green above zero, red below) ─────────────────────────
        clamped = max(-self.MAX_FPM, min(self.MAX_FPM, self.vertical_speed_fpm))
        angle = self._fpm_to_angle(clamped)
        needle_color = (100, 220, 100) if clamped >= 0 else (220, 100, 100)
        self._draw_needle(
            self.surface, center, angle,
            length=radius - 14, width=3,
            color=needle_color, tail_length=radius * 0.18, tail_color=(180, 180, 180),
        )

        # Digital readout
        digital = self.font.render(f"{self.vertical_speed_fpm:+.0f}", True, (240, 240, 240))
        self.surface.blit(digital, digital.get_rect(center=(int(cx), int(cy) + 46)))

        self._draw_pivot_cap(self.surface, center, radius=5)
        return self.surface

