"""Generate placeholder WAV sound files for the flight simulator sound system.

These are synthetic sounds made with numpy.  They are fully open/public-domain
and can be replaced with higher-fidelity recordings at any time.

Run:
    python /tmp/gen_sounds.py /path/to/assets/sounds/
"""
from __future__ import annotations

import sys
import wave
import struct
import math

SAMPLE_RATE = 44_100


def _to_int16(samples: list[float]) -> bytes:
    """Clip float samples to [-1, 1] and pack as signed 16-bit PCM."""
    out = []
    for s in samples:
        s = max(-1.0, min(1.0, s))
        out.append(int(s * 32_767))
    return struct.pack(f"<{len(out)}h", *out)


def save_wav(path: str, samples: list[float], channels: int = 1) -> None:
    with wave.open(path, "w") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(_to_int16(samples))
    print(f"  wrote {path}  ({len(samples)/SAMPLE_RATE:.2f}s)")


def sine(freq: float, duration: float, amp: float = 1.0, phase: float = 0.0) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    return [amp * math.sin(2 * math.pi * freq * i / SAMPLE_RATE + phase) for i in range(n)]


def noise(duration: float, amp: float = 0.5, seed: int = 42) -> list[float]:
    """Deterministic white noise (no numpy dependency)."""
    import random
    rng = random.Random(seed)
    n = int(SAMPLE_RATE * duration)
    return [amp * (2 * rng.random() - 1) for _ in range(n)]


def mix(*signals: list[float]) -> list[float]:
    length = min(len(s) for s in signals)
    return [sum(s[i] for s in signals) for i in range(length)]


def scale(signal: list[float], amp: float) -> list[float]:
    return [s * amp for s in signal]


def fade_in(signal: list[float], ms: float = 20.0) -> list[float]:
    fade_samples = int(SAMPLE_RATE * ms / 1000)
    result = list(signal)
    for i in range(min(fade_samples, len(result))):
        result[i] *= i / fade_samples
    return result


def fade_out(signal: list[float], ms: float = 20.0) -> list[float]:
    fade_samples = int(SAMPLE_RATE * ms / 1000)
    result = list(signal)
    n = len(result)
    for i in range(min(fade_samples, n)):
        result[n - 1 - i] *= i / fade_samples
    return result


def make_loopable(signal: list[float], crossfade_ms: float = 30.0) -> list[float]:
    """Crossfade the end into the beginning so the WAV loops seamlessly."""
    xf = int(SAMPLE_RATE * crossfade_ms / 1000)
    if xf * 2 >= len(signal):
        return signal
    result = list(signal)
    for i in range(xf):
        t = i / xf
        result[i] = result[i] * t + result[len(result) - xf + i] * (1.0 - t)
    # Zero-out tail that was blended in
    for i in range(xf):
        idx = len(result) - xf + i
        result[idx] = result[idx] * (1.0 - (i / xf))
    return result


def envelope(signal: list[float], attack_ms: float = 10.0, release_ms: float = 30.0) -> list[float]:
    return fade_out(fade_in(signal, attack_ms), release_ms)


def chirp(f0: float, f1: float, duration: float, amp: float = 0.7) -> list[float]:
    """Linear frequency sweep from f0 to f1."""
    n = int(SAMPLE_RATE * duration)
    result = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = f0 + (f1 - f0) * (i / n)
        phase = 2 * math.pi * freq * t
        result.append(amp * math.sin(phase))
    return result


def generate_engine_idle(path: str) -> None:
    """
    Loopable idle engine rumble (Lycoming O-235 @ ~700 RPM).
    Firing frequency ~23 Hz; we add harmonics at 46, 92, 138, 184 Hz
    plus band-limited noise for texture.
    Duration: 2 s (easily loops).
    """
    dur = 2.0
    # Harmonic stack of the 46 Hz fundamental (2×23) and above
    h1 = sine(46,  dur, 0.50)
    h2 = sine(92,  dur, 0.35)
    h3 = sine(138, dur, 0.22)
    h4 = sine(184, dur, 0.14)
    h5 = sine(230, dur, 0.08)
    # Subharmonic low thump
    sub = sine(23, dur, 0.30)
    # Narrow noise band for mechanical texture
    n1 = scale(noise(dur, 0.20, seed=1), 0.20)
    sig = mix(sub, h1, h2, h3, h4, h5, n1)
    # Normalise to ~0.6 peak
    pk = max(abs(s) for s in sig)
    if pk > 0:
        sig = scale(sig, 0.6 / pk)
    sig = make_loopable(sig, crossfade_ms=40)
    save_wav(path, sig)


def generate_engine_high(path: str) -> None:
    """
    Loopable high-power engine loop (approaching 2750 RPM).
    Fundamentals shifted up: ~91 Hz firing, harmonics 182, 273, 364 Hz.
    Duration: 2 s.
    """
    dur = 2.0
    h1 = sine(91,  dur, 0.45)
    h2 = sine(182, dur, 0.35)
    h3 = sine(273, dur, 0.25)
    h4 = sine(364, dur, 0.15)
    h5 = sine(455, dur, 0.08)
    n1 = scale(noise(dur, 0.25, seed=2), 0.25)
    sig = mix(h1, h2, h3, h4, h5, n1)
    pk = max(abs(s) for s in sig)
    if pk > 0:
        sig = scale(sig, 0.75 / pk)
    sig = make_loopable(sig, crossfade_ms=40)
    save_wav(path, sig)


