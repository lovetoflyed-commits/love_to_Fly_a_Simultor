from __future__ import annotations

import math
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
        self.bg_color = pygame.Color("#1e1e1e")
        self.panel_color = pygame.Color("#111111")
        self.font = pygame.font.SysFont("arial", 15)
        self.small_font = pygame.font.SysFont("arial", 11)
        self.large_font = pygame.font.SysFont("arial", 22, bold=True)

    @abstractmethod
    def update(self, state: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(self) -> pygame.Surface:
        raise NotImplementedError

    def _draw_circle_bg(
        self,
        surface: pygame.Surface,
        color: tuple[int, int, int] | pygame.Color,
    ) -> None:
        """Draw a realistic instrument bezel: outer chrome ring, inner face."""
        radius = min(self.width, self.height) // 2 - 4
        center = (self.width // 2, self.height // 2)

        # Shadow ring (darkest, outermost)
        pygame.draw.circle(surface, (15, 15, 15), center, radius + 4)

        # Outer chrome ring with gradient simulation (highlight top-left)
        for i in range(5, 0, -1):
            shade = 55 + i * 18
            pygame.draw.circle(surface, (shade, shade, shade), center, radius + i, 1)

        # Bezel inner ring (dark groove)
        pygame.draw.circle(surface, (20, 20, 20), center, radius + 1)

        # Instrument face
        pygame.draw.circle(surface, color, center, radius)

        # Inner bezel shadow at face edge
        pygame.draw.circle(surface, (0, 0, 0, 120), center, radius, 3)

        # Decorative screws at the four corners of the bezel
        r = radius + 2
        for angle_deg in (45, 135, 225, 315):
            a = math.radians(angle_deg)
            sx = int(center[0] + math.cos(a) * r)
            sy = int(center[1] + math.sin(a) * r)
            pygame.draw.circle(surface, (60, 60, 60), (sx, sy), 3)
            pygame.draw.circle(surface, (90, 90, 90), (sx, sy), 3, 1)
            # Cross slot on screw
            pygame.draw.line(surface, (100, 100, 100), (sx - 2, sy), (sx + 2, sy), 1)
            pygame.draw.line(surface, (100, 100, 100), (sx, sy - 2), (sx, sy + 2), 1)

    def _draw_needle(
        self,
        surface: pygame.Surface,
        center: tuple[float, float],
        angle_rad: float,
        length: float,
        width: int = 3,
        color: tuple[int, int, int] = (255, 255, 255),
        tail_length: float = 0.0,
        tail_color: tuple[int, int, int] | None = None,
    ) -> None:
        """Draw a tapered needle from center outward.

        The needle is drawn as a thin polygon tapering to a point for a more
        realistic look, with an optional short counterweight tail.
        """
        cx, cy = center
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Tip point
        tip_x = cx + cos_a * length
        tip_y = cy - sin_a * length

        # Base half-width
        hw = max(1.5, width / 2)

        # Perpendicular unit vector
        px = sin_a
        py = cos_a

        # Polygon: base-left, base-right, tip
        pts = [
            (cx - px * hw, cy - py * hw),
            (cx + px * hw, cy + py * hw),
            (tip_x, tip_y),
        ]
        pygame.draw.polygon(surface, color, pts)

        # Counterweight tail
        if tail_length > 0:
            tc = tail_color if tail_color is not None else color
            tail_x = cx - cos_a * tail_length
            tail_y = cy + sin_a * tail_length
            tw = max(1.5, hw * 0.7)
            tail_pts = [
                (cx - px * hw, cy - py * hw),
                (cx + px * hw, cy + py * hw),
                (tail_x + px * tw * 0.5, tail_y + py * tw * 0.5),
                (tail_x - px * tw * 0.5, tail_y - py * tw * 0.5),
            ]
            pygame.draw.polygon(surface, tc, tail_pts)

    def _draw_pivot_cap(
        self,
        surface: pygame.Surface,
        center: tuple[float, float],
        radius: int = 6,
        color: tuple[int, int, int] = (40, 40, 40),
    ) -> None:
        """Draw a centre pivot cap over needle roots."""
        cx, cy = int(center[0]), int(center[1])
        pygame.draw.circle(surface, (20, 20, 20), (cx, cy), radius + 2)
        pygame.draw.circle(surface, color, (cx, cy), radius)
        pygame.draw.circle(surface, (120, 120, 120), (cx, cy), radius, 1)
        # Highlight dot
        pygame.draw.circle(surface, (160, 160, 160), (cx - 1, cy - 1), max(1, radius // 3))

    @staticmethod
    def _rotate_surface(surf: pygame.Surface, angle: float) -> pygame.Surface:
        return pygame.transform.rotozoom(surf, angle, 1.0)
