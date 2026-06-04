from __future__ import annotations

import math
from dataclasses import dataclass
import pygame

from ..models.position import Position

# ── Terrain constants ─────────────────────────────────────────────────────────
# São Paulo plateau base elevation (ft MSL) – below all airports in the area
# so collision-detection stays correct when on the ground.
_SP_PLATEAU_FT = 2400.0

# Gaussian hill peaks: (center_lat, center_lon, peak_ft, radius_deg)
# Radii are kept tight (~0.05-0.08°, ≈3-5 NM) so each hill only affects
# its immediate vicinity and does not raise the plateau around the airports.
# Hill centres are positioned at the real peak locations.
_HILLS: list[tuple[float, float, float, float]] = [
    # Serra da Cantareira – dense forest/mountain N of São Paulo
    (-23.280, -46.520, 3937.0, 0.06),
    # Pico do Jaraguá – highest point within the city of São Paulo
    (-23.459, -46.762, 3724.0, 0.05),
    # Serra do Japi – mountain range W of São Paulo (Jundiaí area)
    (-23.215, -47.050, 3740.0, 0.08),
    # Serra do Mar southern ridge – coastal range SE of the plateau
    (-23.800, -46.300, 4200.0, 0.10),
    # Pico do Papagaio (Serra do Japi eastern spur)
    (-23.290, -46.840, 3600.0, 0.06),
]


@dataclass
class TerrainObject:
    """A named terrain feature or obstacle visible on the map and from the cockpit."""
    name: str
    lat: float
    lon: float
    base_elevation_ft: float   # terrain elevation at the base (ft MSL)
    height_ft: float           # structure height above terrain (0 for natural peaks)
    object_type: str           # "hill" | "tower" | "building" | "water_tower"

    @property
    def top_elevation_ft(self) -> float:
        return self.base_elevation_ft + self.height_ft


