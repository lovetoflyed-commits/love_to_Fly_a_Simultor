from __future__ import annotations

import math
import pygame

from .base_instrument import Instrument


class AttitudeIndicator(Instrument):
    """Attitude indicator (artificial horizon) for the Cessna 152.

    Sky half: rich blue gradient.
    Ground half: warm brown.
    Pitch ladder: lines at 5° intervals, major at 10°, with tick length distinction.
    Bank scale arc with tick marks at 10/20/30/45/60°.
    Yellow aircraft reference symbol.
    """

    def __init__(self, width: int = 220, height: int = 220) -> None:
        super().__init__(width, height)
        self.pitch_deg = 0.0
        self.roll_deg = 0.0

    def update(self, state: dict) -> None:
        self.pitch_deg = float(state.get("pitch_deg", 0.0))
        self.roll_deg = float(state.get("roll_deg", 0.0))

    def draw(self) -> pygame.Surface:
        self.surface.fill((0, 0, 0, 0))
        self._draw_circle_bg(self.surface, self.bg_color)
        radius = min(self.width, self.height) // 2 - 10
        cx = self.width / 2
        cy = self.height / 2
        center = (cx, cy)

        # ── Sky / ground horizon ball ────────────────────────────────────
        ball_w = radius * 3
        ball_h = radius * 3
        horizon = pygame.Surface((ball_w, ball_h), pygame.SRCALPHA)

        # Sky: vertical gradient from darker blue (top) to lighter (horizon)
        sky_top = (30, 90, 180)
        sky_bot = (95, 165, 230)
        half_h = ball_h // 2
        for row in range(half_h):
            t = row / max(1, half_h - 1)
            r = int(sky_top[0] + t * (sky_bot[0] - sky_top[0]))
            g = int(sky_top[1] + t * (sky_bot[1] - sky_top[1]))
            b = int(sky_top[2] + t * (sky_bot[2] - sky_top[2]))
            pygame.draw.line(horizon, (r, g, b), (0, row), (ball_w, row))

        # Ground: vertical gradient from warm brown (horizon) to darker
        gnd_top = (115, 75, 40)
        gnd_bot = (65, 45, 25)
        for row in range(half_h):
            t = row / max(1, half_h - 1)
            r = int(gnd_top[0] + t * (gnd_bot[0] - gnd_top[0]))
            g = int(gnd_top[1] + t * (gnd_bot[1] - gnd_top[1]))
            b = int(gnd_top[2] + t * (gnd_bot[2] - gnd_top[2]))
            pygame.draw.line(horizon, (r, g, b), (0, half_h + row), (ball_w, half_h + row))

        # Pitch offset (4 px per degree)
        pitch_offset = self.pitch_deg * 4.0

        # Horizon dividing line
        pygame.draw.line(
            horizon, (245, 245, 245),
            (0, half_h + int(pitch_offset)),
            (ball_w, half_h + int(pitch_offset)),
            3,
        )

        # Pitch ladder
        for pitch in range(-30, 35, 5):
            if pitch == 0:
                continue
            y = half_h + int(pitch_offset) - int(pitch * 4.0)
            major = pitch % 10 == 0
            half_len = 50 if major else 28
            lw = 2 if major else 1
            bx = ball_w // 2
            pygame.draw.line(
                horizon, (240, 240, 240),
                (bx - half_len, y), (bx + half_len, y), lw,
            )
            # Tick end caps on major lines
            if major:
                for side in (-1, 1):
                    pygame.draw.line(
                        horizon, (240, 240, 240),
                        (bx + side * half_len, y),
                        (bx + side * half_len, y + (6 if pitch < 0 else -6)),
                        lw,
                    )
            if major:
                txt = self.small_font.render(str(abs(pitch)), True, (255, 255, 255))
                horizon.blit(txt, (bx + half_len + 6, y - 6))
                horizon.blit(txt, (bx - half_len - txt.get_width() - 6, y - 6))

        # Rotate ball by roll angle
        rotated = self._rotate_surface(horizon, self.roll_deg)
        rect = rotated.get_rect(center=(cx, cy + pitch_offset))

        # Clip to instrument circle
        mask = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255), (int(cx), int(cy)), radius)
        temp = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        temp.blit(rotated, rect)
        temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.surface.blit(temp, (0, 0))

        # ── Bezel ring over the clipped ball ────────────────────────────
        pygame.draw.circle(self.surface, (60, 60, 60), (int(cx), int(cy)), radius, 2)

        # ── Bank scale arc and tick marks ────────────────────────────────
        arc_radius = radius - 8
        # Arc from 210° to 330° (above centre) – matches typical AI bank scale
        pygame.draw.arc(
            self.surface, (210, 210, 210),
            (int(cx) - arc_radius, int(cy) - arc_radius, arc_radius * 2, arc_radius * 2),
            math.radians(210), math.radians(330), 2,
        )
        for angle_deg in (10, 20, 30, 45, 60):
            for direction in (-1, 1):
                tick_angle = math.radians(270 - direction * angle_deg)
                inner_r = arc_radius - (12 if angle_deg % 30 == 0 else 7)
                ix = cx + math.cos(tick_angle) * inner_r
                iy = cy + math.sin(tick_angle) * inner_r
                ox = cx + math.cos(tick_angle) * arc_radius
                oy = cy + math.sin(tick_angle) * arc_radius
                pygame.draw.line(self.surface, (230, 230, 230), (ix, iy), (ox, oy), 2)

        # Bank pointer triangle (fixed, points up)
        pygame.draw.polygon(
            self.surface, (255, 210, 0),
            [(cx, cy - arc_radius - 2), (cx - 6, cy - arc_radius + 11), (cx + 6, cy - arc_radius + 11)],
        )

        # ── Aircraft reference symbol (yellow) ───────────────────────────
        # Wings
        pygame.draw.line(self.surface, (255, 210, 0), (int(cx) - 44, int(cy)), (int(cx) - 10, int(cy)), 5)
        pygame.draw.line(self.surface, (255, 210, 0), (int(cx) + 10, int(cy)), (int(cx) + 44, int(cy)), 5)
        # Wing-tips downturn
        pygame.draw.line(self.surface, (255, 210, 0), (int(cx) - 44, int(cy)), (int(cx) - 44, int(cy) + 8), 5)
        pygame.draw.line(self.surface, (255, 210, 0), (int(cx) + 44, int(cy)), (int(cx) + 44, int(cy) + 8), 5)
        # Centre dot/fuselage
        pygame.draw.circle(self.surface, (255, 210, 0), (int(cx), int(cy)), 5)
        pygame.draw.circle(self.surface, (0, 0, 0), (int(cx), int(cy)), 5, 1)

        return self.surface

