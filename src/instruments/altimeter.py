from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class Altimeter(Instrument):
    """Three-pointer altimeter for the Cessna 152.

    Needles:
      Long   (hundreds)  – one full revolution per 1 000 ft
      Short  (thousands) – one full revolution per 10 000 ft
      Stub   (ten-thousands) – one full revolution per 100 000 ft
    Scale: 0–1 000 ft labelled 1–9 (×100) around the face; 270 ° sweep.
    """

    def __init__(self, width: int = 150, height: int = 150) -> None:
        super().__init__(width, height)
        self.altitude_ft = 0.0
        self.baro_inhg = 29.92

    def update(self, state: dict) -> None:
        self.altitude_ft = float(state.get("altitude_ft", 0.0))
        self.baro_inhg = float(state.get("baro_inhg", 29.92))

    # ------------------------------------------------------------------

    def _alt_to_angle(self, alt_mod: float, full_rev: float) -> float:
        """Convert altitude modulus to needle angle in radians.

        0 ft → 90° (12-o'clock), sweeping clockwise.
        """
        frac = (alt_mod % full_rev) / full_rev
        return math.radians(90.0 - frac * 360.0)

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        cx = self.width / 2
        cy = self.height / 2
        center = (cx, cy)
        radius = min(self.width, self.height) // 2 - 12

        # ── Tick marks ──────────────────────────────────────────────────
        for i in range(50):                     # every 20 ft on hundreds needle
            angle = math.radians(90 - i * (360 / 50))
            major = (i % 5 == 0)               # every 100 ft
            mid   = (i % 5 == 0 and i % 10 != 0)  # every 100 ft between majors
            inner_r = radius - (14 if major else 6)
            ox = cx + math.cos(angle) * radius
            oy = cy - math.sin(angle) * radius
            ix = cx + math.cos(angle) * inner_r
            iy = cy - math.sin(angle) * inner_r
            lw = 2 if major else 1
            pygame.draw.line(self.surface, (255, 255, 255), (ox, oy), (ix, iy), lw)

        # Labels 1–9 at the 100-ft marks
        for digit in range(1, 10):
            angle = math.radians(90 - digit * (360 / 10))
            lbl = self.small_font.render(str(digit), True, (230, 230, 230))
            lx = cx + math.cos(angle) * (radius - 24) - lbl.get_width() / 2
            ly = cy - math.sin(angle) * (radius - 24) - lbl.get_height() / 2
            self.surface.blit(lbl, (lx, ly))

        # ── Baro window (Kollsman window) — bottom of dial ───────────────
        baro_rect = pygame.Rect(int(cx) - 30, int(cy) + int(radius * 0.52), 60, 18)
        pygame.draw.rect(self.surface, (20, 20, 20), baro_rect, border_radius=3)
        pygame.draw.rect(self.surface, (80, 80, 120), baro_rect, 1, border_radius=3)
        baro_text = self.small_font.render(f"{self.baro_inhg:.2f}", True, (180, 220, 255))
        self.surface.blit(baro_text, baro_text.get_rect(center=baro_rect.center))

        # ── Triangle marker at 12-o'clock ───────────────────────────────
        tri_tip = (cx, cy - radius + 4)
        pygame.draw.polygon(
            self.surface, (255, 200, 0),
            [(cx - 5, cy - radius + 14), (cx + 5, cy - radius + 14), tri_tip],
        )

        alt = max(0.0, self.altitude_ft)

        # ── Ten-thousands needle (short stub, white) ─────────────────────
        ten_k_angle = self._alt_to_angle(alt, 100_000.0)
        self._draw_needle(
            self.surface, center, ten_k_angle,
            length=radius * 0.40, width=3,
            color=(230, 230, 230), tail_length=radius * 0.12,
        )

        # ── Thousands needle (medium, white) ─────────────────────────────
        thou_angle = self._alt_to_angle(alt, 10_000.0)
        self._draw_needle(
            self.surface, center, thou_angle,
            length=radius * 0.62, width=4,
            color=(230, 230, 230), tail_length=radius * 0.18,
        )

        # ── Hundreds needle (long, bright white) ─────────────────────────
        hund_angle = self._alt_to_angle(alt, 1_000.0)
        self._draw_needle(
            self.surface, center, hund_angle,
            length=radius * 0.82, width=3,
            color=(255, 255, 255), tail_length=radius * 0.22,
        )

        # Pivot cap
        self._draw_pivot_cap(self.surface, center, radius=6)

        return self.surface

