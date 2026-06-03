from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class Tachometer(Instrument):
    """RPM gauge for the Cessna 152 Lycoming O-235 piston engine.

    Green arc: 1700–2750 RPM (normal operating range).
    Red arc: 2750–3000 RPM (do-not-exceed).
    Scale: 270° sweep, 0 RPM at bottom-left, 3000 RPM at bottom-right.
    Tick labels show × 100 RPM (e.g. "5" = 500 RPM).
    """

    MAX_RPM = 3000
    REDLINE_RPM = 2750
    GREEN_START_RPM = 1700

    def __init__(self, width: int = 150, height: int = 150) -> None:
        super().__init__(width, height)
        self.rpm = 0.0

    def update(self, state: dict) -> None:
        self.rpm = float(state.get("rpm", 0.0))

    def _rpm_to_angle_deg(self, rpm: float) -> float:
        """Return needle angle in degrees (225 = bottom-left, sweeping CW to -45/315)."""
        ratio = max(0.0, min(float(self.MAX_RPM), rpm)) / float(self.MAX_RPM)
        return 225.0 - ratio * 270.0

    def _draw_arc_range(
        self,
        color: tuple[int, int, int],
        start_rpm: float,
        end_rpm: float,
        arc_radius: int,
        width: int = 6,
    ) -> None:
        rect = pygame.Rect(
            self.width / 2 - arc_radius,
            self.height / 2 - arc_radius,
            arc_radius * 2,
            arc_radius * 2,
        )
        a_start = math.radians(-self._rpm_to_angle_deg(start_rpm))
        a_end = math.radians(-self._rpm_to_angle_deg(end_rpm))
        pygame.draw.arc(self.surface, color, rect, a_start, a_end, width)

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        cx = self.width / 2
        cy = self.height / 2
        center = (cx, cy)
        radius = min(self.width, self.height) // 2 - 12

        # Coloured arcs
        self._draw_arc_range((0, 185, 75), self.GREEN_START_RPM, self.REDLINE_RPM, radius - 1, 7)
        self._draw_arc_range((215, 40, 40), self.REDLINE_RPM, self.MAX_RPM, radius - 1, 7)

        # Tick marks and labels (every 100 RPM, major every 500)
        for rpm in range(0, self.MAX_RPM + 1, 100):
            angle = math.radians(self._rpm_to_angle_deg(rpm))
            major = rpm % 500 == 0
            mid = rpm % 500 == 250
            inner_r = radius - (17 if major else (10 if mid else 6))
            ox = cx + math.cos(angle) * radius
            oy = cy - math.sin(angle) * radius
            ix = cx + math.cos(angle) * inner_r
            iy = cy - math.sin(angle) * inner_r
            lw = 2 if major else 1
            pygame.draw.line(self.surface, (255, 255, 255), (ox, oy), (ix, iy), lw)
            if major and rpm > 0:
                lbl = self.small_font.render(str(rpm // 100), True, (215, 215, 215))
                lx = cx + math.cos(angle) * (radius - 28) - lbl.get_width() / 2
                ly = cy - math.sin(angle) * (radius - 28) - lbl.get_height() / 2
                self.surface.blit(lbl, (lx, ly))

        # × 100 RPM label
        x100_lbl = self.small_font.render("× 100 RPM", True, (140, 140, 140))
        self.surface.blit(x100_lbl, x100_lbl.get_rect(center=(int(cx), int(cy) + 20)))

        # Needle
        angle = math.radians(self._rpm_to_angle_deg(self.rpm))
        self._draw_needle(
            self.surface, center, angle,
            length=radius - 13, width=4,
            color=(255, 255, 255), tail_length=radius * 0.20, tail_color=(80, 80, 80),
        )
        # Red tip on upper portion
        tip_len = radius - 13
        tip_x = cx + math.cos(angle) * tip_len
        tip_y = cy - math.sin(angle) * tip_len
        mid_x = cx + math.cos(angle) * (radius * 0.45)
        mid_y = cy - math.sin(angle) * (radius * 0.45)
        pygame.draw.line(self.surface, (220, 55, 55), (mid_x, mid_y), (tip_x, tip_y), 2)

        # Digital RPM readout
        digital = self.large_font.render(f"{int(self.rpm):4d}", True, (255, 255, 255))
        self.surface.blit(digital, digital.get_rect(center=(int(cx), int(cy) + 44)))

        self._draw_pivot_cap(self.surface, center, radius=6)
        return self.surface

