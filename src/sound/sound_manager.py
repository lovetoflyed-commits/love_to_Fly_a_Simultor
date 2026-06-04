"""Realistic sound manager for the flight simulator.

Hooks engine/throttle state to audio channels using pygame.mixer.
The system is fully fail-safe: if audio initialisation or any individual
sound file fails to load, the simulator continues running silently.

Audio channels
--------------
0 – ENGINE_IDLE  : low-RPM engine loop (looping, volume modulated)
1 – ENGINE_HIGH  : high-power engine loop (looping, volume modulated)
2 – TRANSIENT    : one-shot events (crank, shutdown, throttle cues)
3 – ALERT        : warning/alert beeps

Volume modulation (RPM bands)
------------------------------
At idle RPM  → idle channel full volume, high channel silent.
At max RPM   → idle channel ~10 % volume, high channel ~80 % volume.
Intermediate → linear crossfade proportional to normalised RPM.

Throttle events
---------------
A one-shot throttle-up or throttle-down cue fires whenever the throttle
moves more than THROTTLE_EVENT_THRESHOLD percent in a single frame.

Alert
-----
A double-beep repeats every ALERT_INTERVAL_S seconds while:
  • fuel_kg   < LOW_FUEL_KG  (approximately 2 gallons remaining), OR
  • oil_pressure_psi < LOW_OIL_PSI while the engine is running.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pygame

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public constants – useful if callers want to inspect/override thresholds.
# ---------------------------------------------------------------------------
LOW_FUEL_KG: float = 5.0          # ~2 US gallons
LOW_OIL_PSI: float = 20.0         # dangerously low oil pressure
ALERT_INTERVAL_S: float = 2.0     # seconds between alert beeps
THROTTLE_EVENT_THRESHOLD: float = 3.0  # % throttle change per-frame

# Engine RPM reference values (mirror Engine class constants)
_IDLE_RPM: float = 700.0
_MAX_RPM: float = 2750.0

# Channel indices
_CH_IDLE = 0
_CH_HIGH = 1
_CH_TRANSIENT = 2
_CH_ALERT = 3
_NUM_CHANNELS = 8

# Sound file names (relative to assets/sounds/)
_SOUND_FILES: dict[str, str] = {
    "crank":        "engine_crank.wav",
    "idle":         "engine_idle.wav",
    "high_power":   "engine_high.wav",
    "throttle_up":  "throttle_up.wav",
    "throttle_down": "throttle_down.wav",
    "shutdown":     "engine_shutdown.wav",
    "alert":        "alert_warning.wav",
}


class SoundManager:
    """Manages all audio playback for the flight simulator.

    Parameters
    ----------
    assets_dir:
        Path to the repository ``assets/`` directory.  Sound files are
        expected under ``assets/sounds/``.
    """

    # Internal engine-sound state machine
    _ENGINE_OFF = "off"
    _ENGINE_CRANKING = "cranking"
    _ENGINE_RUNNING = "running"

    def __init__(self, assets_dir: Path) -> None:
        self._available: bool = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._engine_state: str = self._ENGINE_OFF
        self._prev_throttle_pct: float = 0.0
        self._alert_timer: float = 0.0

        # Pygame mixer channels (assigned after successful init)
        self._ch_idle: Optional[pygame.mixer.Channel] = None
        self._ch_high: Optional[pygame.mixer.Channel] = None
        self._ch_transient: Optional[pygame.mixer.Channel] = None
        self._ch_alert: Optional[pygame.mixer.Channel] = None

        self._init_mixer(assets_dir / "sounds")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """True if audio was initialised successfully."""
        return self._available

    @property
    def engine_audio_state(self) -> str:
        """Current engine audio state: 'off', 'cranking', or 'running'."""
        return self._engine_state

    def update(self, state: dict, dt: float) -> None:
        """Drive audio playback from the current simulator state dict.

        Should be called once per simulation frame *after* all physics
        and state updates have been applied.

        Parameters
        ----------
        state:
            The simulator state dict (the same one passed to cockpit.update).
            Relevant keys:

            - ``engine_running``  (bool)
            - ``starter_engaged`` (bool)
            - ``throttle_pct``    (float, 0-100)
            - ``rpm``             (float)
            - ``fuel_kg``         (float)
            - ``max_fuel_kg``     (float)
            - ``oil_pressure_psi``(float)
            - ``master_on``       (bool)
            - ``mixture_pct``     (float)

        dt:
            Elapsed time since the last frame, in seconds.
        """
        if not self._available:
            return

        engine_running: bool = bool(state.get("engine_running", False))
        starter_engaged: bool = bool(state.get("starter_engaged", False))
        throttle_pct: float = float(state.get("throttle_pct", 0.0))
        rpm: float = float(state.get("rpm", 0.0))
        fuel_kg: float = float(state.get("fuel_kg", 100.0))
        oil_pressure_psi: float = float(state.get("oil_pressure_psi", 65.0))
        master_on: bool = bool(state.get("master_on", False))
        mixture_pct: float = float(state.get("mixture_pct", 100.0))

        # ------------------------------------------------------------------
        # Engine state machine
        # ------------------------------------------------------------------
        prev_state = self._engine_state

        if engine_running:
            if prev_state != self._ENGINE_RUNNING:
                self._on_engine_start()
        else:
            if prev_state == self._ENGINE_RUNNING:
                self._on_engine_stop()
            elif starter_engaged and master_on:
                if prev_state != self._ENGINE_CRANKING:
                    self._on_cranking_start()
            else:
                if prev_state == self._ENGINE_CRANKING:
                    self._on_cranking_stop()

        # ------------------------------------------------------------------
        # Continuous running-engine audio (volume crossfade by RPM)
        # ------------------------------------------------------------------
        if self._engine_state == self._ENGINE_RUNNING:
            self._update_running_volumes(rpm)

        # ------------------------------------------------------------------
        # Throttle-event one-shots (only while engine is running)
        # ------------------------------------------------------------------
        if self._engine_state == self._ENGINE_RUNNING:
            delta = throttle_pct - self._prev_throttle_pct
            if delta >= THROTTLE_EVENT_THRESHOLD:
                self._play_transient("throttle_up")
            elif delta <= -THROTTLE_EVENT_THRESHOLD:
                self._play_transient("throttle_down")

        # Mixture cutoff – hard stop before engine_running flag clears
        if (mixture_pct <= 5.0
                and self._engine_state == self._ENGINE_RUNNING
                and not engine_running):
            self._on_engine_stop()

        # ------------------------------------------------------------------
        # Alert / warning audio
        # ------------------------------------------------------------------
        low_fuel = 0.0 <= fuel_kg < LOW_FUEL_KG
        low_oil = engine_running and oil_pressure_psi < LOW_OIL_PSI
        alert_needed = low_fuel or low_oil

        if alert_needed:
            self._alert_timer += dt
            if self._alert_timer >= ALERT_INTERVAL_S:
                self._alert_timer = 0.0
                self._play_alert()
        else:
            self._alert_timer = 0.0

        # ------------------------------------------------------------------
        # Book-keeping
        # ------------------------------------------------------------------
        self._prev_throttle_pct = throttle_pct

    def shutdown(self) -> None:
        """Stop all channels cleanly.  Call before ``pygame.quit()``."""
        if self._available:
            pygame.mixer.stop()

    # ------------------------------------------------------------------
    # Engine state transitions
    # ------------------------------------------------------------------

    def _on_engine_start(self) -> None:
        """Engine transitions from cranking/off → running."""
        self._engine_state = self._ENGINE_RUNNING
        # Stop cranking sound if still playing
        if self._ch_transient and self._ch_transient.get_busy():
            self._ch_transient.stop()
        # Start both engine loops; volumes will be set by _update_running_volumes
        if "idle" in self._sounds and self._ch_idle:
            self._ch_idle.play(self._sounds["idle"], loops=-1)
            self._ch_idle.set_volume(0.6)
        if "high_power" in self._sounds and self._ch_high:
            self._ch_high.play(self._sounds["high_power"], loops=-1)
            self._ch_high.set_volume(0.0)
        log.debug("SoundManager: engine started")

    def _on_engine_stop(self) -> None:
        """Engine shuts down (mixture cutoff / fuel exhaustion / etc.)."""
        self._engine_state = self._ENGINE_OFF
        if self._ch_idle:
            self._ch_idle.stop()
        if self._ch_high:
            self._ch_high.stop()
        if "shutdown" in self._sounds and self._ch_transient:
            self._ch_transient.play(self._sounds["shutdown"])
        log.debug("SoundManager: engine stopped")

    def _on_cranking_start(self) -> None:
        """Starter motor engaged, engine not yet running."""
        self._engine_state = self._ENGINE_CRANKING
        if "crank" in self._sounds and self._ch_transient:
            self._ch_transient.play(self._sounds["crank"], loops=-1)
        log.debug("SoundManager: cranking started")

    def _on_cranking_stop(self) -> None:
        """Starter released without a successful start."""
        self._engine_state = self._ENGINE_OFF
        if self._ch_transient:
            self._ch_transient.stop()
        log.debug("SoundManager: cranking stopped (no start)")

    # ------------------------------------------------------------------
    # Continuous audio helpers
    # ------------------------------------------------------------------

    def _update_running_volumes(self, rpm: float) -> None:
        """Crossfade idle/high-power loops based on normalised RPM."""
        rpm_norm = max(0.0, min(1.0, (rpm - _IDLE_RPM) / (_MAX_RPM - _IDLE_RPM)))
        # Idle channel: 0.6 at idle RPM, fades to 0.10 at full power
        idle_vol = 0.10 + (1.0 - rpm_norm) * 0.50
        # High-power channel: 0.0 at idle, 0.80 at full power
        high_vol = rpm_norm * 0.80

        if self._ch_idle and self._ch_idle.get_busy():
            self._ch_idle.set_volume(max(0.0, min(1.0, idle_vol)))
        if self._ch_high and self._ch_high.get_busy():
            self._ch_high.set_volume(max(0.0, min(1.0, high_vol)))

    def _play_transient(self, key: str) -> None:
        """Play a one-shot sound if the transient channel is free."""
        if (key in self._sounds
                and self._ch_transient
                and not self._ch_transient.get_busy()):
            self._ch_transient.play(self._sounds[key])

    def _play_alert(self) -> None:
        """Play alert sound (does not interrupt an already-playing alert)."""
        if (self._ch_alert
                and "alert" in self._sounds
                and not self._ch_alert.get_busy()):
            self._ch_alert.play(self._sounds["alert"])

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_mixer(self, sounds_dir: Path) -> None:
        """Initialise pygame mixer and load sound assets.

        All errors are caught and logged; the SoundManager stays
        ``available=False`` if anything critical fails.
        """
        try:
            # Only initialise if not already done (main.py calls pygame.init).
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44_100, size=-16, channels=2, buffer=1_024)
        except Exception as exc:  # noqa: BLE001
            log.warning("SoundManager: pygame.mixer init failed – %s", exc)
            return

        pygame.mixer.set_num_channels(_NUM_CHANNELS)

        for key, filename in _SOUND_FILES.items():
            path = sounds_dir / filename
            if not path.exists():
                log.debug("SoundManager: asset not found – %s", path)
                continue
            try:
                self._sounds[key] = pygame.mixer.Sound(str(path))
            except Exception as exc:  # noqa: BLE001
                log.warning("SoundManager: could not load %s – %s", path, exc)

        if not self._sounds:
            log.info("SoundManager: no sound assets found; running silently")
            return

        try:
            self._ch_idle = pygame.mixer.Channel(_CH_IDLE)
            self._ch_high = pygame.mixer.Channel(_CH_HIGH)
            self._ch_transient = pygame.mixer.Channel(_CH_TRANSIENT)
            self._ch_alert = pygame.mixer.Channel(_CH_ALERT)
        except Exception as exc:  # noqa: BLE001
            log.warning("SoundManager: channel setup failed – %s", exc)
            return

        self._available = True
        log.info(
            "SoundManager: initialised with %d/%d sound(s)",
            len(self._sounds),
            len(_SOUND_FILES),
        )
