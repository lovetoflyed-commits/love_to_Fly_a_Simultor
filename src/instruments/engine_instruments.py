from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class EngineInstruments(Instrument):
    def __init__(self, width: int = 240, height: int = 220) -> None:
        super().__init__(width, height)
        self.n1_pct = 0.0
        self.fuel_kg = 0.0
        self.max_fuel_kg = 1.0
        self.oil_pressure = 60.0
        self.egt_c = 650.0

    def update(self, state: dict) -> None:
        self.n1_pct = float(state.get("n1_pct", 0.0))
        self.fuel_kg = float(state.get("fuel_kg", 0.0))
        self.max_fuel_kg = max(1.0, float(state.get("max_fuel_kg", 1.0)))
        self.oil_pressure = float(state.get("oil_pressure_psi", 60.0))
        self.egt_c = float(state.get("egt_c", 650.0))

    def draw(self) -> pygame.Surface:
        self.surface.fill((26, 26, 26))
        center = pygame.Vector2(70, 80)
        pygame.draw.circle(self.surface, (42, 42, 42), center, 58)
        pygame.draw.circle(self.surface, (130, 130, 130), center, 58, 2)
        rect = pygame.Rect(center.x - 50, center.y - 50, 100, 100)
        pygame.draw.arc(self.surface, (60, 180, 60), rect, math.radians(135), math.radians(315), 8)
        angle = math.radians(135 + (self.n1_pct / 100.0) * 180.0)
        tip = (center.x + math.cos(angle) * 42, center.y + math.sin(angle) * 42)
        pygame.draw.line(self.surface, (255, 80, 80), center, tip, 4)
        self.surface.blit(self.font.render("N1", True, (255, 255, 255)), (55, 18))
        self.surface.blit(self.large_font.render(f"{self.n1_pct:0.0f}", True, (255, 255, 255)), (42, 90))

        fuel_ratio = self.fuel_kg / self.max_fuel_kg
        pygame.draw.rect(self.surface, (50, 50, 50), pygame.Rect(150, 30, 30, 150))
        pygame.draw.rect(self.surface, (60, 200, 90), pygame.Rect(150, 30 + (1 - fuel_ratio) * 150, 30, fuel_ratio * 150))
        self.surface.blit(self.font.render("FUEL", True, (255, 255, 255)), (138, 8))
        self.surface.blit(self.small_font.render(f"{self.fuel_kg:.0f}kg", True, (220, 220, 220)), (138, 186))

        oil_width = min(90, max(0, self.oil_pressure))
        pygame.draw.rect(self.surface, (50, 50, 50), pygame.Rect(30, 180, 90, 14))
        pygame.draw.rect(self.surface, (220, 180, 60), pygame.Rect(30, 180, oil_width, 14))
        self.surface.blit(self.small_font.render(f"Oil {self.oil_pressure:.0f} psi", True, (220, 220, 220)), (30, 198))

        egt_width = min(90, max(0, self.egt_c / 10.0))
        pygame.draw.rect(self.surface, (50, 50, 50), pygame.Rect(30, 150, 90, 14))
        pygame.draw.rect(self.surface, (220, 80, 50), pygame.Rect(30, 150, egt_width, 14))
        self.surface.blit(self.small_font.render(f"EGT {self.egt_c:.0f} C", True, (220, 220, 220)), (30, 130))
        return self.surface
