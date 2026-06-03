from __future__ import annotations

import pygame

from ..navigation.procedures import Procedure


class ProcedureViewer:
    def __init__(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.SysFont("arial", 18)
        self.procedure: Procedure | None = None
        self.step_index = 0

    def load_procedure(self, procedure: Procedure) -> None:
        self.procedure = procedure
        self.step_index = 0

    def draw(self, surface: pygame.Surface) -> None:
        if self.procedure is None:
            return
        panel = pygame.Rect(surface.get_width() - 320, 20, 300, 220)
        pygame.draw.rect(surface, (18, 18, 18), panel, border_radius=6)
        pygame.draw.rect(surface, (100, 100, 100), panel, 1, border_radius=6)
        title = self.font.render(self.procedure.name, True, (255, 255, 255))
        surface.blit(title, (panel.x + 10, panel.y + 8))
        for idx, waypoint in enumerate(self.procedure.waypoints):
            prefix = ">" if idx == self.step_index else " "
            text = self.font.render(f"{prefix} {waypoint.name} {waypoint.altitude_ft or 0:.0f}ft", True, (200, 220, 255) if idx == self.step_index else (210, 210, 210))
            surface.blit(text, (panel.x + 10, panel.y + 40 + idx * 24))

    def next_step(self) -> None:
        if self.procedure is not None:
            self.step_index = min(self.step_index + 1, len(self.procedure.waypoints) - 1)

    def prev_step(self) -> None:
        self.step_index = max(0, self.step_index - 1)

    @property
    def current_step(self) -> str:
        if self.procedure is None or not self.procedure.waypoints:
            return ""
        return self.procedure.waypoints[self.step_index].name
