"""Random 50/50 sample selection from drone-audio and non-drone-audio directories."""

import random
import sqlite3
import wave
from dataclasses import dataclass
from pathlib import Path

from drau.data.analytics.store import DB_FILENAME as _ANALYTICS_DB


@dataclass
class Sample:
    path: Path
    label: str  # "drone" or "non_drone"


def _filter_by_duration(
    files: list[Path],
    label: str,
    audio_dir: Path,
    min_duration_s: float,
) -> list[Path]:
    db_path = audio_dir / _ANALYTICS_DB
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        eligible = {
            r[0] for r in conn.execute(
                "SELECT filename FROM audio_files WHERE label = ? AND duration_s >= ?",
                (label, min_duration_s),
            ).fetchall()
        }
        conn.close()
        return [f for f in files if f.name in eligible]

    result = []
    for f in files:
        with wave.open(str(f)) as wf:
            if (wf.getnframes() or 0) / wf.getframerate() >= min_duration_s:
                result.append(f)
    return result


def select_samples(
    audio_dir: Path,
    n: int,
    rng: random.Random,
    min_duration_s: float | None = None,
) -> list[Sample]:
    """Return n samples split ~50 % drone / 50 % non-drone, shuffled.

    If min_duration_s is set, only files meeting that threshold are candidates.
    """
    drone_files     = sorted((audio_dir / "drone-audio").glob("*.wav"))
    non_drone_files = sorted((audio_dir / "non-drone-audio").glob("*.wav"))

    if min_duration_s is not None:
        drone_files     = _filter_by_duration(drone_files,     "drone",     audio_dir, min_duration_s)
        non_drone_files = _filter_by_duration(non_drone_files, "non_drone", audio_dir, min_duration_s)

    if not drone_files:
        raise FileNotFoundError(f"No eligible drone WAV files in {audio_dir / 'drone-audio'}")
    if not non_drone_files:
        raise FileNotFoundError(f"No eligible non-drone WAV files in {audio_dir / 'non-drone-audio'}")

    n_drone     = (n + 1) // 2
    n_non_drone = n // 2

    chosen = (
        [Sample(path=p, label="drone")     for p in rng.sample(drone_files,     min(n_drone,     len(drone_files)))]
        + [Sample(path=p, label="non_drone") for p in rng.sample(non_drone_files, min(n_non_drone, len(non_drone_files)))]
    )
    rng.shuffle(chosen)
    return chosen[:n]
