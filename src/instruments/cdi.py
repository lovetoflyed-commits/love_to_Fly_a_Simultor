from __future__ import annotations

import math

import pygame

from .base_instrument import Instrument


class CDI(Instrument):
    """Course Deviation Indicator — shows ILS localizer and glideslope deviation.

    Localizer: horizontal needle, full-scale = ±1.0 (±2.5 degrees off course).
    Glideslope: vertical needle, full-scale = ±1.0 (±0.7 degrees off path).
    """

    _NEEDLE_COLOR = (255, 220, 0)
    _SCALE_COLOR = (220, 220, 220)
    _FLAG_COLOR = (255, 60, 60)
    _VALID_COLOR = (60, 200, 60)
    _BG_COLOR = (26, 26, 26)

    def __init__(self, width: int = 310, height: int = 80) -> None:
        super().__init__(width, height)
        self.loc_deviation = 0.0   # -1.0 (full fly-right) to +1.0 (full fly-left)
        self.gs_deviation = 0.0    # -1.0 (fly-down) to +1.0 (fly-up)
        self.loc_valid = False
        self.gs_valid = False
        self.course_deg = 100.0
        self.nav1_mhz = 110.3
        self.avionics_powered = True

    def update(self, state: dict) -> None:
        self.loc_deviation = float(state.get("loc_deviation", 0.0))
        self.gs_deviation = float(state.get("gs_deviation", 0.0))
        self.loc_valid = bool(state.get("loc_valid", False))
        self.gs_valid = bool(state.get("gs_valid", False))
        self.course_deg = float(state.get("ils_course_deg", 100.0))
        self.nav1_mhz = float(state.get("nav1_mhz", 110.3))
        self.avionics_powered = bool(state.get("avionics_powered", True))

    def draw(self) -> pygame.Surface:
        self.surface.fill(self._BG_COLOR)
        pygame.draw.rect(self.surface, (50, 50, 50), self.surface.get_rect(), 2)

        if not self.avionics_powered:
            off = self.small_font.render("CDI OFF", True, (120, 120, 120))
            self.surface.blit(off, off.get_rect(center=(self.width // 2, self.height // 2)))
            return self.surface

        # ── Layout ────────────────────────────────────────────────────────────
        # Left section: course arrow + LOC scale (width*0.55)
        # Right section: GS scale (remaining width)
        loc_w = int(self.width * 0.60)
        gs_x0 = loc_w + 8
        cy = self.height // 2

        # ── Course label ──────────────────────────────────────────────────────
        course_lbl = self.small_font.render(
            f"CRS {self.course_deg:03.0f}°  NAV1 {self.nav1_mhz:.2f}", True, (200, 200, 200)
        )
        self.surface.blit(course_lbl, (6, 4))

        # ── LOC scale (5 dots, centre + ±1 + ±2 notches) ─────────────────────
        loc_cx = loc_w // 2
        loc_scale_px = int(loc_w * 0.35)  # half-scale in pixels
        dot_radius = 4
        for offset in (-2, -1, 0, 1, 2):
            dot_x = loc_cx + offset * (loc_scale_px // 2)
            pygame.draw.circle(self.surface, self._SCALE_COLOR, (dot_x, cy), dot_radius, 1)

        # LOC centre cross
        pygame.draw.line(self.surface, self._SCALE_COLOR, (loc_cx, cy - 14), (loc_cx, cy + 14), 1)

        if self.loc_valid:
            # LOC deviation needle (vertical bar)
            needle_x = int(loc_cx + self.loc_deviation * loc_scale_px)
            needle_x = max(loc_cx - loc_scale_px, min(loc_cx + loc_scale_px, needle_x))
            pygame.draw.line(self.surface, self._NEEDLE_COLOR, (needle_x, cy - 18), (needle_x, cy + 18), 4)
            flag_surf = self.small_font.render("LOC", True, self._VALID_COLOR)
        else:
            flag_surf = self.small_font.render("LOC", True, self._FLAG_COLOR)

        self.surface.blit(flag_surf, (6, self.height - flag_surf.get_height() - 4))

        # ── GS scale (vertical strip on right) ───────────────────────────────
        gs_scale_px = int(self.height * 0.30)
        for offset in (-1, 0, 1):
            dot_y = cy + offset * gs_scale_px
            pygame.draw.circle(
                self.surface, self._SCALE_COLOR, (gs_x0 + 14, dot_y), dot_radius, 1
            )
        pygame.draw.line(
            self.surface, self._SCALE_COLOR,
            (gs_x0 + 2, cy), (gs_x0 + 26, cy), 1
        )

        if self.gs_valid:
            needle_y = int(cy - self.gs_deviation * gs_scale_px)
            needle_y = max(cy - gs_scale_px, min(cy + gs_scale_px, needle_y))
            pygame.draw.line(
                self.surface, self._NEEDLE_COLOR,
                (gs_x0 + 2, needle_y), (gs_x0 + 26, needle_y), 4
            )
            gs_flag = self.small_font.render("GS", True, self._VALID_COLOR)
        else:
            gs_flag = self.small_font.render("GS", True, self._FLAG_COLOR)

        self.surface.blit(gs_flag, (gs_x0 + 2, self.height - gs_flag.get_height() - 4))

        # ── Deviation readout ─────────────────────────────────────────────────
        dev_text = ""
        if self.loc_valid:
            side = "R" if self.loc_deviation < 0 else "L"
            dev_text += f"LOC {abs(self.loc_deviation):.2f}{side}  "
        if self.gs_valid:
            side = "U" if self.gs_deviation > 0 else "D"
            dev_text += f"GS {abs(self.gs_deviation):.2f}{side}"
        if dev_text:
            dev_s = self.small_font.render(dev_text.strip(), True, (180, 220, 255))
            self.surface.blit(dev_s, (loc_w // 2 - dev_s.get_width() // 2, self.height - dev_s.get_height() - 4))

        return self.surface


class StallWarning:
    """Simple visual stall warning strip rendered onto any surface."""

    def __init__(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self._font = pygame.font.SysFont("arial", 20, bold=True)
        self._phase = 0.0

    def update(self, dt: float, is_stalling: bool) -> None:
        if is_stalling:
            self._phase = (self._phase + dt * 4.0) % (2 * math.pi)
        else:
            self._phase = 0.0

    def draw(self, surface: pygame.Surface, is_stalling: bool) -> None:
        if not is_stalling:
            return
        alpha = int(180 + 75 * math.sin(self._phase))
        w, h = surface.get_width(), 36
        y = 50
        warning_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        warning_surf.fill((200, 0, 0, alpha))
        text = self._font.render("⚠  STALL  ⚠", True, (255, 255, 255))
        warning_surf.blit(text, text.get_rect(center=(w // 2, h // 2)))
        surface.blit(warning_surf, (0, y))
