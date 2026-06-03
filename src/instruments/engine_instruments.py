from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class EngineInstruments(Instrument):
    """Engine monitoring sub-panel for the Cessna 152.

    Contains arc-style gauges for:
      - Oil Temperature (°C)
      - Oil Pressure (PSI)
    And vertical bar gauges for:
      - Fuel Left / Right (kg)
    Plus system status line: VAC, BUS voltage, master/avionics/magneto.
    """

    def __init__(self, width: int = 185, height: int = 162) -> None:
        super().__init__(width, height)
        self.oil_temp_c = 80.0
        self.oil_pressure_psi = 65.0
        self.fuel_kg = 0.0
        self.max_fuel_kg = 83.0
        self.suction_inhg = 4.8
        self.bus_voltage_v = 13.8
        self.master_on = True
        self.avionics_on = True
        self.engine_running = True
        self.magneto_position = "BOTH"

    def update(self, state: dict) -> None:
        self.oil_temp_c = float(state.get("oil_temp_c", 80.0))
        self.oil_pressure_psi = float(state.get("oil_pressure_psi", 65.0))
        self.fuel_kg = float(state.get("fuel_kg", 0.0))
        self.max_fuel_kg = max(1.0, float(state.get("max_fuel_kg", 83.0)))
        self.suction_inhg = float(state.get("suction_inhg", 4.8))
        self.bus_voltage_v = float(state.get("bus_voltage_v", 13.8))
        self.master_on = bool(state.get("master_on", True))
        self.avionics_on = bool(state.get("avionics_on", True))
        self.engine_running = bool(state.get("engine_running", True))
        self.magneto_position = str(state.get("magneto_position", "BOTH")).upper()

    # ------------------------------------------------------------------
    # Colour helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _oil_temp_color(temp_c: float) -> tuple[int, int, int]:
        if temp_c < 40:
            return (80, 160, 230)   # cold – blue
        if temp_c < 100:
            return (0, 185, 75)     # normal – green
        if temp_c < 120:
            return (215, 175, 30)   # warm – yellow
        return (215, 40, 40)        # hot – red

    @staticmethod
    def _oil_pressure_color(psi: float) -> tuple[int, int, int]:
        if psi < 25:
            return (215, 40, 40)    # low – red
        if psi < 55:
            return (215, 175, 30)   # low-normal – yellow
        if psi <= 90:
            return (0, 185, 75)     # normal – green
        return (215, 175, 30)       # high – yellow

    @staticmethod
    def _fuel_color(ratio: float) -> tuple[int, int, int]:
        if ratio < 0.15:
            return (215, 40, 40)
        if ratio < 0.25:
            return (215, 175, 30)
        return (0, 185, 75)

    @staticmethod
    def _suction_color(suction_inhg: float) -> tuple[int, int, int]:
        if suction_inhg < 3.0:
            return (215, 40, 40)
        if suction_inhg < 4.5:
            return (215, 175, 30)
        if suction_inhg <= 5.5:
            return (0, 185, 75)
        return (215, 175, 30)

    @staticmethod
    def _bus_color(voltage: float, powered: bool) -> tuple[int, int, int]:
        if not powered:
            return (120, 120, 120)
        if voltage < 12.0:
            return (215, 40, 40)
        if voltage < 12.6:
            return (215, 175, 30)
        return (0, 185, 75)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_arc_gauge(
        self,
        label: str,
        reading: str,
        cx: float,
        cy: float,
        arc_r: int,
        ratio: float,
        color: tuple[int, int, int],
        start_deg: float = 210.0,
        sweep_deg: float = 120.0,
    ) -> None:
        """Draw a compact arc-style gauge centred at (cx, cy)."""
        # Background arc (dark)
        bg_rect = pygame.Rect(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
        pygame.draw.arc(self.surface, (45, 45, 45), bg_rect,
                        math.radians(start_deg - sweep_deg),
                        math.radians(start_deg), 6)
        # Active arc
        active_sweep = sweep_deg * max(0.0, min(1.0, ratio))
        if active_sweep > 1.0:
            pygame.draw.arc(self.surface, color, bg_rect,
                            math.radians(start_deg - active_sweep),
                            math.radians(start_deg), 7)
        # Bezel ring
        pygame.draw.circle(self.surface, (55, 55, 55), (int(cx), int(cy)), arc_r + 2, 2)
        # Tick marks at 0%, 25%, 50%, 75%, 100%
        for pct in (0, 25, 50, 75, 100):
            tick_angle = math.radians(start_deg - pct / 100.0 * sweep_deg)
            ox = cx + math.cos(tick_angle) * arc_r
            oy = cy - math.sin(tick_angle) * arc_r
            ix = cx + math.cos(tick_angle) * (arc_r - 7)
            iy = cy - math.sin(tick_angle) * (arc_r - 7)
            pygame.draw.line(self.surface, (160, 160, 160), (ox, oy), (ix, iy), 1)
        # Needle line from centre to arc edge
        needle_angle = math.radians(start_deg - ratio * sweep_deg)
        nx = cx + math.cos(needle_angle) * (arc_r - 2)
        ny = cy - math.sin(needle_angle) * (arc_r - 2)
        pygame.draw.line(self.surface, (255, 255, 255), (cx, cy), (nx, ny), 2)
        pygame.draw.circle(self.surface, (40, 40, 40), (int(cx), int(cy)), 4)
        pygame.draw.circle(self.surface, (120, 120, 120), (int(cx), int(cy)), 4, 1)
        # Labels
        lbl = self.small_font.render(label, True, (170, 170, 170))
        self.surface.blit(lbl, lbl.get_rect(center=(int(cx), int(cy) + arc_r + 10)))
        val = self.small_font.render(reading, True, (220, 220, 220))
        self.surface.blit(val, val.get_rect(center=(int(cx), int(cy) + arc_r + 20)))

    def _draw_fuel_bar(
        self,
        label: str,
        reading: str,
        x: int,
        bar_top: int,
        bar_h: int,
        bar_w: int,
        ratio: float,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a vertical bar fuel gauge."""
        # Background
        bg_rect = pygame.Rect(x, bar_top, bar_w, bar_h)
        pygame.draw.rect(self.surface, (28, 28, 28), bg_rect, border_radius=3)
        pygame.draw.rect(self.surface, (75, 75, 75), bg_rect, 1, border_radius=3)

        # Fill
        fill_h = int(max(0.0, min(1.0, ratio)) * (bar_h - 2))
        if fill_h > 0:
            fill_rect = pygame.Rect(x + 1, bar_top + bar_h - 1 - fill_h, bar_w - 2, fill_h)
            pygame.draw.rect(self.surface, color, fill_rect, border_radius=2)
            # Highlight stripe
            pygame.draw.rect(self.surface, tuple(min(255, c + 40) for c in color),
                             pygame.Rect(x + 2, bar_top + bar_h - 1 - fill_h, 3, fill_h))

        # Tick marks at 25/50/75%
        for pct in (25, 50, 75):
            ty = bar_top + bar_h - int(bar_h * pct / 100)
            pygame.draw.line(self.surface, (80, 80, 80), (x, ty), (x + bar_w, ty), 1)

        # Labels
        lbl = self.small_font.render(label, True, (165, 165, 165))
        self.surface.blit(lbl, (x + bar_w // 2 - lbl.get_width() // 2, bar_top + bar_h + 2))
        val = self.small_font.render(reading, True, (210, 210, 210))
        self.surface.blit(val, (x + bar_w // 2 - val.get_width() // 2, bar_top + bar_h + 13))

    def draw(self) -> pygame.Surface:
        self.surface.fill((50, 50, 50))
        # Subtle panel gradient (darker at top)
        for y in range(self.height):
            t = y / max(1, self.height)
            shade = int(42 + t * 16)
            pygame.draw.line(self.surface, (shade, shade, shade), (0, y), (self.width, y))

        pygame.draw.rect(self.surface, (35, 35, 35),
                         pygame.Rect(0, 0, self.width, self.height), 2)

        # ── Section header ────────────────────────────────────────────────
        title = self.small_font.render("ENGINE", True, (180, 180, 180))
        self.surface.blit(title, title.get_rect(center=(self.width // 2, 8)))

        # Divider
        pygame.draw.line(self.surface, (65, 65, 65), (6, 16), (self.width - 6, 16), 1)

        # ── Oil gauges (arc style) ────────────────────────────────────────
        arc_r = 28
        oil_t_cx = int(self.width * 0.27)
        oil_t_cy = 52
        oil_p_cx = int(self.width * 0.73)
        oil_p_cy = 52

        self._draw_arc_gauge(
            "OIL T", f"{self.oil_temp_c:.0f}°",
            oil_t_cx, oil_t_cy, arc_r,
            ratio=self.oil_temp_c / 150.0,
            color=self._oil_temp_color(self.oil_temp_c),
        )
        self._draw_arc_gauge(
            "OIL P", f"{self.oil_pressure_psi:.0f}",
            oil_p_cx, oil_p_cy, arc_r,
            ratio=self.oil_pressure_psi / 100.0,
            color=self._oil_pressure_color(self.oil_pressure_psi),
        )

        # Thin divider between oil gauges and fuel bars
        div_y = oil_t_cy + arc_r + 28
        pygame.draw.line(self.surface, (60, 60, 60), (6, div_y), (self.width - 6, div_y), 1)

        # ── Fuel bar gauges ───────────────────────────────────────────────
        fuel_half = self.fuel_kg / 2.0
        max_half = self.max_fuel_kg / 2.0
        ratio = fuel_half / max(0.01, max_half)
        color = self._fuel_color(ratio)

        bar_top = div_y + 4
        bar_h = 42
        bar_w = 26
        margin = 20
        # Left fuel tank
        lx = margin
        self._draw_fuel_bar("L", f"{fuel_half:.0f}kg", lx, bar_top, bar_h, bar_w, ratio, color)
        # Right fuel tank
        rx = self.width - margin - bar_w
        self._draw_fuel_bar("R", f"{fuel_half:.0f}kg", rx, bar_top, bar_h, bar_w, ratio, color)

        # ── Systems status row ────────────────────────────────────────────
        systems_y = bar_top + bar_h + 28
        engine_active = self.master_on and self.engine_running

        vac = self.small_font.render(
            f"VAC {self.suction_inhg:.1f}",
            True, self._suction_color(self.suction_inhg),
        )
        bus = self.small_font.render(
            f"BUS {self.bus_voltage_v:.1f}V",
            True, self._bus_color(self.bus_voltage_v, self.master_on),
        )
        switches = self.small_font.render(
            f"M:{'ON' if self.master_on else 'OFF'}"
            f"  AV:{'ON' if self.avionics_on else 'OFF'}"
            f"  {self.magneto_position}",
            True,
            (200, 200, 200) if engine_active else (140, 140, 140),
        )
        self.surface.blit(vac, (8, systems_y))
        self.surface.blit(bus, (self.width - bus.get_width() - 8, systems_y))
        self.surface.blit(switches, switches.get_rect(center=(self.width // 2, systems_y + 13)))

        return self.surface

