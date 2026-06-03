from __future__ import annotations

import pygame

from ..navigation.autopilot import Autopilot


class HUD:
    def __init__(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.SysFont("arial", 18, bold=True)
        self.small_font = pygame.font.SysFont("arial", 15)

    def draw(self, surface: pygame.Surface, state: dict, autopilot: Autopilot) -> None:
        airspeed_bug = self.small_font.render(f"SPD {state.get('airspeed_kts', 0):.0f}", True, (120, 255, 120))
        altitude_bug = self.small_font.render(f"ALT {state.get('altitude_ft', 0):.0f}", True, (120, 255, 120))
        heading_bug = self.small_font.render(f"HDG {state.get('heading_bug_deg', 0):03.0f}", True, (120, 220, 255))
        next_wp = self.small_font.render(f"NEXT {state.get('next_waypoint', '---')}", True, (120, 220, 255))
        ete = self.small_font.render(f"ETE {state.get('ete_min', 0):.1f} min", True, (120, 220, 255))
        ap = self.font.render("AP " + " ".join(autopilot.active_modes), True, (255, 200, 0))
        surface.blit(ap, (20, 18))
        surface.blit(airspeed_bug, (20, 46))
        surface.blit(altitude_bug, (20, 66))
        surface.blit(heading_bug, (20, 86))
        surface.blit(next_wp, (surface.get_width() - 170, 20))
        surface.blit(ete, (surface.get_width() - 170, 42))

        # Flap position
        flaps = float(state.get("flaps_deg", 0.0))
        if flaps > 0:
            flap_color = (255, 200, 60) if flaps <= 20 else (255, 100, 60)
            fl = self.small_font.render(f"FLAPS {flaps:.0f}°", True, flap_color)
            surface.blit(fl, (20, 106))

        # Pause indicator
        if state.get("paused", False):
            pause_text = self.font.render("⏸  PAUSED  ⏸", True, (255, 255, 100))
            surface.blit(pause_text, pause_text.get_rect(center=(surface.get_width() // 2, 20)))
