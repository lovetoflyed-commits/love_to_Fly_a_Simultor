# Flight Simulator – Sound Assets

This directory contains the audio files used by the simulator's sound
system (`src/sound/sound_manager.py`).

---

## Included placeholder files

All files shipped in this repository are **procedurally generated**
synthetic sounds (pure Python, no external tools).  They are
public-domain and provide immediate, functional audio feedback while
giving you a clear target for higher-fidelity replacements.

| File | Duration | Description |
|------|----------|-------------|
| `engine_idle.wav`     | 2.0 s loop | Low-RPM engine rumble (700 RPM, ~46 Hz fundamental + harmonics) |
| `engine_high.wav`     | 2.0 s loop | High-power engine loop (approaching 2750 RPM, ~91 Hz fundamental) |
| `engine_crank.wav`    | 1.8 s loop | Starter-motor cranking + engagement clicks |
| `throttle_up.wav`     | 0.25 s    | Ascending pitch cue – throttle increasing |
| `throttle_down.wav`   | 0.25 s    | Descending pitch cue – throttle decreasing |
| `engine_shutdown.wav` | 2.5 s     | Descending engine-off sound (mixture cutoff / fuel exhaustion) |
| `alert_warning.wav`   | 0.5 s     | Double-beep cockpit alert (low fuel / low oil pressure) |

---

## How the sound system uses these files

```
engine_idle.wav  ──── Channel 0 (loop, volume ∝ low RPM)
engine_high.wav  ──── Channel 1 (loop, volume ∝ high RPM / throttle)
engine_crank.wav ──┐
throttle_up.wav  ──┤─ Channel 2 (one-shot transients)
throttle_down.wav──┤
engine_shutdown.wav┘
alert_warning.wav ── Channel 3 (timed repeating alert)
```

Volume crossfade:
- At **idle RPM (700)** → Channel 0 at ~60 %, Channel 1 silent.
- At **max RPM (2750)** → Channel 0 at ~10 %, Channel 1 at ~80 %.
- Intermediate RPM → linear interpolation between the two extremes.

Alerts fire once every **2 seconds** while:
- Fuel remaining < 5 kg (~2 US gallons), **or**
- Oil pressure < 20 psi while the engine is running.

---

## Replacing placeholders with higher-fidelity recordings

1. **Format**: WAV (recommended) or OGG Vorbis.  Mono is fine; stereo
   works too.  Sample rate 44 100 Hz, 16-bit PCM.
2. **Loop points**: `engine_idle.wav` and `engine_high.wav` are looped
   continuously.  Make sure the waveform has identical amplitude /
   phase at the start and end to avoid clicks.  Audio editors such as
   Audacity can set loop points manually.
3. **Normalisation**: Target a peak of roughly −3 dBFS.  The sound
   manager applies its own gain via `Channel.set_volume()`, so
   over-normalised clips will still sound correct.
4. **Sources for realistic recordings** (check licensing carefully):
   - [Freesound.org](https://freesound.org) – search "Lycoming O-235",
     "Cessna 152 engine", "aircraft starter".  Many files are
     CC0 or CC-BY.
   - [ZapSplat](https://www.zapsplat.com) – free with attribution.
   - Record your own with a field recorder or phone at a local airfield.
5. **File naming**: Keep the same filenames as the placeholders, or
   update `_SOUND_FILES` in `src/sound/sound_manager.py`.

---

## Regenerating the placeholder files

```bash
python tools/generate_placeholder_sounds.py assets/sounds/
```

The script uses only Python standard library + `math`/`random` –
no extra dependencies required.
