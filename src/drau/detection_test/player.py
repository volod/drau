"""Audio loading and distance-simulated playback."""

import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from drau.detection_test.calibrate import MIN_PLAYBACK_GAIN

# Normalize all source audio to this RMS level before applying distance gain.
_NORM_DBFS = -18.0


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Load a WAV file as a mono float32 array in [-1, 1]."""
    with wave.open(str(path)) as wf:
        sr           = wf.getframerate()
        raw          = wf.readframes(wf.getnframes())
        sample_width = wf.getsampwidth()
        n_channels   = wf.getnchannels()

    dtype   = np.int16 if sample_width == 2 else np.int32
    divisor = float(2 ** (sample_width * 8 - 1))
    audio   = np.frombuffer(raw, dtype=dtype).astype(np.float32) / divisor

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    return audio, sr


def rms_dbfs(audio: np.ndarray) -> float:
    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
    return 20.0 * np.log10(max(float(rms), 1e-10))


def play_at_distance(audio: np.ndarray, sr: int, distance_m: float, calibration) -> bool:
    """Normalise audio and play at volume simulating a drone at distance_m.

    Returns True when the raw inverse-distance gain fell below MIN_PLAYBACK_GAIN
    (i.e. the distance exceeded the speaker-calibration reliable range).
    """
    current_db     = rms_dbfs(audio)
    normalize_gain = 10.0 ** ((_NORM_DBFS - current_db) / 20.0)

    raw_gain    = calibration.ref_scale / max(float(distance_m), 1.0)
    was_clamped = raw_gain < MIN_PLAYBACK_GAIN
    gain        = float(np.clip(raw_gain, 0.0, 1.0))

    output = (audio * normalize_gain * gain).astype(np.float32)
    sd.play(output, sr, blocking=True)
    return was_clamped


def stop_playback() -> None:
    sd.stop()
