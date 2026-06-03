from __future__ import annotations

from abc import ABC, abstractmethod
import pygame


class Instrument(ABC):
    def __init__(self, width: int, height: int) -> None:
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.bg_color = pygame.Color("#2a2a2a")
        self.panel_color = pygame.Color("#1a1a1a")
        self.font = pygame.font.SysFont("arial", 16)
        self.small_font = pygame.font.SysFont("arial", 12)
        self.large_font = pygame.font.SysFont("arial", 26, bold=True)

    @abstractmethod
    def update(self, state: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(self) -> pygame.Surface:
        raise NotImplementedError

    def _draw_circle_bg(self, surface: pygame.Surface, color: tuple[int, int, int] | pygame.Color) -> None:
        radius = min(self.width, self.height) // 2 - 4
        center = (self.width // 2, self.height // 2)
        pygame.draw.circle(surface, self.panel_color, center, radius + 3)
        pygame.draw.circle(surface, color, center, radius)
        pygame.draw.circle(surface, (90, 90, 90), center, radius, 2)

    @staticmethod
    def _rotate_surface(surf: pygame.Surface, angle: float) -> pygame.Surface:
        return pygame.transform.rotozoom(surf, angle, 1.0)
