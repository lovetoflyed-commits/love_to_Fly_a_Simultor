from __future__ import annotations

import pygame

from ..instruments.airspeed_indicator import AirspeedIndicator
from ..instruments.altimeter import Altimeter
from ..instruments.attitude_indicator import AttitudeIndicator
from ..instruments.engine_instruments import EngineInstruments
from ..instruments.heading_indicator import HeadingIndicator
from ..instruments.nav_display import NavDisplay
from ..instruments.vsi import VSI


class CockpitView:
    def __init__(self, screen_width: int, screen_height: int) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.width = screen_width
        self.height = screen_height
        self.font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 15)
        self.attitude = AttitudeIndicator(220, 220)
        self.airspeed = AirspeedIndicator(170, 170)
        self.altimeter = Altimeter(170, 170)
        self.vsi = VSI(170, 170)
        self.heading = HeadingIndicator(180, 180)
        self.nav_display = NavDisplay(360, 240)
        self.engine = EngineInstruments(240, 220)
        self.atc_messages: list[str] = []
        self.checklist_status = "Checklist idle"
        self.layouts = {
            self.attitude: (210, 180),
            self.airspeed: (20, 135),
            self.altimeter: (420, 135),
            self.vsi: (610, 135),
            self.heading: (210, 390),
            self.nav_display: (850, 95),
            self.engine: (900, 380),
        }

    def update(self, state: dict) -> None:
        self.attitude.update(state)
        self.airspeed.update(state)
        self.altimeter.update(state)
        self.vsi.update(state)
        self.heading.update(state)
        self.nav_display.update(state)
        self.engine.update(state)
        self.atc_messages = [message.text if hasattr(message, "text") else str(message) for message in state.get("atc_messages", [])][-3:]
        self.checklist_status = state.get("checklist_status", self.checklist_status)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((26, 26, 26))
        panel = pygame.Rect(10, 10, self.width - 20, self.height - 20)
        pygame.draw.rect(screen, (34, 34, 34), panel, border_radius=8)
        pygame.draw.rect(screen, (55, 55, 55), panel, 2, border_radius=8)
        for instrument, pos in self.layouts.items():
            screen.blit(instrument.draw(), pos)
        bottom = pygame.Rect(20, self.height - 110, self.width - 40, 80)
        pygame.draw.rect(screen, (20, 20, 20), bottom, border_radius=6)
        pygame.draw.rect(screen, (90, 90, 90), bottom, 1, border_radius=6)
        for idx, message in enumerate(self.atc_messages):
            text = self.small_font.render(message, True, (200, 220, 255))
            screen.blit(text, (bottom.x + 10, bottom.y + 8 + idx * 20))
        checklist = self.small_font.render(self.checklist_status, True, (255, 230, 150))
        screen.blit(checklist, (bottom.right - checklist.get_width() - 10, bottom.y + 8))
