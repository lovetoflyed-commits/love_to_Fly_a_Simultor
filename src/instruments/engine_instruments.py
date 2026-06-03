from __future__ import annotations

import pygame

from .base_instrument import Instrument


class EngineInstruments(Instrument):
    """Oil temperature, oil pressure, and L/R fuel quantity panel for the C152."""

    def __init__(self, width: int = 180, height: int = 170) -> None:
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
            return (0, 175, 65)     # normal – green
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
            return (0, 175, 65)     # normal – green
        return (215, 175, 30)       # high – yellow

    @staticmethod
    def _fuel_color(ratio: float) -> tuple[int, int, int]:
        if ratio < 0.15:
            return (215, 40, 40)
        if ratio < 0.25:
            return (215, 175, 30)
        return (0, 175, 65)

    @staticmethod
    def _suction_color(suction_inhg: float) -> tuple[int, int, int]:
        if suction_inhg < 3.0:
            return (215, 40, 40)
        if suction_inhg < 4.5:
            return (215, 175, 30)
        if suction_inhg <= 5.5:
            return (0, 175, 65)
        return (215, 175, 30)

    @staticmethod
    def _bus_color(voltage: float, powered: bool) -> tuple[int, int, int]:
        if not powered:
            return (120, 120, 120)
        if voltage < 12.0:
            return (215, 40, 40)
        if voltage < 12.6:
            return (215, 175, 30)
        return (0, 175, 65)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_bar_gauge(
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
        """Draw a vertical bar gauge with a label below."""
        bg_rect = pygame.Rect(x, bar_top, bar_w, bar_h)
        pygame.draw.rect(self.surface, (28, 28, 28), bg_rect)
        pygame.draw.rect(self.surface, (85, 85, 85), bg_rect, 1)

        fill_h = int(max(0.0, min(1.0, ratio)) * (bar_h - 2))
        if fill_h > 0:
            pygame.draw.rect(
                self.surface, color,
                pygame.Rect(x + 1, bar_top + bar_h - 1 - fill_h, bar_w - 2, fill_h),
            )

        lbl_surf = self.small_font.render(label, True, (175, 175, 175))
        self.surface.blit(lbl_surf, (x + bar_w // 2 - lbl_surf.get_width() // 2, bar_top + bar_h + 2))

        val_surf = self.small_font.render(reading, True, (215, 215, 215))
        self.surface.blit(val_surf, (x + bar_w // 2 - val_surf.get_width() // 2, bar_top + bar_h + 14))

    def draw(self) -> pygame.Surface:
        self.surface.fill((58, 58, 58))
        pygame.draw.rect(self.surface, (48, 48, 48),
                         pygame.Rect(0, 0, self.width, self.height), 2)

        # Title
        title = self.font.render("ENGINE", True, (195, 195, 195))
        self.surface.blit(title, title.get_rect(center=(self.width // 2, 10)))

        bar_top = 24
        bar_h = 90
        bar_w = 28

        fuel_half = self.fuel_kg / 2.0
        max_half = self.max_fuel_kg / 2.0

        gauges = [
            (
                "OIL T",
                f"{self.oil_temp_c:.0f}\u00b0",
                self.oil_temp_c / 150.0,
                self._oil_temp_color(self.oil_temp_c),
            ),
            (
                "OIL P",
                f"{self.oil_pressure_psi:.0f}",
                self.oil_pressure_psi / 100.0,
                self._oil_pressure_color(self.oil_pressure_psi),
            ),
            (
                "FUEL L",
                f"{fuel_half:.0f}kg",
                fuel_half / max_half,
                self._fuel_color(fuel_half / max_half),
            ),
            (
                "FUEL R",
                f"{fuel_half:.0f}kg",
                fuel_half / max_half,
                self._fuel_color(fuel_half / max_half),
            ),
        ]

        # Evenly space four gauges across panel width
        margin = 12
        spacing = (self.width - 2 * margin - bar_w * len(gauges)) // (len(gauges) - 1)
        for i, (lbl, reading, ratio, color) in enumerate(gauges):
            bx = margin + i * (bar_w + spacing)
            self._draw_bar_gauge(lbl, reading, bx, bar_top, bar_h, bar_w, ratio, color)

        systems_y = bar_top + bar_h + 31
        engine_systems_active = self.master_on and self.engine_running
        vac = self.small_font.render(
            f"VAC {self.suction_inhg:0.1f}",
            True,
            self._suction_color(self.suction_inhg),
        )
        bus = self.small_font.render(
            f"BUS {self.bus_voltage_v:0.1f}V",
            True,
            self._bus_color(self.bus_voltage_v, self.master_on),
        )
        switches = self.small_font.render(
            f"M:{'ON' if self.master_on else 'OFF'} AV:{'ON' if self.avionics_on else 'OFF'} MAG:{self.magneto_position}",
            True,
            (205, 205, 205) if engine_systems_active else (150, 150, 150),
        )
        self.surface.blit(vac, (10, systems_y))
        self.surface.blit(bus, (self.width - bus.get_width() - 10, systems_y))
        self.surface.blit(switches, (10, systems_y + 14))

        return self.surface