def generate_engine_crank(path: str) -> None:
    """
    Starter-motor cranking sound (loopable, ~1.8 s).
    Electric motor whine + metallic engagement clicks.
    """
    dur = 1.8
    # Electric motor whine ~200 Hz + harmonic
    whine = mix(
        sine(200, dur, 0.40),
        sine(400, dur, 0.20),
        sine(600, dur, 0.10),
    )
    # Pulsed amplitude modulation at ~3 Hz to simulate engagement
    mod = [0.6 + 0.4 * math.sin(2 * math.pi * 3.0 * i / SAMPLE_RATE) for i in range(int(SAMPLE_RATE * dur))]
    whine_mod = [whine[i] * mod[i] for i in range(len(whine))]
    # Add broad noise for mechanical clatter
    n1 = scale(noise(dur, 0.30, seed=3), 0.30)
    # Metallic click at ~0.3 s intervals
    click_positions = [int(SAMPLE_RATE * 0.10), int(SAMPLE_RATE * 0.45),
                       int(SAMPLE_RATE * 0.80), int(SAMPLE_RATE * 1.15),
                       int(SAMPLE_RATE * 1.50)]
    click_width = int(SAMPLE_RATE * 0.008)  # 8 ms click
    n_samples = int(SAMPLE_RATE * dur)
    clicks = [0.0] * n_samples
    for pos in click_positions:
        for j in range(click_width):
            idx = pos + j
            if idx < n_samples:
                clicks[idx] = 0.5 * math.sin(2 * math.pi * 800 * j / SAMPLE_RATE) * (1.0 - j / click_width)

    sig = [whine_mod[i] + n1[i] + clicks[i] for i in range(n_samples)]
    pk = max(abs(s) for s in sig)
    if pk > 0:
        sig = scale(sig, 0.65 / pk)
    sig = make_loopable(sig, crossfade_ms=40)
    save_wav(path, sig)


def generate_throttle_up(path: str) -> None:
    """Short ascending chirp cue (0.25 s)."""
    dur = 0.25
    sig = chirp(120, 260, dur, amp=0.6)
    sig = envelope(sig, attack_ms=5, release_ms=50)
    save_wav(path, sig)


def generate_throttle_down(path: str) -> None:
    """Short descending chirp cue (0.25 s)."""
    dur = 0.25
    sig = chirp(260, 120, dur, amp=0.6)
    sig = envelope(sig, attack_ms=5, release_ms=50)
    save_wav(path, sig)


def generate_engine_shutdown(path: str) -> None:
    """
    Engine shutdown / mixture cutoff (2.5 s).
    Descending pitch from running RPM to silence.
    """
    dur = 2.5
    n = int(SAMPLE_RATE * dur)
    result = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = 184 * (1.0 - progress) + 23 * progress
        amp = (1.0 - progress) * 0.55
        result.append(amp * math.sin(2 * math.pi * freq * t))
    # Harmonic decay
    result2 = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq2 = 92 * (1.0 - progress) + 20 * progress
        amp2 = (1.0 - progress) * 0.30
        result2.append(amp2 * math.sin(2 * math.pi * freq2 * t))
    sig = [result[i] + result2[i] for i in range(n)]
    sig = fade_out(sig, ms=300)
    save_wav(path, sig)


def generate_alert_warning(path: str) -> None:
    """
    Double-beep warning (0.7 s total).
    Two 880 Hz beeps separated by silence, with sharp attack/release.
    """
    beep_dur = 0.12
    gap_dur  = 0.08
    tail_dur = 0.20

    beep1 = sine(880, beep_dur, 0.75)
    beep1 = envelope(beep1, attack_ms=5, release_ms=15)

    gap = [0.0] * int(SAMPLE_RATE * gap_dur)

    beep2 = sine(880, beep_dur, 0.75)
    beep2 = envelope(beep2, attack_ms=5, release_ms=15)

    tail = [0.0] * int(SAMPLE_RATE * tail_dur)

    sig = beep1 + gap + beep2 + tail
    save_wav(path, sig)


def main(out_dir: str) -> None:
    import os
    os.makedirs(out_dir, exist_ok=True)
    print(f"Generating placeholder WAV files in: {out_dir}")
    generate_engine_idle(      f"{out_dir}/engine_idle.wav")
    generate_engine_high(      f"{out_dir}/engine_high.wav")
    generate_engine_crank(     f"{out_dir}/engine_crank.wav")
    generate_throttle_up(      f"{out_dir}/throttle_up.wav")
    generate_throttle_down(    f"{out_dir}/throttle_down.wav")
    generate_engine_shutdown(  f"{out_dir}/engine_shutdown.wav")
    generate_alert_warning(    f"{out_dir}/alert_warning.wav")
    print("Done.")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    main(out)
