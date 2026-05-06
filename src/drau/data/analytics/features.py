"""Acoustic feature extraction for WAV files — pure computation, no I/O side effects."""

import math
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_ANALYSIS_SECONDS       = 5
_FRAME_SAMPLES          = 512
_SILENCE_THRESHOLD_DBFS = -40.0
_LOW_HZ                 = 500
_HIGH_HZ                = 4_000


@dataclass
class AudioFeatures:
    filename:             str
    label:                str
    duration_s:           float
    rms_dbfs:             float
    peak_dbfs:            float
    zcr:                  float
    spectral_centroid_hz: float
    spectral_bandwidth_hz:float
    spectral_rolloff_hz:  float
    energy_low:           float
    energy_mid:           float
    energy_high:          float
    silence_ratio:        float


def _load_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as wf:
        sr           = wf.getframerate()
        raw          = wf.readframes(wf.getnframes())
        sample_width = wf.getsampwidth()
        n_channels   = wf.getnchannels()
    dtype = np.int16 if sample_width == 2 else np.int32
    audio = np.frombuffer(raw, dtype=dtype).astype(np.float32) / float(2 ** (sample_width * 8 - 1))
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)
    return audio, sr


def analyse_file(path: Path, label: str) -> AudioFeatures:
    """Extract acoustic features from a WAV file."""
    audio, sr = _load_wav(path)
    n = len(audio)

    rms64     = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    rms_dbfs  = 20.0 * math.log10(max(rms64, 1e-10))
    peak_dbfs = 20.0 * math.log10(max(float(np.abs(audio).max()), 1e-10))
    zcr       = float(np.mean(np.abs(np.diff(np.sign(audio))) / 2))

    win_n    = min(n, sr * _ANALYSIS_SECONDS)
    chunk    = audio[:win_n].astype(np.float64)
    spectrum = np.abs(np.fft.rfft(chunk * np.hanning(win_n)))
    freqs    = np.fft.rfftfreq(win_n, 1.0 / sr)
    power    = spectrum ** 2
    total_p  = float(power.sum())

    if total_p > 0:
        cent = float((freqs * power).sum() / total_p)
        bw   = float(np.sqrt((power * (freqs - cent) ** 2).sum() / total_p))
        cum  = np.cumsum(power)
        ri   = min(int(np.searchsorted(cum, 0.85 * total_p)), len(freqs) - 1)
        roll = float(freqs[ri])
        e_lo = float(power[freqs < _LOW_HZ].sum()                           / total_p)
        e_mi = float(power[(freqs >= _LOW_HZ) & (freqs < _HIGH_HZ)].sum()  / total_p)
        e_hi = float(power[freqs >= _HIGH_HZ].sum()                         / total_p)
    else:
        cent = bw = roll = e_lo = e_mi = e_hi = 0.0

    n_frames = n // _FRAME_SAMPLES
    if n_frames > 0:
        frames    = audio[:n_frames * _FRAME_SAMPLES].reshape(n_frames, _FRAME_SAMPLES)
        frame_rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
        thresh    = 10.0 ** (_SILENCE_THRESHOLD_DBFS / 20.0)
        sil_ratio = float((frame_rms < thresh).mean())
    else:
        sil_ratio = 0.0

    return AudioFeatures(
        filename              = path.name,
        label                 = label,
        duration_s            = n / sr,
        rms_dbfs              = rms_dbfs,
        peak_dbfs             = peak_dbfs,
        zcr                   = zcr,
        spectral_centroid_hz  = cent,
        spectral_bandwidth_hz = bw,
        spectral_rolloff_hz   = roll,
        energy_low            = e_lo,
        energy_mid            = e_mi,
        energy_high           = e_hi,
        silence_ratio         = sil_ratio,
    )
