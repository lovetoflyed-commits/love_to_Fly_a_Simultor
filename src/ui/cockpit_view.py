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
_ROW1_Y = _PANEL_TOP + 8   # top edge of first instrument row
_ROW2_Y = _ROW1_Y + _INST_SIZE + 14  # second row

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
_RADIO_W = 178
_RADIO_H = _ENGINE_Y + _ENGINE_H - _PANEL_TOP

_NAV_X = 930
_NAV_Y = _ROW1_Y
_NAV_W = 310
_NAV_H = 210

_CDI_X = _NAV_X
_CDI_Y = _NAV_Y + _NAV_H + 20   # directly below nav display
_CDI_H = 80                       # height of CDI strip

# Panel colours
_CESSNA_GRAY = (58, 60, 62)          # realistic Cessna panel dark grey
_PANEL_HIGHLIGHT = (75, 77, 80)       # lighter edge for 3-D effect
_PANEL_SHADOW = (40, 40, 42)          # darker edge for 3-D effect
_BEZEL_COLOR = (30, 30, 32)
_BEZEL_HIGHLIGHT = (65, 65, 68)
_GLARESHIELD_COLOR = (18, 18, 18)
_PILLAR_COLOR = (28, 28, 28)
_LABEL_COLOR = (170, 172, 175)
_SECTION_LINE = (50, 52, 54)         # subtle divider lines between panel zones


