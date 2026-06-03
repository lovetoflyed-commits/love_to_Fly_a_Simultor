from __future__ import annotations

import pygame


class MainMenu:
    """Pre-flight main menu: aircraft selection and scenario selection."""

    _BG = (14, 18, 30)
    _ACCENT = (60, 130, 200)
    _TEXT = (220, 230, 255)
    _HIGHLIGHT = (255, 220, 80)
    _MUTED = (120, 130, 150)
    _ITEM_H = 48
    _PANEL_W = 480

    _AIRCRAFT_OPTIONS = [
        ("C152",  "Cessna 152  (80 kts cruise, IFR trainer)"),
        ("C172",  "Cessna 172  (110 kts cruise, touring)"),
        ("PA28",  "Piper PA-28 Archer  (120 kts cruise)"),
        ("B737",  "Boeing 737-800  (450 kts cruise, airliner)"),
    ]

    _SCENARIO_OPTIONS = [
        ("ILS_APPROACH",        "ILS 10R SBGR approach"),
        ("MISSED_APPROACH",     "Missed approach & go-around"),
        ("HOLDING_PATTERN",     "Holding pattern – partial panel"),
        ("ENGINE_FAILURE_SCENARIO", "Engine failure & diversion"),
        ("PARTIAL_PANEL",       "Partial panel recovery"),
        ("DIVERSION",           "Weather diversion to SBSP"),
    ]

    def __init__(self, screen_w: int, screen_h: int) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._title_font = pygame.font.SysFont("arial", 36, bold=True)
        self._sub_font = pygame.font.SysFont("arial", 18, bold=True)
        self._item_font = pygame.font.SysFont("arial", 16)
        self._small_font = pygame.font.SysFont("arial", 13)
        self._aircraft_idx = 0
        self._scenario_idx = 0
        self._focus = "aircraft"  # "aircraft" | "scenario" | "start"
        self.done = False
        self.selected_aircraft = "C152"
        self.selected_scenario = "ILS_APPROACH"

    # ── Public ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if self._focus == "aircraft":
            if event.key in (pygame.K_UP, pygame.K_w):
                self._aircraft_idx = (self._aircraft_idx - 1) % len(self._AIRCRAFT_OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._aircraft_idx = (self._aircraft_idx + 1) % len(self._AIRCRAFT_OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                self._focus = "scenario"
        elif self._focus == "scenario":
            if event.key in (pygame.K_UP, pygame.K_w):
                self._scenario_idx = (self._scenario_idx - 1) % len(self._SCENARIO_OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._scenario_idx = (self._scenario_idx + 1) % len(self._SCENARIO_OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                self._focus = "start"
            elif event.key == pygame.K_BACKSPACE:
                self._focus = "aircraft"
        elif self._focus == "start":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.selected_aircraft = self._AIRCRAFT_OPTIONS[self._aircraft_idx][0]
                self.selected_scenario = self._SCENARIO_OPTIONS[self._scenario_idx][0]
                self.done = True
            elif event.key == pygame.K_BACKSPACE:
                self._focus = "scenario"

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self._BG)
        self._draw_title(surface)
        cx = self.screen_w // 2
        # Aircraft column
        self._draw_section(
            surface,
            label="SELECT AIRCRAFT",
            items=[d for _, d in self._AIRCRAFT_OPTIONS],
            selected=self._aircraft_idx,
            active=self._focus == "aircraft",
            x=cx - self._PANEL_W - 10,
            y=130,
        )
        # Scenario column
        self._draw_section(
            surface,
            label="SELECT SCENARIO",
            items=[d for _, d in self._SCENARIO_OPTIONS],
            selected=self._scenario_idx,
            active=self._focus == "scenario",
            x=cx + 10,
            y=130,
        )
        self._draw_start_button(surface)
        self._draw_hint(surface)

    # ── Private ───────────────────────────────────────────────────────────────

    def _draw_title(self, surface: pygame.Surface) -> None:
        title = self._title_font.render("✈  love to Fly — IFR Simulator", True, self._TEXT)
        sub = self._small_font.render("Phase 2 · Advanced IFR Training", True, self._MUTED)
        surface.blit(title, title.get_rect(center=(self.screen_w // 2, 50)))
        surface.blit(sub, sub.get_rect(center=(self.screen_w // 2, 90)))
        pygame.draw.line(surface, self._ACCENT, (80, 110), (self.screen_w - 80, 110), 1)

    def _draw_section(
        self,
        surface: pygame.Surface,
        label: str,
        items: list[str],
        selected: int,
        active: bool,
        x: int,
        y: int,
    ) -> None:
        panel_h = self._ITEM_H * len(items) + 44
        border_color = self._ACCENT if active else (60, 65, 80)
        pygame.draw.rect(surface, (22, 28, 44), (x, y, self._PANEL_W, panel_h), border_radius=8)
        pygame.draw.rect(surface, border_color, (x, y, self._PANEL_W, panel_h), 2, border_radius=8)
        lbl = self._sub_font.render(label, True, self._ACCENT if active else self._MUTED)
        surface.blit(lbl, (x + 14, y + 10))
        for i, text in enumerate(items):
            iy = y + 44 + i * self._ITEM_H
            if i == selected:
                pygame.draw.rect(surface, (40, 70, 120), (x + 4, iy, self._PANEL_W - 8, self._ITEM_H - 4), border_radius=4)
                color = self._HIGHLIGHT
            else:
                color = self._TEXT
            t = self._item_font.render(text, True, color)
            surface.blit(t, (x + 14, iy + (self._ITEM_H - t.get_height()) // 2))

    def _draw_start_button(self, surface: pygame.Surface) -> None:
        cx = self.screen_w // 2
        by = self.screen_h - 90
        color = (60, 180, 80) if self._focus == "start" else (40, 80, 50)
        border = (100, 230, 120) if self._focus == "start" else (60, 100, 70)
        pygame.draw.rect(surface, color, (cx - 110, by, 220, 48), border_radius=8)
        pygame.draw.rect(surface, border, (cx - 110, by, 220, 48), 2, border_radius=8)
        label = "▶  START FLIGHT" if self._focus != "start" else "[ ENTER ] FLY"
        t = self._sub_font.render(label, True, (240, 255, 240))
        surface.blit(t, t.get_rect(center=(cx, by + 24)))

    def _draw_hint(self, surface: pygame.Surface) -> None:
        hints = {
            "aircraft": "↑↓ choose aircraft  ·  ENTER / TAB to confirm",
            "scenario": "↑↓ choose scenario  ·  ENTER / TAB to confirm  ·  BACKSPACE back",
            "start":    "ENTER to fly  ·  BACKSPACE back",
        }
        hint_text = hints.get(self._focus, "")
        t = self._small_font.render(hint_text, True, self._MUTED)
        surface.blit(t, t.get_rect(center=(self.screen_w // 2, self.screen_h - 22)))
