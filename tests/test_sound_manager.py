"""Tests for the SoundManager non-audio logic.

These tests exercise the state-machine and threshold logic without
requiring a working audio device.  pygame.mixer is not initialised so
all tests run cleanly in headless CI environments.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.sound.sound_manager import (
    SoundManager,
    LOW_FUEL_KG,
    LOW_OIL_PSI,
    ALERT_INTERVAL_S,
    THROTTLE_EVENT_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager(available: bool = False) -> SoundManager:
    """Return a SoundManager whose _available flag is set explicitly,
    bypassing real mixer initialisation."""
    with patch.object(SoundManager, "_init_mixer"):
        sm = SoundManager(Path("/nonexistent"))
        sm._available = available
    return sm


def _base_state(**overrides) -> dict:
    state = {
        "engine_running": False,
        "starter_engaged": False,
        "throttle_pct": 0.0,
        "rpm": 0.0,
        "fuel_kg": 50.0,
        "max_fuel_kg": 83.0,
        "oil_pressure_psi": 65.0,
        "master_on": False,
        "mixture_pct": 100.0,
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# Unavailable manager – should be a no-op
# ---------------------------------------------------------------------------

class TestUnavailableManager:
    def test_update_does_not_raise_when_unavailable(self):
        sm = _make_manager(available=False)
        sm.update(_base_state(), dt=0.016)  # must not raise

    def test_shutdown_does_not_raise_when_unavailable(self):
        sm = _make_manager(available=False)
        sm.shutdown()  # must not raise

    def test_available_is_false(self):
        sm = _make_manager(available=False)
        assert sm.available is False

    def test_engine_audio_state_starts_off(self):
        sm = _make_manager(available=False)
        assert sm.engine_audio_state == "off"


# ---------------------------------------------------------------------------
# Engine state machine (tested with a mocked-available manager)
# ---------------------------------------------------------------------------

def _mock_channels():
    """Return mock channel objects for patching."""
    ch = MagicMock()
    ch.get_busy.return_value = False
    return ch


class TestEngineStateMachine:
    def _sm_with_sounds(self) -> SoundManager:
        sm = _make_manager(available=True)
        # Provide mock Sound objects
        mock_sound = MagicMock()
        for key in ("crank", "idle", "high_power", "throttle_up", "throttle_down",
                    "shutdown", "alert"):
            sm._sounds[key] = mock_sound
        # Provide mock channels
        for attr in ("_ch_idle", "_ch_high", "_ch_transient", "_ch_alert"):
            ch = MagicMock()
            ch.get_busy.return_value = False
            setattr(sm, attr, ch)
        return sm

    def test_starts_in_off_state(self):
        sm = self._sm_with_sounds()
        assert sm.engine_audio_state == "off"

    def test_transitions_to_cranking_on_starter(self):
        sm = self._sm_with_sounds()
        state = _base_state(starter_engaged=True, master_on=True, engine_running=False)
        sm.update(state, dt=0.016)
        assert sm.engine_audio_state == "cranking"

    def test_transitions_to_running_when_engine_running(self):
        sm = self._sm_with_sounds()
        state = _base_state(engine_running=True, rpm=700.0)
        sm.update(state, dt=0.016)
        assert sm.engine_audio_state == "running"

    def test_transitions_to_off_when_engine_stops(self):
        sm = self._sm_with_sounds()
        # Start the engine
        sm.update(_base_state(engine_running=True, rpm=700.0), dt=0.016)
        assert sm.engine_audio_state == "running"
        # Stop the engine
        sm.update(_base_state(engine_running=False), dt=0.016)
        assert sm.engine_audio_state == "off"

    def test_cranking_to_running_transition(self):
        sm = self._sm_with_sounds()
        sm.update(_base_state(starter_engaged=True, master_on=True), dt=0.016)
        assert sm.engine_audio_state == "cranking"
        sm.update(_base_state(engine_running=True, rpm=700.0), dt=0.016)
        assert sm.engine_audio_state == "running"

    def test_cranking_stops_when_starter_released(self):
        sm = self._sm_with_sounds()
        sm.update(_base_state(starter_engaged=True, master_on=True), dt=0.016)
        assert sm.engine_audio_state == "cranking"
        sm.update(_base_state(starter_engaged=False, master_on=True), dt=0.016)
        assert sm.engine_audio_state == "off"

    def test_starter_without_master_does_not_crank(self):
        sm = self._sm_with_sounds()
        sm.update(_base_state(starter_engaged=True, master_on=False), dt=0.016)
        assert sm.engine_audio_state == "off"

    def test_engine_stop_plays_shutdown_sound(self):
        sm = self._sm_with_sounds()
        sm.update(_base_state(engine_running=True, rpm=700.0), dt=0.016)
        sm._ch_transient.play.reset_mock()
        sm.update(_base_state(engine_running=False), dt=0.016)
        sm._ch_transient.play.assert_called_once_with(sm._sounds["shutdown"])

    def test_engine_start_plays_idle_loop(self):
        sm = self._sm_with_sounds()
        sm.update(_base_state(engine_running=True, rpm=700.0), dt=0.016)
        sm._ch_idle.play.assert_called_once_with(sm._sounds["idle"], loops=-1)


# ---------------------------------------------------------------------------
# Throttle event thresholds
# ---------------------------------------------------------------------------

class TestThrottleEvents:
    def _sm_running(self) -> SoundManager:
        sm = _make_manager(available=True)
        mock_sound = MagicMock()
        for key in ("crank", "idle", "high_power", "throttle_up",
                    "throttle_down", "shutdown", "alert"):
            sm._sounds[key] = mock_sound
        for attr in ("_ch_idle", "_ch_high", "_ch_transient", "_ch_alert"):
            ch = MagicMock()
            ch.get_busy.return_value = False
            setattr(sm, attr, ch)
        sm._engine_state = "running"
        sm._prev_throttle_pct = 50.0
        return sm

    def test_throttle_up_fires_above_threshold(self):
        sm = self._sm_running()
        sm._ch_transient.get_busy.return_value = False
        sm.update(_base_state(engine_running=True, rpm=1200.0,
                               throttle_pct=50.0 + THROTTLE_EVENT_THRESHOLD + 1.0),
                  dt=0.016)
        sm._ch_transient.play.assert_called_with(sm._sounds["throttle_up"])

    def test_throttle_down_fires_above_threshold(self):
        sm = self._sm_running()
        sm._ch_transient.get_busy.return_value = False
        sm.update(_base_state(engine_running=True, rpm=1200.0,
                               throttle_pct=50.0 - THROTTLE_EVENT_THRESHOLD - 1.0),
                  dt=0.016)
        sm._ch_transient.play.assert_called_with(sm._sounds["throttle_down"])

    def test_small_throttle_change_does_not_fire(self):
        sm = self._sm_running()
        sm._ch_transient.get_busy.return_value = False
        sm.update(_base_state(engine_running=True, rpm=1200.0,
                               throttle_pct=50.0 + THROTTLE_EVENT_THRESHOLD - 1.0),
                  dt=0.016)
        sm._ch_transient.play.assert_not_called()

    def test_throttle_event_not_fired_when_engine_off(self):
        sm = _make_manager(available=True)
        mock_sound = MagicMock()
        for key in ("throttle_up", "throttle_down"):
            sm._sounds[key] = mock_sound
        for attr in ("_ch_idle", "_ch_high", "_ch_transient", "_ch_alert"):
            ch = MagicMock()
            ch.get_busy.return_value = False
            setattr(sm, attr, ch)
        sm._engine_state = "off"
        sm._prev_throttle_pct = 0.0
        sm.update(_base_state(throttle_pct=100.0), dt=0.016)
        sm._ch_transient.play.assert_not_called()


# ---------------------------------------------------------------------------
# Alert logic
# ---------------------------------------------------------------------------

class TestAlertLogic:
    def _sm(self) -> SoundManager:
        sm = _make_manager(available=True)
        mock_sound = MagicMock()
        for key in ("crank", "idle", "high_power", "throttle_up",
                    "throttle_down", "shutdown", "alert"):
            sm._sounds[key] = mock_sound
        for attr in ("_ch_idle", "_ch_high", "_ch_transient", "_ch_alert"):
            ch = MagicMock()
            ch.get_busy.return_value = False
            setattr(sm, attr, ch)
        return sm

    def test_alert_fires_when_timer_reaches_interval(self):
        sm = self._sm()
        sm._alert_timer = ALERT_INTERVAL_S - 0.001
        sm.update(_base_state(fuel_kg=LOW_FUEL_KG - 1.0), dt=0.1)
        sm._ch_alert.play.assert_called_once_with(sm._sounds["alert"])

    def test_alert_does_not_fire_before_interval(self):
        sm = self._sm()
        sm._alert_timer = 0.0
        sm.update(_base_state(fuel_kg=LOW_FUEL_KG - 1.0), dt=0.016)
        sm._ch_alert.play.assert_not_called()

    def test_alert_fires_for_low_oil_when_engine_running(self):
        sm = self._sm()
        sm._alert_timer = ALERT_INTERVAL_S - 0.001
        sm.update(_base_state(engine_running=True, rpm=700.0,
                               oil_pressure_psi=LOW_OIL_PSI - 1.0),
                  dt=0.1)
        sm._ch_alert.play.assert_called_once_with(sm._sounds["alert"])

    def test_alert_does_not_fire_for_low_oil_when_engine_off(self):
        sm = self._sm()
        sm._alert_timer = ALERT_INTERVAL_S - 0.001
        sm.update(_base_state(engine_running=False,
                               oil_pressure_psi=LOW_OIL_PSI - 1.0),
                  dt=0.1)
        sm._ch_alert.play.assert_not_called()

    def test_no_alert_when_conditions_normal(self):
        sm = self._sm()
        sm._alert_timer = ALERT_INTERVAL_S + 1.0
        sm.update(_base_state(fuel_kg=50.0, oil_pressure_psi=65.0), dt=0.1)
        sm._ch_alert.play.assert_not_called()

    def test_alert_timer_resets_after_fire(self):
        sm = self._sm()
        sm._alert_timer = ALERT_INTERVAL_S - 0.001
        sm.update(_base_state(fuel_kg=0.0), dt=0.1)
        assert sm._alert_timer == pytest.approx(0.0)

    def test_alert_timer_resets_when_condition_clears(self):
        sm = self._sm()
        sm._alert_timer = 1.5
        sm.update(_base_state(fuel_kg=50.0), dt=0.1)
        assert sm._alert_timer == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Volume crossfade
# ---------------------------------------------------------------------------

class TestVolumeCrossfade:
    def _sm_running(self) -> SoundManager:
        sm = _make_manager(available=True)
        mock_sound = MagicMock()
        for key in ("idle", "high_power"):
            sm._sounds[key] = mock_sound
        for attr in ("_ch_idle", "_ch_high", "_ch_transient", "_ch_alert"):
            ch = MagicMock()
            ch.get_busy.return_value = True
            setattr(sm, attr, ch)
        sm._engine_state = "running"
        return sm

    def test_idle_channel_louder_at_idle_rpm(self):
        sm = self._sm_running()
        sm._update_running_volumes(rpm=700.0)
        idle_vol = sm._ch_idle.set_volume.call_args[0][0]
        high_vol = sm._ch_high.set_volume.call_args[0][0]
        assert idle_vol > high_vol

    def test_high_channel_louder_at_max_rpm(self):
        sm = self._sm_running()
        sm._update_running_volumes(rpm=2750.0)
        idle_vol = sm._ch_idle.set_volume.call_args[0][0]
        high_vol = sm._ch_high.set_volume.call_args[0][0]
        assert high_vol > idle_vol

    def test_volumes_between_zero_and_one(self):
        sm = self._sm_running()
        for rpm in (700.0, 1000.0, 1500.0, 2000.0, 2750.0):
            sm._update_running_volumes(rpm=rpm)
            idle_vol = sm._ch_idle.set_volume.call_args[0][0]
            high_vol = sm._ch_high.set_volume.call_args[0][0]
            assert 0.0 <= idle_vol <= 1.0
            assert 0.0 <= high_vol <= 1.0

    def test_rpm_below_idle_clamps_correctly(self):
        sm = self._sm_running()
        sm._update_running_volumes(rpm=0.0)  # below idle RPM
        idle_vol = sm._ch_idle.set_volume.call_args[0][0]
        high_vol = sm._ch_high.set_volume.call_args[0][0]
        assert idle_vol >= 0.0
        assert high_vol == pytest.approx(0.0)
