"""Text report generation and console eligibility output for audio analytics."""

import math
import sqlite3
from pathlib import Path

from rich.console import Console

from drau.data.analytics.store import query_eligible_counts

REPORT_FILENAME = "analytics_report.txt"


def _col_vals(conn: sqlite3.Connection, label: str, col: str) -> list[float]:
    return [r[0] for r in conn.execute(
        f"SELECT {col} FROM audio_files WHERE label = ?", (label,)
    ).fetchall()]


def _fmt_stat(vals: list[float], unit: str = "", fmt: str = ".2f") -> str:
    if not vals:
        return "no data"
    n   = len(vals)
    mn  = min(vals)
    mx  = max(vals)
    avg = sum(vals) / n
    std = math.sqrt(sum((v - avg) ** 2 for v in vals) / max(n - 1, 1))
    return (
        f"n={n}  min={mn:{fmt}}{unit}  max={mx:{fmt}}{unit}"
        f"  mean={avg:{fmt}}{unit}  std={std:{fmt}}{unit}"
    )


def write_report(conn: sqlite3.Connection, report_path: Path, console: Console) -> None:
    W = 72
    out: list[str] = []
    out.append("AUDIO DATASET ANALYTICS REPORT")
    out.append("=" * W)

    for label in ("drone", "non_drone"):
        total = conn.execute(
            "SELECT COUNT(*) FROM audio_files WHERE label = ?", (label,)
        ).fetchone()[0]
        heading = "DRONE" if label == "drone" else "NON-DRONE"
        out.append(f"\n{heading} FILES  ({total} total)")
        out.append("-" * W)

        for col, name, unit, fmt in [
            ("duration_s",            "Duration",             "s",     ".2f"),
            ("rms_dbfs",              "RMS level",            " dBFS", ".1f"),
            ("peak_dbfs",             "Peak level",           " dBFS", ".1f"),
            ("zcr",                   "Zero-crossing rate",   "",      ".4f"),
            ("spectral_centroid_hz",  "Spectral centroid",    " Hz",   ".0f"),
            ("spectral_bandwidth_hz", "Spectral bandwidth",   " Hz",   ".0f"),
            ("spectral_rolloff_hz",   "Spectral rolloff 85%", " Hz",   ".0f"),
            ("energy_low",            "Energy <500 Hz",       "",      ".3f"),
            ("energy_mid",            "Energy 500–4 kHz",     "",      ".3f"),
            ("energy_high",           "Energy >4 kHz",        "",      ".3f"),
            ("silence_ratio",         "Silence ratio",        "",      ".3f"),
        ]:
            vals = _col_vals(conn, label, col)
            out.append(f"  {name:<28} {_fmt_stat(vals, unit, fmt)}")

        out.append("\n  Duration distribution:")
        buckets: list[tuple[float, float]] = [
            (0, 1), (1, 2), (2, 3), (3, 5), (5, 10), (10, float("inf"))
        ]
        for lo, hi in buckets:
            if hi == float("inf"):
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM audio_files WHERE label=? AND duration_s>=?",
                    (label, lo),
                ).fetchone()[0]
                lbl = f"≥{lo:.0f}s"
            else:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM audio_files"
                    " WHERE label=? AND duration_s>=? AND duration_s<?",
                    (label, lo, hi),
                ).fetchone()[0]
                lbl = f"{lo:.0f}–{hi:.0f}s"
            pct = cnt / max(total, 1) * 100
            out.append(f"    {lbl:<8}  {cnt:>5}  {pct:5.1f}%  {'█' * int(pct / 2)}")

    out.append("\n" + "=" * W)
    report_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    console.print(f"Report → [cyan]{report_path}[/cyan]")


def print_duration_stats(audio_dir: Path, min_duration_s: float, console: Console) -> None:
    c = query_eligible_counts(audio_dir, min_duration_s)
    d_tot, d_el = c["drone_total"],     c["drone_eligible"]
    n_tot, n_el = c["non_drone_total"], c["non_drone_eligible"]
    tot,   el   = d_tot + n_tot,        d_el + n_el
    console.print(
        f"\n[bold]Audio file eligibility[/bold]"
        f" (min duration [cyan]{min_duration_s:.1f}s[/cyan]):\n"
        f"  Drone      {d_el:>5} / {d_tot:<6} ({d_el / max(d_tot, 1):.1%})\n"
        f"  Non-drone  {n_el:>5} / {n_tot:<6} ({n_el / max(n_tot, 1):.1%})\n"
        f"  Total      {el:>5} / {tot:<6} ({el / max(tot, 1):.1%})\n"
    )
