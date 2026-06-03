from __future__ import annotations

import math
import pygame

from ..instruments.airspeed_indicator import AirspeedIndicator
from ..instruments.altimeter import Altimeter
from ..instruments.attitude_indicator import AttitudeIndicator
from ..instruments.engine_instruments import EngineInstruments
from ..instruments.heading_indicator import HeadingIndicator
from ..instruments.nav_display import NavDisplay
from ..instruments.tachometer import Tachometer
from ..instruments.turn_coordinator import TurnCoordinator
from ..instruments.vsi import VSI

# ── Layout constants (1280 × 720) ──────────────────────────────────────────
_WINDSHIELD_H = 262        # pixel height of outside-view area
_GLARESHIELD_H = 28        # dark bar below windshield
_PANEL_TOP = _WINDSHIELD_H + _GLARESHIELD_H   # y=290

_INST_SIZE = 150           # square instrument diameter (px)
_ROW1_Y = _PANEL_TOP + 5   # top edge of first instrument row
_ROW2_Y = _ROW1_Y + _INST_SIZE + 12  # second row

_COL_ASI = 45
_COL_AI = 210
_COL_ALT = 375
_COL_TC = 45
_COL_DI = 210
_COL_VSI = 375

_TACH_X = 545
_TACH_Y = _ROW1_Y
_ENGINE_X = 545
_ENGINE_Y = _ROW2_Y
_ENGINE_W = 185
_ENGINE_H = 162

_RADIO_X = 740
_RADIO_Y = _PANEL_TOP
_RADIO_W = 175
_RADIO_H = _ENGINE_Y + _ENGINE_H - _PANEL_TOP

_NAV_X = 930
_NAV_Y = _ROW1_Y
_NAV_W = 310
_NAV_H = 210

_CESSNA_GRAY = (68, 68, 68)
_BEZEL_COLOR = (38, 38, 38)
_GLARESHIELD_COLOR = (22, 22, 22)
_PILLAR_COLOR = (30, 30, 30)
_LABEL_COLOR = (175, 175, 175)


