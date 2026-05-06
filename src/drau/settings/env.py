"""Environment variable helpers.

This module centralizes configuration and `.env` loading.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    hf_token: Optional[str]

    # ── Audio duration filters ─────────────────────────────────────────────
    audio_duration_min_s: Optional[float]   # Exclude samples shorter than this (None = no filter)
    audio_duration_max_s: float             # Clip samples longer than this

    # ── Detection test defaults ────────────────────────────────────────────
    detection_reliable_range_m: float   # Distance beyond which a warning is shown
    mic_detect_max_m: float             # Distance beyond which detection is not expected
    detection_audio_dir: str
    detection_output_dir: str

    # ── Data pipeline defaults ─────────────────────────────────────────────
    data_cache_dir: str
    data_audio_dir: str


def load_env(repo_root: Optional[Path] = None) -> None:
    """Loads environment variables from a `.env` file if present.

    Args:
        repo_root: Optional explicit repository root (directory containing `.env`).
    """
    if repo_root is not None:
        env_path = repo_root / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
        return

    env_path_str = find_dotenv(filename=".env", usecwd=True)
    if env_path_str:
        load_dotenv(dotenv_path=env_path_str, override=False)


def get_settings() -> Settings:
    """Builds Settings from process environment."""
    hf_token = os.environ.get("HF_TOKEN") or None

    raw_dur_min = os.environ.get("AUDIO_DURATION_MIN")
    audio_duration_min_s = float(raw_dur_min) if raw_dur_min else None

    audio_duration_max_s = float(os.environ.get("AUDIO_DURATION_MAX") or "30.0")

    detection_reliable_range_m = float(
        os.environ.get("DETECTION_RELIABLE_RANGE_M") or "100.0"
    )
    mic_detect_max_m = float(
        os.environ.get("MIC_DETECT_MAX_M") or "100.0"
    )

    detection_audio_dir = (
        os.environ.get("DETECTION_AUDIO_DIR")
        or ".data/drone-audio-detection-samples/audio"
    )
    detection_output_dir = (
        os.environ.get("DETECTION_OUTPUT_DIR")
        or ".data/detection-tests"
    )

    data_cache_dir = (
        os.environ.get("DATA_CACHE_DIR")
        or ".data/drone-audio-detection-samples"
    )
    data_audio_dir = (
        os.environ.get("DATA_AUDIO_DIR")
        or ".data/drone-audio-detection-samples/audio"
    )

    return Settings(
        hf_token=hf_token,
        audio_duration_min_s=audio_duration_min_s,
        audio_duration_max_s=audio_duration_max_s,
        detection_reliable_range_m=detection_reliable_range_m,
        mic_detect_max_m=mic_detect_max_m,
        detection_audio_dir=detection_audio_dir,
        detection_output_dir=detection_output_dir,
        data_cache_dir=data_cache_dir,
        data_audio_dir=data_audio_dir,
    )
