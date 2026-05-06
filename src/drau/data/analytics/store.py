"""SQLite persistence and eligibility queries for audio analytics."""

import sqlite3
import wave
from datetime import datetime, timezone
from pathlib import Path

from drau.data.analytics.features import AudioFeatures

DB_FILENAME    = "analytics.db"
_LABEL_SUBDIRS = {"drone": "drone-audio", "non_drone": "non-drone-audio"}


def open_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audio_files (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            filename              TEXT    NOT NULL,
            label                 TEXT    NOT NULL,
            duration_s            REAL    NOT NULL,
            rms_dbfs              REAL    NOT NULL,
            peak_dbfs             REAL    NOT NULL,
            zcr                   REAL    NOT NULL,
            spectral_centroid_hz  REAL    NOT NULL,
            spectral_bandwidth_hz REAL    NOT NULL,
            spectral_rolloff_hz   REAL    NOT NULL,
            energy_low            REAL    NOT NULL,
            energy_mid            REAL    NOT NULL,
            energy_high           REAL    NOT NULL,
            silence_ratio         REAL    NOT NULL,
            analyzed_at           TEXT    NOT NULL,
            UNIQUE(filename, label)
        )
    """)
    conn.commit()
    return conn


def insert(conn: sqlite3.Connection, feat: AudioFeatures) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO audio_files
           (filename, label, duration_s, rms_dbfs, peak_dbfs, zcr,
            spectral_centroid_hz, spectral_bandwidth_hz, spectral_rolloff_hz,
            energy_low, energy_mid, energy_high, silence_ratio, analyzed_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (feat.filename, feat.label, feat.duration_s, feat.rms_dbfs, feat.peak_dbfs, feat.zcr,
         feat.spectral_centroid_hz, feat.spectral_bandwidth_hz, feat.spectral_rolloff_hz,
         feat.energy_low, feat.energy_mid, feat.energy_high, feat.silence_ratio,
         datetime.now(timezone.utc).isoformat()),
    )


def query_eligible_counts(audio_dir: Path, min_duration_s: float) -> dict[str, int]:
    """Return per-label totals and eligible counts; uses DB if present, else WAV headers."""
    db_path = audio_dir / DB_FILENAME
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        result: dict[str, int] = {}
        for label in ("drone", "non_drone"):
            row = conn.execute(
                """SELECT COUNT(*),
                          SUM(CASE WHEN duration_s >= ? THEN 1 ELSE 0 END)
                   FROM audio_files WHERE label = ?""",
                (min_duration_s, label),
            ).fetchone()
            result[f"{label}_total"]    = row[0] or 0
            result[f"{label}_eligible"] = row[1] or 0
        conn.close()
        return result

    result = {}
    for label, subdir in _LABEL_SUBDIRS.items():
        files = sorted((audio_dir / subdir).glob("*.wav"))
        eligible = 0
        for f in files:
            with wave.open(str(f)) as wf:
                if (wf.getnframes() or 0) / wf.getframerate() >= min_duration_s:
                    eligible += 1
        result[f"{label}_total"]    = len(files)
        result[f"{label}_eligible"] = eligible
    return result