class Terrain:
    """Terrain model for the SBGR (São Paulo/Guarulhos) operating area.

    Elevation is based on real topography of the São Paulo plateau:
    – plateau base at ~2400 ft MSL (below all local airports)
    – Serra da Cantareira and Pico do Jaraguá mountain peaks to the NW
    – Serra do Mar coastal range to the SE
    Individual Gaussian hill contributions use the *maximum* (not sum) so
    overlapping ridges do not artificially inflate the plateau elevation.
    """

    # Named terrain objects derived from Google Maps / aerial photography of the
    # SBGR / São Paulo metropolitan area.
    OBJECTS: list[TerrainObject] = [
        # Natural peaks / ridges
        TerrainObject("Serra da Cantareira", -23.280, -46.520, 3937.0, 0.0, "hill"),
        TerrainObject("Pico do Jaraguá",     -23.459, -46.762, 3724.0, 0.0, "hill"),
        TerrainObject("Serra do Japi",        -23.215, -47.050, 3740.0, 0.0, "hill"),
        TerrainObject("Serra do Mar (ridge)", -23.800, -46.300, 4200.0, 0.0, "hill"),
        # Telecommunication / broadcast towers
        TerrainObject("Torres Pico Jaraguá", -23.460, -46.765, 3724.0, 230.0, "tower"),
        TerrainObject("Torre Cantareira TV", -23.270, -46.515, 3800.0, 180.0, "tower"),
        TerrainObject("Antena SBMT",         -23.510, -46.640, 2450.0, 150.0, "tower"),
        # Industrial / urban landmarks visible from SBGR final approach
        TerrainObject("Complexo Embraer",    -23.420, -46.470, 2475.0, 60.0,  "building"),
        TerrainObject("Terminal SBGR Norte", -23.430, -46.480, 2459.0, 50.0,  "building"),
        TerrainObject("Refinaria RECAP",     -23.580, -46.430, 2600.0, 70.0,  "building"),
        TerrainObject("Caixa d'Água GRU",    -23.470, -46.530, 2500.0, 90.0,  "water_tower"),
    ]

    def __init__(self) -> None:
        pass

    # ── Elevation query ───────────────────────────────────────────────────────

    def get_elevation_ft(self, lat: float, lon: float) -> float:
        """Return terrain elevation in feet MSL for the given coordinate.

        Uses the plateau base plus the *maximum* single Gaussian hill contribution
        at the queried point to avoid artificial inflation from overlapping ridges.
        """
        max_contrib = 0.0
        for h_lat, h_lon, h_peak, h_radius in _HILLS:
            dist_deg = math.hypot(lat - h_lat, lon - h_lon)
            contrib = (h_peak - _SP_PLATEAU_FT) * math.exp(-0.5 * (dist_deg / h_radius) ** 2)
            if contrib > max_contrib:
                max_contrib = contrib
        return max(0.0, _SP_PLATEAU_FT + max_contrib)

    def is_collision(self, position: Position) -> bool:
        return position.altitude_ft <= self.get_elevation_ft(position.latitude_deg, position.longitude_deg)

    # ── Object lookup ─────────────────────────────────────────────────────────

    def get_objects_in_range(self, lat: float, lon: float, range_nm: float = 30.0) -> list[TerrainObject]:
        """Return terrain objects within *range_nm* nautical miles of the given position."""
        result = []
        cos_lat = math.cos(math.radians(lat))
        nm_per_deg_lat = 60.0
        nm_per_deg_lon = 60.0 * cos_lat
        for obj in self.OBJECTS:
            d_nm = math.hypot(
                (obj.lat - lat) * nm_per_deg_lat,
                (obj.lon - lon) * nm_per_deg_lon,
            )
            if d_nm <= range_nm:
                result.append(obj)
        return result

    # ── Map rendering ─────────────────────────────────────────────────────────

    def draw_map(self, surface: pygame.Surface, center_lat: float, center_lon: float, zoom: float) -> None:
        """Render a top-down terrain colour map onto *surface*."""
        tile = 32
        font = pygame.font.SysFont("arial", 9) if pygame.font.get_init() else None
        W, H = surface.get_width(), surface.get_height()
        for x in range(0, W, tile):
            for y in range(0, H, tile):
                lat = center_lat + (H / 2 - y) / (zoom * 600.0)
                lon = center_lon + (x - W / 2) / (zoom * 600.0)
                elevation = self.get_elevation_ft(lat, lon)
                if elevation < 2450:
                    color = (40, 120, 40)       # low ground / valleys
                elif elevation < 2700:
                    color = (70, 110, 55)        # plateau level
                elif elevation < 3200:
                    color = (110, 100, 60)       # foothills
                elif elevation < 3700:
                    color = (140, 120, 80)       # lower slopes
                else:
                    color = (160, 145, 130)      # peaks / high ridges
                pygame.draw.rect(surface, color, pygame.Rect(x, y, tile, tile))

        # Draw named terrain objects as icons
        if font:
            for obj in self.OBJECTS:
                px = int(W / 2 + (obj.lon - center_lon) * zoom * 600.0)
                py = int(H / 2 - (obj.lat - center_lat) * zoom * 600.0)
                if 0 <= px < W and 0 <= py < H:
                    if obj.object_type == "hill":
                        color = (200, 160, 100)
                        pygame.draw.polygon(surface, color, [(px, py - 7), (px - 6, py + 4), (px + 6, py + 4)])
                    elif obj.object_type == "tower":
                        pygame.draw.line(surface, (255, 80, 80), (px, py - 8), (px, py + 4), 2)
                        pygame.draw.line(surface, (255, 80, 80), (px - 4, py - 2), (px + 4, py - 2), 1)
                    elif obj.object_type in ("building", "water_tower"):
                        pygame.draw.rect(surface, (180, 180, 100), pygame.Rect(px - 3, py - 3, 6, 6))
                    label = font.render(obj.name, True, (240, 240, 240))
                    surface.blit(label, (px + 8, py - 5))


@dataclass
class TerrainObject:
    """A named terrain feature or obstacle visible on the map and from the cockpit."""
    name: str
    lat: float
    lon: float
    base_elevation_ft: float   # terrain elevation at the base (MSL)
    height_ft: float           # structure height above terrain (0 for natural peaks)
    object_type: str           # "hill" | "tower" | "building" | "water_tower"

    @property
    def top_elevation_ft(self) -> float:
        return self.base_elevation_ft + self.height_ft


