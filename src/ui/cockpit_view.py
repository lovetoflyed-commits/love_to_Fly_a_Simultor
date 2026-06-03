from __future__ import annotations

import math
import pygame

from ..instruments.airspeed_indicator import AirspeedIndicator
from ..instruments.altimeter import Altimeter
from ..instruments.attitude_indicator import AttitudeIndicator
from ..instruments.cdi import CDI, StallWarning
from ..instruments.engine_instruments import EngineInstruments
from ..instruments.heading_indicator import HeadingIndicator
from ..instruments.nav_display import NavDisplay
from ..instruments.tachometer import Tachometer
from ..instruments.turn_coordinator import TurnCoordinator
from ..instruments.vsi import VSI
from ..models.position import Position

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

_CDI_X = _NAV_X
_CDI_Y = _NAV_Y + _NAV_H + 20   # directly below nav display
_CDI_H = 80                       # height of CDI strip

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
        self.cdi = CDI(_NAV_W, _CDI_H)
        self.stall_warning = StallWarning()

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
        self._master_on = True
        self._avionics_on = True
        self._avionics_powered = True
        self._mixture_pct = 100.0
        self._carb_heat_on = False
        self._magneto_position = "BOTH"
        self._position = Position(0.0, 0.0, 0.0)
        self._heading_deg = 0.0
        self._altitude_ft = 0.0
        self._weather_ceiling_ft: int | None = None
        self._runways: list[dict] = []
        self._flaps_deg = 0.0
        self._stall = False
        self._debrief_text: str | None = None
        self._com1_mhz = 122.800
        self._nav1_mhz = 110.30
        self._squawk = 1200

    # ── Public API ─────────────────────────────────────────────────────────

    def update(self, state: dict) -> None:
        self._pitch_deg = float(state.get("pitch_deg", 0.0))
        self._roll_deg = float(state.get("roll_deg", 0.0))
        self._position = state.get("position", self._position)
        self._heading_deg = float(state.get("heading_deg", 0.0))
        self._altitude_ft = float(state.get("altitude_ft", 0.0))
        self._weather_ceiling_ft = state.get("weather_ceiling_ft", None)
        self._runways = state.get("nearby_runways", [])
        self._flaps_deg = float(state.get("flaps_deg", 0.0))
        self._stall = bool(state.get("stall_warning", False))
        self._debrief_text = state.get("debrief_text", None)
        for inst, *_ in self._six_pack:
            inst.update(state)  # type: ignore[attr-defined]
        self.tachometer.update(state)
        self.engine.update(state)
        self._avionics_powered = bool(state.get("avionics_powered", True))
        if self._avionics_powered:
            self.nav_display.update(state)
            self.cdi.update(state)
        else:
            self.nav_display.update(
                {
                    "position": state.get("position"),
                    "waypoints": [],
                    "active_leg": 0,
                    "bearing_to_next_deg": 0.0,
                    "distance_to_next_nm": 0.0,
                }
            )
            self.cdi.update({"avionics_powered": False})
        self._master_on = bool(state.get("master_on", True))
        self._avionics_on = bool(state.get("avionics_on", True))
        self._mixture_pct = float(state.get("mixture_pct", 100.0))
        self._carb_heat_on = bool(state.get("carb_heat_on", False))
        self._magneto_position = str(state.get("magneto_position", "BOTH")).upper()
        self._com1_mhz = float(state.get("com1_mhz", self._com1_mhz))
        self._nav1_mhz = float(state.get("nav1_mhz", self._nav1_mhz))
        self._squawk = int(state.get("squawk", self._squawk))
        self.atc_messages = [
            m.text if hasattr(m, "text") else str(m)
            for m in state.get("atc_messages", [])
        ][-3:]
        self.checklist_status = state.get("checklist_status", self.checklist_status)
        self.stall_warning.update(0.016, self._stall)

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

        # Radio stack (interactive)
        self._draw_radio_stack(screen)

        # Nav display
        screen.blit(self.nav_display.draw(), (_NAV_X, _NAV_Y))

        # CDI
        screen.blit(self.cdi.draw(), (_CDI_X, _CDI_Y))
        cdi_lbl = self.label_font.render("ILS CDI", True, _LABEL_COLOR)
        screen.blit(cdi_lbl, (_CDI_X + _NAV_W // 2 - cdi_lbl.get_width() // 2,
                               _CDI_Y + _CDI_H + 2))

        # ATC messages + checklist strip
        self._draw_info_strip(screen)

        # Yoke
        self._draw_yoke(screen)

        # Flap position indicator
        self._draw_flap_indicator(screen)

        # Stall warning overlay
        self.stall_warning.draw(screen, self._stall)

        # Debrief overlay
        if self._debrief_text:
            self._draw_debrief(screen)

    # ── Private drawing helpers ────────────────────────────────────────────

    def _draw_windshield(self, screen: pygame.Surface) -> None:
        W, H = self.width, _WINDSHIELD_H

        # ── Ground colour depends on rough terrain altitude ───────────────────
        alt_ft = self._altitude_ft
        if alt_ft < 500:
            ground_color = (35, 100, 35)        # low/green
        elif alt_ft < 2000:
            ground_color = (70, 95, 55)         # mid elevation
        elif alt_ft < 8000:
            ground_color = (100, 80, 60)        # brown upland
        else:
            ground_color = (130, 120, 110)      # high / rocky

        # ── Sky gradient ─────────────────────────────────────────────────────
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

        # ── Tilted horizon line ───────────────────────────────────────────────
        cx, cy_base = W // 2, _WINDSHIELD_H // 2
        horizon_cy = cy_base + self._pitch_deg * 7.5
        (hl_x, hl_y), (hr_x, hr_y) = self._horizon_line_endpoints(
            W, horizon_cy, self._roll_deg
        )

        # Ground polygon
        ground_pts = [(hl_x, hl_y), (hr_x, hr_y), (W, H), (0, H)]
        pygame.draw.polygon(screen, ground_color, ground_pts)

        # Perspective grid on ground
        vp = (cx, int(horizon_cy))
        ground_line_color = tuple(max(0, c - 20) for c in ground_color)
        for gx in range(0, W + 1, 80):
            pygame.draw.line(screen, ground_line_color, vp, (gx, H), 1)
        for yy in range(int(max(hl_y, hr_y)), H, 40):
            pygame.draw.line(screen, ground_line_color, (0, yy), (W, yy), 1)

        # ── Runway rendering ─────────────────────────────────────────────────
        for rwy in self._runways:
            self._draw_runway(screen, rwy, W, H, horizon_cy)

        # Horizon line
        pygame.draw.line(screen, (230, 220, 190), (int(hl_x), int(hl_y)), (int(hr_x), int(hr_y)), 2)

        # ── Cloud layer ──────────────────────────────────────────────────────
        if self._weather_ceiling_ft is not None:
            self._draw_cloud_layer(screen, W, H, horizon_cy)

        # Haze layer at horizon
        haze_h = 18
        haze_y = int(min(hl_y, hr_y)) - haze_h // 2
        haze_surf = pygame.Surface((W, haze_h), pygame.SRCALPHA)
        for yy in range(haze_h):
            alpha = int(80 * (1 - abs(yy / haze_h - 0.5) * 2))
            pygame.draw.line(haze_surf, (210, 230, 255, alpha), (0, yy), (W, yy))
        screen.blit(haze_surf, (0, max(0, haze_y)))

        # A-pillars
        pillar_w_top = 40
        pillar_w_bot = 60
        pygame.draw.polygon(screen, _PILLAR_COLOR, [
            (0, 0), (pillar_w_top, 0),
            (pillar_w_bot, H), (0, H),
        ])
        pygame.draw.polygon(screen, _PILLAR_COLOR, [
            (W - pillar_w_top, 0), (W, 0),
            (W, H), (W - pillar_w_bot, H),
        ])
        pygame.draw.rect(screen, _PILLAR_COLOR, pygame.Rect(0, 0, W, 14))
        pygame.draw.rect(screen, _PILLAR_COLOR, pygame.Rect(0, H - 6, W, 6))

    # ── Runway perspective helper ─────────────────────────────────────────────

    def _project_world_point(
        self,
        lat: float,
        lon: float,
        alt_ft: float,
        heading_rad: float,
        pitch_rad: float,
        roll_rad: float,
        screen_cx: float,
        horizon_cy: float,
        focal: float = 620.0,
    ) -> tuple[float, float] | None:
        """Project a world lat/lon/alt point onto the windshield screen coords.

        Returns (sx, sy) or None if the point is behind the aircraft.
        """
        # NED metres relative to aircraft
        lat0 = math.radians(self._position.latitude_deg)
        north_m = (lat - self._position.latitude_deg) * 111_320.0
        east_m = (lon - self._position.longitude_deg) * 111_320.0 * math.cos(lat0)
        up_m = (alt_ft - self._altitude_ft) * 0.3048   # up positive

        # Rotate into aircraft body frame (forward/right/up)
        # 1) yaw by -heading
        fwd = north_m * math.cos(heading_rad) + east_m * math.sin(heading_rad)
        right = -north_m * math.sin(heading_rad) + east_m * math.cos(heading_rad)
        up = up_m

        if fwd < 5.0:           # point is behind or very close
            return None

        # 2) pitch: positive pitch rotates nose up
        fwd2 = fwd * math.cos(pitch_rad) + up * math.sin(pitch_rad)
        up2 = -fwd * math.sin(pitch_rad) + up * math.cos(pitch_rad)
        if fwd2 < 1.0:
            return None

        # 3) roll: positive roll tilts right wing down
        right2 = right * math.cos(roll_rad) + up2 * math.sin(roll_rad)
        up3 = -right * math.sin(roll_rad) + up2 * math.cos(roll_rad)

        sx = screen_cx + (right2 / fwd2) * focal
        # up3 > 0 means above horizon → negative screen y offset
        sy = horizon_cy - (up3 / fwd2) * focal
        return sx, sy

    def _draw_runway(
        self,
        screen: pygame.Surface,
        rwy: dict,
        W: int,
        H: int,
        horizon_cy: float,
    ) -> None:
        """Draw a runway as a perspective-projected trapezoid."""
        heading_rad = math.radians(self._heading_deg)
        pitch_rad = math.radians(self._pitch_deg)
        roll_rad = math.radians(-self._roll_deg)   # screen y is flipped
        cx = W / 2

        rwy_hdg_rad = math.radians(float(rwy.get("heading_deg", 0)))
        t_lat = float(rwy.get("threshold_lat", 0.0))
        t_lon = float(rwy.get("threshold_lon", 0.0))
        length_ft = float(rwy.get("length_ft", 5000.0))
        elev_ft = float(rwy.get("elevation_ft", 0.0))
        half_width_ft = 75.0   # ~150 ft standard

        # Build 4 corners of the runway slab
        def offset(lat: float, lon: float, dist_ft: float, bearing_rad: float) -> tuple[float, float]:
            d_m = dist_ft * 0.3048
            d_lat = d_m * math.cos(bearing_rad) / 111_320.0
            d_lon = d_m * math.sin(bearing_rad) / (111_320.0 * math.cos(math.radians(lat)))
            return lat + d_lat, lon + d_lon

        perp = rwy_hdg_rad + math.pi / 2
        tl_lat, tl_lon = offset(t_lat, t_lon, half_width_ft, perp)
        tr_lat, tr_lon = offset(t_lat, t_lon, -half_width_ft, perp)
        far_lat, far_lon = offset(t_lat, t_lon, length_ft, rwy_hdg_rad)
        fl_lat, fl_lon = offset(far_lat, far_lon, half_width_ft, perp)
        fr_lat, fr_lon = offset(far_lat, far_lon, -half_width_ft, perp)

        corners_world = [
            (tl_lat, tl_lon),
            (tr_lat, tr_lon),
            (fr_lat, fr_lon),
            (fl_lat, fl_lon),
        ]
        pts = []
        for lat, lon in corners_world:
            p = self._project_world_point(lat, lon, elev_ft, heading_rad, pitch_rad, roll_rad, cx, horizon_cy)
            if p is None:
                return     # partial clip — skip for simplicity
            sx, sy = p
            if not (-W <= int(sx) <= W * 2 and -H <= int(sy) <= H * 2):
                return
            pts.append((int(sx), int(sy)))

        # Only draw if at least one corner is on screen
        if any(0 <= x <= W and 0 <= y <= H for x, y in pts):
            pygame.draw.polygon(screen, (70, 70, 70), pts)
            pygame.draw.polygon(screen, (100, 100, 100), pts, 1)
            # Centre-line dashes
            mid_t = ((tl_lat + tr_lat) / 2, (tl_lon + tr_lon) / 2)
            mid_f = ((fl_lat + fr_lat) / 2, (fl_lon + fr_lon) / 2)
            p_t = self._project_world_point(*mid_t, elev_ft, heading_rad, pitch_rad, roll_rad, cx, horizon_cy)
            p_f = self._project_world_point(*mid_f, elev_ft, heading_rad, pitch_rad, roll_rad, cx, horizon_cy)
            if p_t and p_f:
                pygame.draw.line(screen, (255, 255, 255), (int(p_t[0]), int(p_t[1])), (int(p_f[0]), int(p_f[1])), 1)

    def _draw_cloud_layer(self, screen: pygame.Surface, W: int, H: int, horizon_cy: float) -> None:
        """Draw a solid cloud overcast layer at the weather ceiling."""
        if self._weather_ceiling_ft is None:
            return
        ceiling_ft = float(self._weather_ceiling_ft)
        alt_ft = self._altitude_ft
        delta_ft = ceiling_ft - alt_ft

        # Vertical position on windshield: above horizon = negative offset
        # sky scale: ~7.5 px per degree of pitch, at typical approach 5 deg pitch-down view
        sky_scale_px_per_ft = 7.5 / max(1.0, alt_ft)  # rough scale
        # Alternatively: use direct projection at mid-screen distance
        # Keep it simple: if ceiling is above, draw at top; if below, fill entire sky
        if delta_ft <= 0:
            # We are in/above the cloud — grey out entire sky
            cloud_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            cloud_surf.fill((200, 200, 200, 210))
            screen.blit(cloud_surf, (0, 0))
        else:
            # Cloud base is above us — draw a band
            # Map: ceiling_ft above = horizon offset
            # Simple model: cloud_y = horizon_cy - delta_ft * (H/2) / max(500, alt_ft)
            cloud_y = int(horizon_cy - delta_ft * 0.012)
            cloud_y = max(0, min(H - 10, cloud_y))
            band_h = max(20, H - cloud_y)
            cloud_surf = pygame.Surface((W, band_h), pygame.SRCALPHA)
            # Gradient: more opaque at top, less at bottom edge
            for row in range(band_h):
                alpha = int(180 * (1.0 - row / band_h))
                pygame.draw.line(cloud_surf, (200, 205, 210, alpha), (0, row), (W, row))
            screen.blit(cloud_surf, (0, cloud_y))

    def _horizon_line_endpoints(
        self, width: int, horizon_center_y: float, roll_deg: float
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        center_x = width / 2
        roll_rad = math.radians(roll_deg)
        slope = math.tan(roll_rad)
        return (
            (0.0, horizon_center_y + center_x * slope),
            (float(width), horizon_center_y - (width - center_x) * slope),
        )

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

        # CDI bezel
        cdi_r = pygame.Rect(
            _CDI_X - recess_margin, _CDI_Y - recess_margin,
            _NAV_W + recess_margin * 2, _CDI_H + recess_margin * 2 + 18,
        )
        pygame.draw.rect(screen, _BEZEL_COLOR, cdi_r, border_radius=6)
        pygame.draw.rect(screen, (25, 25, 25), cdi_r, 2, border_radius=6)

    def _draw_radio_stack(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (20, 20, 20),
                         pygame.Rect(_RADIO_X, _RADIO_Y, _RADIO_W, _RADIO_H),
                         border_radius=4)
        pygame.draw.rect(screen, (55, 55, 55),
                         pygame.Rect(_RADIO_X, _RADIO_Y, _RADIO_W, _RADIO_H),
                         1, border_radius=4)
        if self._avionics_powered:
            labels = [
                ("COM1", f"{self._com1_mhz:.3f}", (0, 185, 255)),
                ("NAV1", f"{self._nav1_mhz:.2f}",  (100, 230, 100)),
                ("XPDR", f"{self._squawk:04d}",    (230, 200, 100)),
                ("ADF",  "400.0",                  (220, 180, 220)),
            ]
        else:
            labels = [
                ("COM1", "OFF", (120, 120, 120)),
                ("NAV1", "OFF", (120, 120, 120)),
                ("XPDR", "OFF", (120, 120, 120)),
                ("ADF",  "OFF", (120, 120, 120)),
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
        cx, cy = self.width // 2, self.height - 26
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
        system_text = (
            f"MSTR {'ON' if self._master_on else 'OFF'}  "
            f"AVN {'ON' if self._avionics_on else 'OFF'}  "
            f"MAG {self._magneto_position}  "
            f"MIX {self._mixture_pct:3.0f}%  "
            f"CARB {'HOT' if self._carb_heat_on else 'COLD'}"
        )
        sys_surface = self.info_font.render(system_text, True, (180, 180, 180))
        screen.blit(sys_surface, (8, strip_y - 16))

    def _draw_flap_indicator(self, screen: pygame.Surface) -> None:
        """Small flap position indicator strip above the info strip."""
        if self._flaps_deg <= 0.0:
            return
        x, y = 550, self.height - 36
        w, h = 120, 14
        pygame.draw.rect(screen, (40, 40, 40), (x, y, w, h))
        fill_w = int(w * self._flaps_deg / 30.0)
        color = (100, 220, 100) if self._flaps_deg <= 20 else (230, 180, 60)
        pygame.draw.rect(screen, color, (x, y, fill_w, h))
        pygame.draw.rect(screen, (120, 120, 120), (x, y, w, h), 1)
        lbl = self.label_font.render(f"FLAPS {self._flaps_deg:.0f}°", True, (230, 230, 230))
        screen.blit(lbl, (x + w + 6, y))

    def _draw_debrief(self, screen: pygame.Surface) -> None:
        """Render a debrief text overlay in the centre of the screen."""
        if not self._debrief_text:
            return
        lines = self._debrief_text.split("\n")
        pad = 18
        line_h = 22
        panel_h = len(lines) * line_h + pad * 2
        panel_w = 460
        px = (self.width - panel_w) // 2
        py = (self.height - panel_h) // 2
        overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        overlay.fill((10, 15, 30, 220))
        pygame.draw.rect(overlay, (80, 130, 200), overlay.get_rect(), 2, border_radius=8)
        for i, line in enumerate(lines):
            color = (255, 220, 80) if i == 0 else (210, 230, 255)
            t = self.info_font.render(line, True, color)
            overlay.blit(t, (pad, pad + i * line_h))
        hint = self.label_font.render("Press D to close debrief", True, (120, 140, 180))
        overlay.blit(hint, (panel_w - hint.get_width() - pad, panel_h - hint.get_height() - 6))
        screen.blit(overlay, (px, py))
