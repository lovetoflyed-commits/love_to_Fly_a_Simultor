from __future__ import annotations

import math
import pygame

from ..models.position import Position


class Terrain:
    def __init__(self) -> None:
        self.obstacles = [
            (-23.44, -46.47, 3200),
            (33.942, -118.41, 500),
            (51.47, -0.44, 280),
        ]

    def get_elevation_ft(self, lat: float, lon: float) -> float:
        wave = 80.0 * math.sin(lat * 8.0) * math.cos(lon * 8.0)
        for obs_lat, obs_lon, elevation in self.obstacles:
            distance = math.hypot((lat - obs_lat) * 60.0, (lon - obs_lon) * 60.0)
            if distance < 1.0:
                return elevation
        return max(0.0, 120.0 + wave)

    def is_collision(self, position: Position) -> bool:
        return position.altitude_ft <= self.get_elevation_ft(position.latitude_deg, position.longitude_deg)

    def draw_map(self, surface: pygame.Surface, center_lat: float, center_lon: float, zoom: float) -> None:
        tile = 32
        for x in range(0, surface.get_width(), tile):
            for y in range(0, surface.get_height(), tile):
                lat = center_lat + (surface.get_height() / 2 - y) / (zoom * 600.0)
                lon = center_lon + (x - surface.get_width() / 2) / (zoom * 600.0)
                elevation = self.get_elevation_ft(lat, lon)
                if elevation < 150:
                    color = (35, 70, 35)
                elif elevation < 300:
                    color = (70, 95, 55)
                else:
                    color = (100, 100, 100)
                pygame.draw.rect(surface, color, pygame.Rect(x, y, tile, tile))