class CockpitView:
    """Full Cessna 152 front cockpit view with windshield and instrument panel."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.width = screen_width
        self.height = screen_height
        self.label_font = pygame.font.SysFont("arial", 10)
        self.info_font = pygame.font.SysFont("arial", 12)
        self.radio_font = pygame.font.SysFont("courier", 12, bold=True)

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
        self._nearest_airport = "---"
        self._terrain_ft = 0.0
        self._terrain_objects: list = []

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
        self._nearest_airport = str(state.get("nearest_airport", "---"))
        self._terrain_ft = float(state.get("terrain_ft", 0.0))
        self._terrain_objects = state.get("terrain_objects", [])
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

        # Interactive instrument hover highlights
        mx, my = pygame.mouse.get_pos()
        self._draw_hover_highlight(screen, mx, my)
        self._update_cursor(mx, my)

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

        # ── Terrain objects (hills, towers) ──────────────────────────────────
        heading_rad = math.radians(self._heading_deg)
        pitch_rad = math.radians(self._pitch_deg)
        roll_rad = math.radians(-self._roll_deg)
        for obj in self._terrain_objects:
            self._draw_terrain_object(screen, obj, W, H, horizon_cy, heading_rad, pitch_rad, roll_rad, cx)

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

    def _draw_terrain_object(
        self,
        screen: pygame.Surface,
        obj: object,
        W: int,
        H: int,
        horizon_cy: float,
        heading_rad: float,
        pitch_rad: float,
        roll_rad: float,
        cx: float,
    ) -> None:
        """Draw a terrain object (hill silhouette or tower) in the windshield view."""
        lat = float(obj.lat)  # type: ignore[attr-defined]
        lon = float(obj.lon)  # type: ignore[attr-defined]
        base_ft = float(obj.base_elevation_ft)  # type: ignore[attr-defined]
        top_ft = float(obj.top_elevation_ft)  # type: ignore[attr-defined]
        obj_type: str = obj.object_type  # type: ignore[attr-defined]
        name: str = obj.name  # type: ignore[attr-defined]

        p_top = self._project_world_point(lat, lon, top_ft, heading_rad, pitch_rad, roll_rad, cx, horizon_cy)
        if p_top is None:
            return
        sx_top, sy_top = p_top

        if obj_type == "hill":
            # Draw a mountain silhouette as a filled triangle above the horizon
            p_base_l = self._project_world_point(lat - 0.04, lon - 0.04, base_ft, heading_rad, pitch_rad, roll_rad, cx, horizon_cy)
            p_base_r = self._project_world_point(lat + 0.04, lon + 0.04, base_ft, heading_rad, pitch_rad, roll_rad, cx, horizon_cy)
            if p_base_l is None or p_base_r is None:
                return
            pts = [
                (int(p_base_l[0]), int(p_base_l[1])),
                (int(sx_top), int(sy_top)),
                (int(p_base_r[0]), int(p_base_r[1])),
            ]
            # Only draw if at least the peak is somewhere near the screen
            if not (-W <= sx_top <= W * 2 and -H * 2 <= sy_top <= H * 2):
                return
            hill_color = (110, 100, 80) if base_ft < 3500 else (140, 130, 120)
            pygame.draw.polygon(screen, hill_color, pts)
            pygame.draw.polygon(screen, (160, 150, 130), pts, 1)
            # Label near peak if on screen
            if 0 <= int(sx_top) <= W and 0 <= int(sy_top) <= H and hasattr(self, "info_font"):
                lbl = self.info_font.render(name, True, (240, 230, 200))
                screen.blit(lbl, (int(sx_top) + 4, int(sy_top) - 12))
        else:
            # Tower / building: draw a vertical line from base to top
            p_base = self._project_world_point(lat, lon, base_ft, heading_rad, pitch_rad, roll_rad, cx, horizon_cy)
            if p_base is None:
                return
            sx_base, sy_base = p_base
            if not (-W <= sx_top <= W * 2 and -H * 2 <= sy_top <= H * 2):
                return
            color = (255, 80, 80) if obj_type == "tower" else (200, 200, 100)
            pygame.draw.line(screen, color, (int(sx_base), int(sy_base)), (int(sx_top), int(sy_top)), 2)
            # Antenna cap for towers
            if obj_type == "tower":
                pygame.draw.circle(screen, (255, 60, 60), (int(sx_top), int(sy_top)), 3)
            # Label if on-screen
            if 0 <= int(sx_top) <= W and 0 <= int(sy_top) <= H and hasattr(self, "info_font"):
                lbl = self.info_font.render(name, True, (255, 180, 180))
                screen.blit(lbl, (int(sx_top) + 4, int(sy_top) - 10))

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
        """Dark matte glareshield strip below the windshield."""
        # Gradient: slightly lighter at the top (catching light from sky)
        for y in range(_GLARESHIELD_H):
            t = 1.0 - y / _GLARESHIELD_H
            shade = int(18 + t * 14)
            pygame.draw.line(screen, (shade, shade, shade),
                             (0, _WINDSHIELD_H + y), (self.width, _WINDSHIELD_H + y))
        # Thin highlight at the very top of glareshield
        pygame.draw.line(screen, (45, 45, 45),
                         (0, _WINDSHIELD_H), (self.width, _WINDSHIELD_H), 1)

    def _draw_panel_background(self, screen: pygame.Surface) -> None:
        panel_rect = pygame.Rect(0, _PANEL_TOP, self.width, self.height - _PANEL_TOP)
        # Subtle vertical gradient: slightly lighter at top (glareshield edge)
        for y in range(panel_rect.height):
            t = y / max(1, panel_rect.height)
            r = int(_CESSNA_GRAY[0] - t * 8)
            g = int(_CESSNA_GRAY[1] - t * 8)
            b = int(_CESSNA_GRAY[2] - t * 8)
            pygame.draw.line(screen, (r, g, b),
                             (0, _PANEL_TOP + y), (self.width, _PANEL_TOP + y))
        # Top highlight line (bright edge where glareshield meets panel)
        pygame.draw.line(screen, _PANEL_HIGHLIGHT,
                         (0, _PANEL_TOP), (self.width, _PANEL_TOP), 2)
        # Bottom shadow line
        pygame.draw.line(screen, _PANEL_SHADOW,
                         (0, self.height - 1), (self.width, self.height - 1), 2)

    def _draw_panel_details(self, screen: pygame.Surface) -> None:
        """Recessed bezel areas for the instrument clusters with 3-D shadow/highlight."""
        recess_margin = 7

        def draw_bezel(rect: pygame.Rect) -> None:
            """Draw a recessed instrument bay with shadow/highlight edges."""
            # Fill
            pygame.draw.rect(screen, _BEZEL_COLOR, rect, border_radius=7)
            # Shadow on top + left edges (light comes from top-left)
            pygame.draw.line(screen, (15, 15, 15), rect.topleft, rect.topright, 2)
            pygame.draw.line(screen, (15, 15, 15), rect.topleft, rect.bottomleft, 2)
            # Highlight on bottom + right edges
            pygame.draw.line(screen, _BEZEL_HIGHLIGHT, rect.bottomleft, rect.bottomright, 1)
            pygame.draw.line(screen, _BEZEL_HIGHLIGHT, rect.topright, rect.bottomright, 1)
            # Outer outline
            pygame.draw.rect(screen, (20, 20, 20), rect, 1, border_radius=7)

        # Six-pack recess
        r1 = pygame.Rect(
            _COL_ASI - recess_margin,
            _ROW1_Y - recess_margin,
            (_COL_ALT - _COL_ASI) + _INST_SIZE + recess_margin * 2,
            (_ROW2_Y - _ROW1_Y) + _INST_SIZE + recess_margin * 2,
        )
        draw_bezel(r1)

        # "FLIGHT INSTRUMENTS" label above six-pack
        fi_lbl = self.label_font.render("FLIGHT INSTRUMENTS", True, (120, 122, 125))
        screen.blit(fi_lbl, (r1.centerx - fi_lbl.get_width() // 2, r1.top - 14))

        # Tachometer bezel
        tach_r = pygame.Rect(
            _TACH_X - recess_margin, _TACH_Y - recess_margin,
            _INST_SIZE + recess_margin * 2, _INST_SIZE + recess_margin * 2,
        )
        draw_bezel(tach_r)

        # Engine panel recess
        eng_r = pygame.Rect(
            _ENGINE_X - recess_margin, _ENGINE_Y - recess_margin,
            _ENGINE_W + recess_margin * 2, _ENGINE_H + recess_margin * 2,
        )
        draw_bezel(eng_r)

        # Vertical separator between six-pack cluster and right-side panels
        sep_x = r1.right + (_TACH_X - recess_margin - r1.right) // 2
        pygame.draw.line(
            screen, _SECTION_LINE,
            (sep_x, _PANEL_TOP + 4), (sep_x, self.height - 22), 1,
        )

        # Nav display recess
        nav_r = pygame.Rect(
            _NAV_X - recess_margin, _NAV_Y - recess_margin,
            _NAV_W + recess_margin * 2, _NAV_H + recess_margin * 2 + 18,
        )
        draw_bezel(nav_r)

        # CDI bezel
        cdi_r = pygame.Rect(
            _CDI_X - recess_margin, _CDI_Y - recess_margin,
            _NAV_W + recess_margin * 2, _CDI_H + recess_margin * 2 + 18,
        )
        draw_bezel(cdi_r)

    def _draw_radio_stack(self, screen: pygame.Surface) -> None:
        """Render a King-style avionics radio stack with green LCD displays."""
        rx, ry, rw, rh = _RADIO_X, _RADIO_Y, _RADIO_W, _RADIO_H

        # Outer housing
        pygame.draw.rect(screen, (22, 22, 22),
                         pygame.Rect(rx, ry, rw, rh), border_radius=5)
        # Housing highlight/shadow edges
        pygame.draw.line(screen, (50, 50, 50), (rx, ry), (rx + rw, ry), 1)
        pygame.draw.line(screen, (50, 50, 50), (rx, ry), (rx, ry + rh), 1)
        pygame.draw.line(screen, (10, 10, 10), (rx, ry + rh), (rx + rw, ry + rh), 1)
        pygame.draw.line(screen, (10, 10, 10), (rx + rw, ry), (rx + rw, ry + rh), 1)
        pygame.draw.rect(screen, (45, 45, 45),
                         pygame.Rect(rx, ry, rw, rh), 1, border_radius=5)

        if self._avionics_powered:
            entries = [
                ("COM 1", f"{self._com1_mhz:.3f}", "MHz", (0, 200, 80)),
                ("NAV 1", f"{self._nav1_mhz:.2f}",  "MHz", (0, 200, 80)),
                ("XPDR",  f"{self._squawk:04d}",    "CODE", (0, 200, 80)),
                ("ADF",   "400.0",                  "kHz",  (0, 200, 80)),
            ]
        else:
            entries = [
                ("COM 1", "- - - . - - -", "MHz", (55, 55, 55)),
                ("NAV 1", "- - - . - -",   "MHz", (55, 55, 55)),
                ("XPDR",  "- - - -",       "CODE", (55, 55, 55)),
                ("ADF",   "- - - . -",     "kHz",  (55, 55, 55)),
            ]

        item_h = rh // len(entries)
        for i, (name, freq, unit, lcd_color) in enumerate(entries):
            iy = ry + i * item_h
            # Unit face background
            unit_rect = pygame.Rect(rx + 4, iy + 4, rw - 8, item_h - 8)
            pygame.draw.rect(screen, (16, 16, 16), unit_rect, border_radius=4)
            pygame.draw.rect(screen, (40, 40, 40), unit_rect, 1, border_radius=4)

            # Instrument name badge (left side)
            badge_rect = pygame.Rect(rx + 6, iy + 6, 40, item_h - 12)
            pygame.draw.rect(screen, (30, 30, 30), badge_rect, border_radius=3)
            name_surf = self.label_font.render(name, True, (160, 162, 165))
            screen.blit(name_surf, name_surf.get_rect(
                center=(badge_rect.centerx, badge_rect.centery)))

            # LCD display area (right of badge)
            lcd_rect = pygame.Rect(rx + 50, iy + 7, rw - 56, item_h - 14)
            pygame.draw.rect(screen, (8, 20, 8), lcd_rect, border_radius=2)
            pygame.draw.rect(screen, (0, 60, 20), lcd_rect, 1, border_radius=2)

            # Frequency / code in LCD font
            freq_surf = self.radio_font.render(freq, True, lcd_color)
            screen.blit(freq_surf, freq_surf.get_rect(
                center=(lcd_rect.centerx, lcd_rect.centery - 3)))

            # Unit label below freq
            unit_surf = self.label_font.render(unit, True,
                                               (0, 120, 50) if self._avionics_powered else (40, 40, 40))
            screen.blit(unit_surf, unit_surf.get_rect(
                center=(lcd_rect.centerx, lcd_rect.bottom - 5)))

            # Separator line between units
            if i < len(entries) - 1:
                pygame.draw.line(screen, (35, 35, 35),
                                 (rx + 4, iy + item_h),
                                 (rx + rw - 4, iy + item_h), 1)

        label = self.label_font.render("AVIONICS STACK", True, (110, 112, 115))
        screen.blit(label, (rx + rw // 2 - label.get_width() // 2, ry + rh + 3))

    def _draw_yoke(self, screen: pygame.Surface) -> None:
        """Cessna-style control yoke at the bottom centre of the cockpit panel."""
        cx, cy = self.width // 2, self.height - 24
        shaft_color = (28, 28, 28)
        grip_color = (24, 24, 24)
        highlight = (55, 55, 55)

        # Column shaft (slightly tapered)
        pygame.draw.rect(screen, shaft_color,
                         pygame.Rect(cx - 8, cy - 34, 16, 36), border_radius=4)
        pygame.draw.line(screen, highlight, (cx - 8, cy - 34), (cx - 8, cy), 1)

        # Horizontal cross-bar
        pygame.draw.rect(screen, shaft_color,
                         pygame.Rect(cx - 52, cy - 34, 104, 14), border_radius=7)
        pygame.draw.line(screen, highlight, (cx - 52, cy - 34), (cx + 52, cy - 34), 1)

        # Left grip (rounded D-shape)
        pygame.draw.ellipse(screen, grip_color,
                            pygame.Rect(cx - 66, cy - 56, 24, 42))
        pygame.draw.ellipse(screen, highlight,
                            pygame.Rect(cx - 66, cy - 56, 24, 42), 1)

        # Right grip
        pygame.draw.ellipse(screen, grip_color,
                            pygame.Rect(cx + 42, cy - 56, 24, 42))
        pygame.draw.ellipse(screen, highlight,
                            pygame.Rect(cx + 42, cy - 56, 24, 42), 1)

        # PTT / horn button (red, left horn)
        pygame.draw.circle(screen, (160, 25, 25), (cx - 54, cy - 36), 5)
        pygame.draw.circle(screen, (200, 60, 60), (cx - 54, cy - 36), 5, 1)

    def _draw_info_strip(self, screen: pygame.Surface) -> None:
        """Bottom status strip with two rows: system state (row 1) and ATC/checklist (row 2)."""
        strip_h = 38
        strip_y = self.height - strip_h

        # Background
        pygame.draw.rect(screen, (12, 12, 14),
                         pygame.Rect(0, strip_y, self.width, strip_h))
        pygame.draw.line(screen, (45, 47, 50),
                         (0, strip_y), (self.width, strip_y), 1)
        # Separator between row 1 and row 2
        pygame.draw.line(screen, (30, 32, 35),
                         (8, strip_y + 19), (self.width - 8, strip_y + 19), 1)

        # ── Row 1: system state badges ────────────────────────────────────
        sys_y = strip_y + 3

        def _sys_badge(label: str, on: bool, good_color: tuple, bad_color: tuple,
                       x: int) -> int:
            color = good_color if on else bad_color
            surf = self.label_font.render(label, True, color)
            screen.blit(surf, (x, sys_y))
            return x + surf.get_width() + 8

        x = 8
        x = _sys_badge(
            f"MSTR:{'ON' if self._master_on else 'OFF'}",
            self._master_on, (140, 220, 140), (220, 140, 140), x,
        )
        x = _sys_badge(
            f"AVN:{'ON' if self._avionics_on else 'OFF'}",
            self._avionics_on, (140, 190, 220), (180, 180, 180), x,
        )
        mag_ok = self._magneto_position in ("BOTH", "LEFT", "RIGHT")
        x = _sys_badge(
            f"MAG:{self._magneto_position}",
            mag_ok, (210, 210, 140), (180, 180, 180), x,
        )
        mix_ok = self._mixture_pct >= 60
        x = _sys_badge(
            f"MIX:{self._mixture_pct:3.0f}%",
            mix_ok, (210, 180, 120), (220, 140, 140), x,
        )
        _sys_badge(
            f"CARB:{'HOT' if self._carb_heat_on else 'COLD'}",
            not self._carb_heat_on, (190, 190, 190), (230, 160, 60), x,
        )

        # Nearest airport + terrain elevation (right side of row 1)
        near_str = f"NEAR:{self._nearest_airport}  GND:{self._terrain_ft:.0f}ft"
        near = self.label_font.render(near_str, True, (150, 155, 165))
        screen.blit(near, (self.width - near.get_width() - 8, sys_y))

        # ── Row 2: ATC messages + checklist ──────────────────────────────
        atc_y = strip_y + 21

        for idx, msg in enumerate(self.atc_messages):
            t = self.info_font.render(msg, True, (145, 195, 255))
            screen.blit(t, (8 + idx * (self.width // 3), atc_y))

        ck = self.info_font.render(self.checklist_status, True, (240, 205, 95))
        screen.blit(ck, (self.width - ck.get_width() - 8, atc_y))

    def _draw_flap_indicator(self, screen: pygame.Surface) -> None:
        """Small flap position indicator strip above the info strip, left side."""
        if self._flaps_deg <= 0.0:
            return
        x, y = 10, self.height - 54   # above the 38 px footer, far left
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

    # ── Interactive instrument mouse support ───────────────────────────────

    # Bounding boxes of interactive instruments (x, y, w, h, scroll_label)
    _INTERACTIVE: list[tuple[int, int, int, int, str]] = [
        (_COL_DI,  _ROW2_Y,  _INST_SIZE, _INST_SIZE, "HDG BUG ±1°  (Shift ±10°)"),
        (_COL_ALT, _ROW1_Y,  _INST_SIZE, _INST_SIZE, "BARO ±0.01 inHg"),
        (_TACH_X,  _TACH_Y,  _INST_SIZE, _INST_SIZE, "THROTTLE ±5%"),
        (_RADIO_X, _RADIO_Y, _RADIO_W,   _RADIO_H,   "RADIO (COM1 / NAV1 / XPDR)"),
    ]

    def handle_event(self, event: pygame.event.Event) -> dict:
        """Process a mouse event for instrument interaction.

        Handles both legacy MOUSEBUTTONDOWN (buttons 4/5) and the modern
        MOUSEWHEEL event (pygame ≥ 2.0).  Returns a dict with any of:
          - heading_bug_delta : float  (degrees, ± with Shift for ±10)
          - baro_delta        : float  (inHg)
          - throttle_delta    : float  (percent)
          - com1_delta        : float  (MHz)
          - nav1_delta        : float  (MHz)
          - squawk_next / squawk_prev : bool
        """
        changes: dict = {}

        # Determine scroll direction and cursor position
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            direction = 1 if event.button == 4 else -1
            mx, my = event.pos
        elif event.type == getattr(pygame, "MOUSEWHEEL", -1):
            direction = 1 if event.y > 0 else -1   # type: ignore[attr-defined]
            mx, my = pygame.mouse.get_pos()
        else:
            return changes

        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

        # ── Heading indicator (heading bug) ──────────────────────────────
        if (_COL_DI <= mx < _COL_DI + _INST_SIZE
                and _ROW2_Y <= my < _ROW2_Y + _INST_SIZE):
            step = 10.0 if shift else 1.0
            changes["heading_bug_delta"] = direction * step

        # ── Altimeter (barometric setting) ───────────────────────────────
        elif (_COL_ALT <= mx < _COL_ALT + _INST_SIZE
                and _ROW1_Y <= my < _ROW1_Y + _INST_SIZE):
            changes["baro_delta"] = direction * 0.01

        # ── Tachometer (throttle) ─────────────────────────────────────────
        elif (_TACH_X <= mx < _TACH_X + _INST_SIZE
                and _TACH_Y <= my < _TACH_Y + _INST_SIZE):
            changes["throttle_delta"] = direction * 5.0

        # ── Radio stack ──────────────────────────────────────────────────
        elif (_RADIO_X <= mx < _RADIO_X + _RADIO_W
                and _RADIO_Y <= my < _RADIO_Y + _RADIO_H
                and self._avionics_powered):
            item_h = _RADIO_H // 4
            row_idx = (my - _RADIO_Y) // item_h
            if row_idx == 0:                    # COM 1
                changes["com1_delta"] = direction * 0.025
            elif row_idx == 1:                  # NAV 1
                changes["nav1_delta"] = direction * 0.05
            elif row_idx == 2:                  # XPDR
                if direction > 0:
                    changes["squawk_next"] = True
                else:
                    changes["squawk_prev"] = True

        return changes

    def _update_cursor(self, mx: int, my: int) -> None:
        """Change the system cursor to a hand when hovering over interactive instruments."""
        hovering = any(
            x <= mx < x + w and y <= my < y + h
            for x, y, w, h, _ in self._INTERACTIVE
        )
        try:
            cursor = pygame.SYSTEM_CURSOR_HAND if hovering else pygame.SYSTEM_CURSOR_ARROW
            pygame.mouse.set_cursor(cursor)
        except (AttributeError, pygame.error):
            pass  # older pygame versions don't support named system cursors

    def _draw_hover_highlight(self, screen: pygame.Surface, mx: int, my: int) -> None:
        """Draw a cyan outline and tooltip over the interactive instrument under the cursor."""
        item_h = _RADIO_H // 4
        radio_rows = [
            (_RADIO_X, _RADIO_Y + i * item_h, _RADIO_W, item_h, lbl)
            for i, lbl in enumerate(
                ["COM1 ±0.025 MHz", "NAV1 ±0.050 MHz", "XPDR code", None]
            )
            if lbl is not None
        ]

        regions: list[tuple[int, int, int, int, str]] = [
            (_COL_DI,  _ROW2_Y,  _INST_SIZE, _INST_SIZE, "↕ HDG BUG ±1°  (Shift ±10°)"),
            (_COL_ALT, _ROW1_Y,  _INST_SIZE, _INST_SIZE, "↕ BARO ±0.01 inHg"),
            (_TACH_X,  _TACH_Y,  _INST_SIZE, _INST_SIZE, "↕ THROTTLE ±5%"),
            *[
                (rx, ry, rw, rh, f"↕ {rl}")
                for rx, ry, rw, rh, rl in radio_rows
            ],
        ]

        for x, y, w, h, tip_text in regions:
            if x <= mx < x + w and y <= my < y + h:
                # Cyan glow outline around the instrument
                pygame.draw.rect(
                    screen, (0, 190, 210),
                    pygame.Rect(x - 2, y - 2, w + 4, h + 4),
                    2, border_radius=8,
                )
                # Tooltip box near cursor
                tip = self.label_font.render(tip_text, True, (0, 230, 255))
                tx = max(4, min(mx - tip.get_width() // 2,
                                self.width - tip.get_width() - 6))
                ty = max(_PANEL_TOP + 2, my - tip.get_height() - 6)
                bg = pygame.Surface(
                    (tip.get_width() + 8, tip.get_height() + 4), pygame.SRCALPHA
                )
                bg.fill((8, 18, 28, 210))
                screen.blit(bg, (tx - 4, ty - 2))
                screen.blit(tip, (tx, ty))
                break
