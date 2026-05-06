"""Audio loading and distance-simulated playback.

Distance simulation applies two physical effects:

1. **Inverse-distance amplitude scaling** — gain = ref_scale / distance_m.
2. **Atmospheric air absorption (ISO 9613-1)** — high-frequency content attenuates
   faster than low-frequency content.  Implemented as a Hann-windowed sinc FIR
   lowpass whose cutoff is derived from the 4 kHz absorption coefficient
   (0.028 dB m⁻¹ at 20 °C, 70 % RH).  Applied for distances ≥ 10 m.
"""

import math
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from drau.settings.constants import (
    AIR_ABSORPTION_COEFF_4KHZ_DB_PER_M,
    AIR_ABSORPTION_FIR_TAPS,
    AIR_ABSORPTION_MIN_CUTOFF_HZ,
    AIR_ABSORPTION_MIN_DISTANCE_M,
    FEATURE_FRAME_SAMPLES,
    FEATURE_SILENCE_THRESHOLD_DBFS,
    LOG_EPSILON,
    PLAYBACK_NORM_DBFS,
    PLAYBACK_REFERENCE_DISTANCE_M,
)
from drau.detection_test.calibrate import Calibration


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
    return 20.0 * np.log10(max(float(rms), LOG_EPSILON))


def _air_absorption_cutoff_hz(distance_m: float, sr: int) -> float | None:
    """First-order lowpass cutoff matching ISO 9613-1 absorption at 4 kHz.

    Derived by equating the first-order LP attenuation at 4 kHz to the true
    atmospheric absorption: A = AIR_ABSORPTION_COEFF_4KHZ_DB_PER_M × distance.
    Solving for fc gives fc = 4000 / sqrt(10^(A/10) − 1).

    Returns None when the ideal cutoff is above sr × 0.45 — absorption is
    negligible at that distance, so no filtering is needed.
    """
    absorption_db = AIR_ABSORPTION_COEFF_4KHZ_DB_PER_M * distance_m
    denominator   = 10.0 ** (absorption_db / 10.0) - 1.0
    if denominator <= 0.0:
        return None
    fc = 4000.0 / math.sqrt(denominator)
    if fc >= sr * 0.45:
        return None     # ideal cutoff above Nyquist clamp — effect is inaudible
    return max(fc, AIR_ABSORPTION_MIN_CUTOFF_HZ)


def apply_air_absorption(audio: np.ndarray, sr: int, distance_m: float) -> np.ndarray:
    """Apply distance-dependent HF attenuation modelling atmospheric absorption.

    No-op for distances where the absorption is perceptually negligible (< 0.5 dB
    at 8 kHz, or below AIR_ABSORPTION_MIN_DISTANCE_M).  Otherwise the audio is
    convolved with a Hann-windowed sinc FIR lowpass whose cutoff decreases with
    distance, making distant sources sound progressively more muffled.
    """
    if distance_m < AIR_ABSORPTION_MIN_DISTANCE_M:
        return audio

    fc = _air_absorption_cutoff_hz(distance_m, sr)
    if fc is None:
        return audio

    fc_norm = fc / sr   # normalized to (0, 0.45]

    n = np.arange(AIR_ABSORPTION_FIR_TAPS, dtype=np.float64) - (AIR_ABSORPTION_FIR_TAPS - 1) / 2.0
    h = 2.0 * fc_norm * np.sinc(2.0 * fc_norm * n)
    h *= np.hanning(AIR_ABSORPTION_FIR_TAPS)
    h = (h / h.sum()).astype(np.float32)

    return np.convolve(audio, h, mode="same").astype(np.float32)


def trim_leading_silence(audio: np.ndarray) -> np.ndarray:
    """Return audio starting from the first frame whose RMS exceeds the silence threshold.

    Scans in FEATURE_FRAME_SAMPLES-sized steps; returns the original array unchanged
    if every frame is below the threshold (fully silent file).
    """
    threshold = 10.0 ** (FEATURE_SILENCE_THRESHOLD_DBFS / 20.0)
    n_frames  = len(audio) // FEATURE_FRAME_SAMPLES
    for i in range(n_frames):
        frame = audio[i * FEATURE_FRAME_SAMPLES : (i + 1) * FEATURE_FRAME_SAMPLES]
        if float(np.sqrt(np.mean(frame.astype(np.float64) ** 2))) > threshold:
            return audio[i * FEATURE_FRAME_SAMPLES:]
    return audio


def play_at_distance(audio: np.ndarray, sr: int, distance_m: float, calibration: Calibration) -> bool:
    """Normalise audio, apply air absorption and distance gain, then play.

    Returns True when the raw inverse-distance gain fell below calibration.min_gain
    (i.e. the distance exceeded the speaker's reliable range).
    """
    current_db     = rms_dbfs(audio)
    normalize_gain = 10.0 ** ((PLAYBACK_NORM_DBFS - current_db) / 20.0)
    normalized     = (audio * normalize_gain).astype(np.float32)

    # Frequency-dependent attenuation due to air absorption
    filtered = apply_air_absorption(normalized, sr, distance_m)

    raw_gain    = calibration.ref_scale / max(float(distance_m), PLAYBACK_REFERENCE_DISTANCE_M)
    was_clamped = raw_gain < calibration.min_gain
    gain        = float(np.clip(raw_gain, 0.0, 1.0))

    output = (filtered * gain).astype(np.float32)
    sd.play(output, sr, blocking=True)
    return was_clamped


def stop_playback() -> None:
    sd.stop()
