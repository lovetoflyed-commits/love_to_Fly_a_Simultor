from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class Tachometer(Instrument):
    """RPM gauge for the Cessna 152 Lycoming O-235 piston engine.

    Green arc: 1700–2750 RPM (normal operating range).
    Red arc: 2750–3000 RPM (do-not-exceed).
    Scale: 270° sweep, 0 RPM at bottom-left, 3000 RPM at bottom-right.
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
        center = pygame.Vector2(self.width / 2, self.height / 2)
        radius = min(self.width, self.height) // 2 - 12

        # Coloured arcs
        self._draw_arc_range((0, 175, 65), self.GREEN_START_RPM, self.REDLINE_RPM, radius - 1, 6)
        self._draw_arc_range((215, 40, 40), self.REDLINE_RPM, self.MAX_RPM, radius - 1, 6)

        # Tick marks and labels
        for rpm in range(0, self.MAX_RPM + 1, 100):
            angle = math.radians(self._rpm_to_angle_deg(rpm))
            major = rpm % 500 == 0
            inner_r = radius - (16 if major else 7)
            ox = center.x + math.cos(angle) * radius
            oy = center.y - math.sin(angle) * radius
            ix = center.x + math.cos(angle) * inner_r
            iy = center.y - math.sin(angle) * inner_r
            pygame.draw.line(self.surface, (255, 255, 255), (ox, oy), (ix, iy), 2 if major else 1)
            if major and rpm > 0:
                lbl = self.small_font.render(str(rpm // 100), True, (215, 215, 215))
                lx = center.x + math.cos(angle) * (radius - 28) - lbl.get_width() / 2
                ly = center.y - math.sin(angle) * (radius - 28) - lbl.get_height() / 2
                self.surface.blit(lbl, (lx, ly))

        # Needle
        angle = math.radians(self._rpm_to_angle_deg(self.rpm))
        tip = (
            center.x + math.cos(angle) * (radius - 15),
            center.y - math.sin(angle) * (radius - 15),
        )
        pygame.draw.line(self.surface, (255, 80, 80), center, tip, 3)
        pygame.draw.circle(self.surface, (255, 80, 80), center, 5)

        # Centre label — ticks are labelled ×100 (e.g. "5" means 500 RPM)
        unit_lbl = self.small_font.render("RPM", True, (175, 175, 175))
        self.surface.blit(unit_lbl, unit_lbl.get_rect(center=(center.x, center.y + 30)))
        digital = self.large_font.render(f"{int(self.rpm):4d}", True, (255, 255, 255))
        self.surface.blit(digital, digital.get_rect(center=(center.x, center.y + 48)))

        return self.surface