class Terrain:
    """Terrain model for the SBGR (São Paulo/Guarulhos) operating area.

    Elevation is based on real topography of the São Paulo plateau:
    – flat plateau at ~2600 ft MSL
    – Serra da Cantareira and Pico do Jaraguá mountain ridges to the NW
    – Serra do Mar coastal range to the SE
    – Tietê River valley cuts a shallow trough through the urban area
    """

    # Named terrain objects derived from Google Maps / aerial photography of the
    # SBGR / São Paulo metropolitan area.
    OBJECTS: list[TerrainObject] = [
        # Natural peaks / ridges
        TerrainObject("Serra da Cantareira", -23.350, -46.550, 3937.0, 0.0, "hill"),
        TerrainObject("Pico do Jaraguá",     -23.459, -46.762, 3724.0, 0.0, "hill"),
        TerrainObject("Serra do Japi",        -23.225, -47.000, 3740.0, 0.0, "hill"),
        TerrainObject("Serra do Mar (ridge)", -23.750, -46.300, 4200.0, 0.0, "hill"),
        # Telecommunication / broadcast towers
        TerrainObject("Torres Pico Jaraguá", -23.460, -46.765, 3724.0, 230.0, "tower"),
        TerrainObject("Torre Cantareira TV", -23.340, -46.535, 3800.0, 180.0, "tower"),
        TerrainObject("Antena SBMT",         -23.510, -46.640, 2450.0, 150.0, "tower"),
        # Industrial / urban landmarks visible from SBGR final approach
        TerrainObject("Complexo Embraer",    -23.420, -46.470, 2475.0, 60.0,  "building"),
        TerrainObject("Terminal SBGR Norte", -23.430, -46.480, 2459.0, 50.0,  "building"),
        TerrainObject("Refinaria RECAP",     -23.580, -46.430, 2600.0, 70.0,  "building"),
        TerrainObject("Caixa d'Água GRU",    -23.470, -46.530, 2600.0, 90.0,  "water_tower"),
    ]

    def __init__(self) -> None:
        pass

    # ── Elevation query ───────────────────────────────────────────────────────

    def get_elevation_ft(self, lat: float, lon: float) -> float:
        """Return terrain elevation in feet MSL for the given coordinate.

        Uses a superposition of Gaussian hills over the São Paulo plateau base.
        """
        elev = _SP_PLATEAU_FT
        for h_lat, h_lon, h_peak, h_radius in _HILLS:
            dist_deg = math.hypot(lat - h_lat, lon - h_lon)
            # Gaussian hill: adds (peak - base) * exp(-0.5*(dist/radius)^2)
            contribution = (h_peak - _SP_PLATEAU_FT) * math.exp(-0.5 * (dist_deg / h_radius) ** 2)
            if contribution > 0:
                elev += contribution
            else:
                # Valleys (negative contribution from Tietê etc.) lower the plateau
                elev += contribution
        return max(0.0, elev)

    def is_collision(self, position: Position) -> bool:
        return position.altitude_ft <= self.get_elevation_ft(position.latitude_deg, position.longitude_deg)

    # ── Object lookup ─────────────────────────────────────────────────────────

    def get_objects_in_range(self, lat: float, lon: float, range_nm: float = 30.0) -> list[TerrainObject]:
        """Return terrain objects within *range_nm* nautical miles of the given position."""
        result = []
        cos_lat = math.cos(math.radians(lat))
        nm_per_deg_lat = 60.0
        nm_per_deg_lon = 60.0 * cos_lat
        for obj in self.OBJECTS:
            d_nm = math.hypot(
                (obj.lat - lat) * nm_per_deg_lat,
                (obj.lon - lon) * nm_per_deg_lon,
            )
            if d_nm <= range_nm:
                result.append(obj)
        return result

    # ── Map rendering ─────────────────────────────────────────────────────────

    def draw_map(self, surface: pygame.Surface, center_lat: float, center_lon: float, zoom: float) -> None:
        """Render a top-down terrain colour map onto *surface*."""
        tile = 32
        font = pygame.font.SysFont("arial", 9) if pygame.font.get_init() else None
        W, H = surface.get_width(), surface.get_height()
        for x in range(0, W, tile):
            for y in range(0, H, tile):
                lat = center_lat + (H / 2 - y) / (zoom * 600.0)
                lon = center_lon + (x - W / 2) / (zoom * 600.0)
                elevation = self.get_elevation_ft(lat, lon)
                if elevation < 2450:
                    color = (40, 120, 40)       # low ground / valleys
                elif elevation < 2700:
                    color = (70, 110, 55)        # plateau level
                elif elevation < 3200:
                    color = (110, 100, 60)       # foothills
                elif elevation < 3700:
                    color = (140, 120, 80)       # lower slopes
                else:
                    color = (160, 145, 130)      # peaks / high ridges
                pygame.draw.rect(surface, color, pygame.Rect(x, y, tile, tile))

        # Draw named terrain objects as icons
        if font:
            for obj in self.OBJECTS:
                px = int(W / 2 + (obj.lon - center_lon) * zoom * 600.0)
                py = int(H / 2 - (obj.lat - center_lat) * zoom * 600.0)
                if 0 <= px < W and 0 <= py < H:
                    if obj.object_type == "hill":
                        color = (200, 160, 100)
                        pygame.draw.polygon(surface, color, [(px, py - 7), (px - 6, py + 4), (px + 6, py + 4)])
                    elif obj.object_type == "tower":
                        pygame.draw.line(surface, (255, 80, 80), (px, py - 8), (px, py + 4), 2)
                        pygame.draw.line(surface, (255, 80, 80), (px - 4, py - 2), (px + 4, py - 2), 1)
                    elif obj.object_type in ("building", "water_tower"):
                        pygame.draw.rect(surface, (180, 180, 100), pygame.Rect(px - 3, py - 3, 6, 6))
                    label = font.render(obj.name, True, (240, 240, 240))
                    surface.blit(label, (px + 8, py - 5))