class CockpitView:
    """Full Cessna 152 front cockpit view with windshield and instrument panel."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.width = screen_width
        self.height = screen_height
        self.label_font = pygame.font.SysFont("arial", 11)
        self.info_font = pygame.font.SysFont("arial", 13)
        self.radio_font = pygame.font.SysFont("courier", 12)

        # ── Six-pack + tachometer + TC ──────────────────────────────────
        self.airspeed = AirspeedIndicator(_INST_SIZE, _INST_SIZE)
        self.attitude = AttitudeIndicator(_INST_SIZE, _INST_SIZE)
        self.altimeter = Altimeter(_INST_SIZE, _INST_SIZE)
        self.turn_coord = TurnCoordinator(_INST_SIZE, _INST_SIZE)
        self.heading = HeadingIndicator(_INST_SIZE, _INST_SIZE)
        self.vsi = VSI(_INST_SIZE, _INST_SIZE)
        self.tachometer = Tachometer(_INST_SIZE, _INST_SIZE)
        self.engine = EngineInstruments(_ENGINE_W, _ENGINE_H)
        self.nav_display = NavDisplay(_NAV_W, _NAV_H)

        self._six_pack: list[tuple[object, int, int, str]] = [
            (self.airspeed,   _COL_ASI, _ROW1_Y, "AIRSPEED"),
            (self.attitude,   _COL_AI,  _ROW1_Y, "ATTITUDE"),
            (self.altimeter,  _COL_ALT, _ROW1_Y, "ALTIMETER"),
            (self.turn_coord, _COL_TC,  _ROW2_Y, "TURN COORD"),
            (self.heading,    _COL_DI,  _ROW2_Y, "HEADING"),
            (self.vsi,        _COL_VSI, _ROW2_Y, "VERT SPEED"),
        ]

        self.atc_messages: list[str] = []
        self.checklist_status = "Checklist idle"
        self._pitch_deg = 0.0
        self._roll_deg = 0.0

    # ── Public API ─────────────────────────────────────────────────────────

    def update(self, state: dict) -> None:
        self._pitch_deg = float(state.get("pitch_deg", 0.0))
        self._roll_deg = float(state.get("roll_deg", 0.0))
        for inst, *_ in self._six_pack:
            inst.update(state)  # type: ignore[attr-defined]
        self.tachometer.update(state)
        self.engine.update(state)
        self.nav_display.update(state)
        self.atc_messages = [
            m.text if hasattr(m, "text") else str(m)
            for m in state.get("atc_messages", [])
        ][-3:]
        self.checklist_status = state.get("checklist_status", self.checklist_status)

    def draw(self, screen: pygame.Surface) -> None:
        self._draw_windshield(screen)
        self._draw_glareshield(screen)
        self._draw_panel_background(screen)
        self._draw_panel_details(screen)

        # Blit six-pack
        for inst, x, y, label in self._six_pack:
            surf = inst.draw()  # type: ignore[attr-defined]
            screen.blit(surf, (x, y))
            lbl = self.label_font.render(label, True, _LABEL_COLOR)
            screen.blit(lbl, (x + _INST_SIZE // 2 - lbl.get_width() // 2,
                               y + _INST_SIZE + 2))

        # Tachometer
        screen.blit(self.tachometer.draw(), (_TACH_X, _TACH_Y))
        tach_lbl = self.label_font.render("TACHOMETER", True, _LABEL_COLOR)
        screen.blit(tach_lbl,
                    (_TACH_X + _INST_SIZE // 2 - tach_lbl.get_width() // 2,
                     _TACH_Y + _INST_SIZE + 2))

        # Engine instruments sub-panel
        screen.blit(self.engine.draw(), (_ENGINE_X, _ENGINE_Y))

        # Radio stack (decorative)
        self._draw_radio_stack(screen)

        # Nav display
        screen.blit(self.nav_display.draw(), (_NAV_X, _NAV_Y))

        # ATC messages + checklist strip
        self._draw_info_strip(screen)

        # Yoke
        self._draw_yoke(screen)

    # ── Private drawing helpers ────────────────────────────────────────────

    def _draw_windshield(self, screen: pygame.Surface) -> None:
        W, H = self.width, _WINDSHIELD_H
        # Sky gradient (bottom row of sky = horizon colour)
        sky_top = (20, 40, 100)
        sky_horizon = (130, 185, 230)
        sky_surf = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            r = int(sky_top[0] + t * (sky_horizon[0] - sky_top[0]))
            g = int(sky_top[1] + t * (sky_horizon[1] - sky_top[1]))
            b = int(sky_top[2] + t * (sky_horizon[2] - sky_top[2]))
            pygame.draw.line(sky_surf, (r, g, b), (0, y), (W, y))
        screen.blit(sky_surf, (0, 0))

        # Tilted horizon line
        cx, cy_base = W // 2, _WINDSHIELD_H // 2
        # Positive pitch → nose up → horizon moves down
        horizon_cy = cy_base + self._pitch_deg * 7.5
        roll_rad = math.radians(self._roll_deg)
        hl_x, hl_y = 0, horizon_cy - cx * math.tan(roll_rad)
        hr_x, hr_y = W, horizon_cy + (W - cx) * math.tan(roll_rad)

        # Ground polygon (brown, fills below horizon line)
        ground_color = (110, 80, 45)
        ground_pts = [(hl_x, hl_y), (hr_x, hr_y), (W, H), (0, H)]
        pygame.draw.polygon(screen, ground_color, ground_pts)

        # Perspective grid on ground (converge to horizon vanishing point)
        vp = (cx, int(horizon_cy))
        ground_line_color = (90, 64, 30)
        for gx in range(0, W + 1, 80):
            pygame.draw.line(screen, ground_line_color, vp, (gx, H), 1)
        for yy in range(int(max(hl_y, hr_y)), H, 40):
            pygame.draw.line(screen, ground_line_color, (0, yy), (W, yy), 1)

        # Horizon line
        pygame.draw.line(screen, (230, 220, 190), (int(hl_x), int(hl_y)), (int(hr_x), int(hr_y)), 2)

        # Haze layer at horizon
        haze_h = 18
        haze_y = int(min(hl_y, hr_y)) - haze_h // 2
        haze_surf = pygame.Surface((W, haze_h), pygame.SRCALPHA)
        for yy in range(haze_h):
            alpha = int(80 * (1 - abs(yy / haze_h - 0.5) * 2))
            pygame.draw.line(haze_surf, (210, 230, 255, alpha), (0, yy), (W, yy))
        screen.blit(haze_surf, (0, max(0, haze_y)))

        # A-pillars (dark trapezoids on each side)
        pillar_w_top = 40
        pillar_w_bot = 60
        # Left pillar
        pygame.draw.polygon(screen, _PILLAR_COLOR, [
            (0, 0), (pillar_w_top, 0),
            (pillar_w_bot, H), (0, H),
        ])
        # Right pillar
        pygame.draw.polygon(screen, _PILLAR_COLOR, [
            (W - pillar_w_top, 0), (W, 0),
            (W, H), (W - pillar_w_bot, H),
        ])
        # Top frame
        pygame.draw.rect(screen, _PILLAR_COLOR, pygame.Rect(0, 0, W, 14))
        # Bottom windshield frame
        pygame.draw.rect(screen, _PILLAR_COLOR, pygame.Rect(0, H - 6, W, 6))

    def _draw_glareshield(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen, _GLARESHIELD_COLOR,
            pygame.Rect(0, _WINDSHIELD_H, self.width, _GLARESHIELD_H),
        )

    def _draw_panel_background(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen, _CESSNA_GRAY,
            pygame.Rect(0, _PANEL_TOP, self.width, self.height - _PANEL_TOP),
        )

    def _draw_panel_details(self, screen: pygame.Surface) -> None:
        """Recessed bezel areas for the instrument clusters."""
        # Six-pack recess
        recess_margin = 6
        r1 = pygame.Rect(
            _COL_ASI - recess_margin,
            _ROW1_Y - recess_margin,
            (_COL_ALT - _COL_ASI) + _INST_SIZE + recess_margin * 2,
            (_ROW2_Y - _ROW1_Y) + _INST_SIZE + recess_margin * 2,
        )
        pygame.draw.rect(screen, _BEZEL_COLOR, r1, border_radius=6)
        pygame.draw.rect(screen, (25, 25, 25), r1, 2, border_radius=6)

        # Tachometer bezel
        tach_r = pygame.Rect(
            _TACH_X - recess_margin, _TACH_Y - recess_margin,
            _INST_SIZE + recess_margin * 2, _INST_SIZE + recess_margin * 2,
        )
        pygame.draw.rect(screen, _BEZEL_COLOR, tach_r, border_radius=6)
        pygame.draw.rect(screen, (25, 25, 25), tach_r, 2, border_radius=6)

        # Engine panel recess
        eng_r = pygame.Rect(
            _ENGINE_X - recess_margin, _ENGINE_Y - recess_margin,
            _ENGINE_W + recess_margin * 2, _ENGINE_H + recess_margin * 2,
        )
        pygame.draw.rect(screen, _BEZEL_COLOR, eng_r, border_radius=6)
        pygame.draw.rect(screen, (25, 25, 25), eng_r, 2, border_radius=6)

        # Nav display recess
        nav_r = pygame.Rect(
            _NAV_X - recess_margin, _NAV_Y - recess_margin,
            _NAV_W + recess_margin * 2, _NAV_H + recess_margin * 2 + 18,
        )
        pygame.draw.rect(screen, _BEZEL_COLOR, nav_r, border_radius=6)
        pygame.draw.rect(screen, (25, 25, 25), nav_r, 2, border_radius=6)

    def _draw_radio_stack(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (20, 20, 20),
                         pygame.Rect(_RADIO_X, _RADIO_Y, _RADIO_W, _RADIO_H),
                         border_radius=4)
        pygame.draw.rect(screen, (55, 55, 55),
                         pygame.Rect(_RADIO_X, _RADIO_Y, _RADIO_W, _RADIO_H),
                         1, border_radius=4)
        labels = [
            ("COM1", "122.800", (0, 185, 255)),
            ("NAV1", "110.30",  (100, 230, 100)),
            ("XPDR", "1200",    (230, 200, 100)),
            ("ADF",  "400.0",   (220, 180, 220)),
        ]
        item_h = _RADIO_H // len(labels)
        for i, (name, freq, color) in enumerate(labels):
            y = _RADIO_Y + i * item_h
            pygame.draw.rect(screen, (28, 28, 28),
                             pygame.Rect(_RADIO_X + 4, y + 4, _RADIO_W - 8, item_h - 8),
                             border_radius=3)
            name_s = self.radio_font.render(name, True, (180, 180, 180))
            freq_s = self.radio_font.render(freq, True, color)
            screen.blit(name_s, (_RADIO_X + 8, y + 6))
            screen.blit(freq_s, (_RADIO_X + 8, y + item_h // 2))
            pygame.draw.line(screen, (50, 50, 50),
                             (_RADIO_X + 4, y + item_h - 4),
                             (_RADIO_X + _RADIO_W - 4, y + item_h - 4), 1)

        label = self.label_font.render("RADIO STACK", True, _LABEL_COLOR)
        screen.blit(label, (_RADIO_X + _RADIO_W // 2 - label.get_width() // 2,
                             _RADIO_Y + _RADIO_H + 2))

    def _draw_yoke(self, screen: pygame.Surface) -> None:
        """Simple yoke shape at the bottom centre of the cockpit panel."""
        cx, cy = self.width // 4, self.height - 26
        yoke_color = (35, 35, 35)
        # Column (vertical rod)
        pygame.draw.rect(screen, yoke_color, pygame.Rect(cx - 7, cy - 30, 14, 32), border_radius=4)
        # Horizontal bar
        pygame.draw.rect(screen, yoke_color, pygame.Rect(cx - 48, cy - 30, 96, 12), border_radius=6)
        # Left grip
        pygame.draw.ellipse(screen, yoke_color, pygame.Rect(cx - 62, cy - 50, 22, 38))
        # Right grip
        pygame.draw.ellipse(screen, yoke_color, pygame.Rect(cx + 40, cy - 50, 22, 38))
        # Horn button (red)
        pygame.draw.circle(screen, (170, 30, 30), (cx - 51, cy - 32), 5)

    def _draw_info_strip(self, screen: pygame.Surface) -> None:
        strip_y = self.height - 18
        pygame.draw.rect(screen, (16, 16, 16),
                         pygame.Rect(0, strip_y, self.width, 18))
        for idx, msg in enumerate(self.atc_messages):
            t = self.info_font.render(msg, True, (160, 200, 255))
            screen.blit(t, (8 + idx * (self.width // 3), strip_y + 2))
        ck = self.info_font.render(self.checklist_status, True, (245, 210, 110))
        screen.blit(ck, (self.width - ck.get_width() - 8, strip_y + 2))

