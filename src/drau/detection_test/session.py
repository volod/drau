"""Detection test session orchestration."""

import csv
import random
from datetime import datetime
from pathlib import Path

from rich.console import Console

from drau.data.analytics import print_duration_stats, query_eligible_counts
from drau.detection_test.calibrate import calibrate
from drau.detection_test.form import collect_results, show_sample
from drau.detection_test.player import load_audio, play_at_distance, rms_dbfs, stop_playback
from drau.detection_test.sampler import select_samples
from drau.env import load_env

_MAX_AUDIO_DURATION_S = 30.0


def run(
    samples_num: int,
    mic_num: int,
    dist_max: float,
    audio_dir: Path,
    output_dir: Path,
    min_duration_s: float | None = None,
    reliable_range: float = 100.0,
) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    load_env(repo_root=repo_root)

    console = Console()
    rng     = random.Random()
    output_dir.mkdir(parents=True, exist_ok=True)

    if min_duration_s is not None:
        counts = query_eligible_counts(audio_dir, min_duration_s)
        total_eligible = counts["drone_eligible"] + counts["non_drone_eligible"]
        if total_eligible < samples_num * 0.5:
            console.print(
                f"\n[bold red]Insufficient eligible samples.[/bold red] "
                f"Only [cyan]{total_eligible}[/cyan] file(s) are ≥ [cyan]{min_duration_s:.1f}s[/cyan], "
                f"which is less than 50 % of the [cyan]{samples_num}[/cyan] requested.\n"
                f"Run [bold]make cache-data[/bold] to analyse the dataset, "
                f"or lower [bold]--audio-duration-min[/bold]."
            )
            print_duration_stats(audio_dir, min_duration_s, console)
            return 1

    calibration = calibrate(console)

    console.print(f"Selecting {samples_num} samples (50 % drone / 50 % non-drone)…")
    samples = select_samples(audio_dir, samples_num, rng, min_duration_s=min_duration_s)

    session_id  = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path    = output_dir / f"session_{session_id}.csv"
    mic_columns = [f"mic_{i}" for i in range(1, mic_num + 1)]
    fieldnames  = [
        "session_id", "timestamp", "sample_num", "filename",
        "label", "distance_m", "rms_dbfs",
    ] + mic_columns

    samples_written = 0
    try:
        with open(csv_path, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for idx, sample in enumerate(samples, 1):
                distance   = rng.uniform(1.0, dist_max)
                audio, sr  = load_audio(sample.path)
                max_samples = int(sr * _MAX_AUDIO_DURATION_S)
                audio       = audio[:max_samples]
                sample_rms = rms_dbfs(audio)
                duration_s = len(audio) / sr

                def _replay(d: float, _a=audio, _s=sr) -> bool:
                    return play_at_distance(_a, _s, d, calibration)

                def _refresh_panel(d: float, w: str | None) -> None:
                    console.clear()
                    show_sample(
                        console,
                        idx,
                        len(samples),
                        sample.label,
                        d,
                        sample.path.name,
                        duration_s=duration_s,
                        warning=w,
                    )

                warning = None
                if distance > reliable_range:
                    warning = (
                        f"⚠ beyond reliable range "
                        f"(≤ {reliable_range:.0f} m) "
                        f"— volume at minimum"
                    )

                console.clear()
                show_sample(
                    console,
                    idx,
                    len(samples),
                    sample.label,
                    distance,
                    sample.path.name,
                    duration_s=duration_s,
                    warning=warning,
                )

                _replay(distance)

                mic_results, final_distance = collect_results(
                    console=console,
                    mic_num=mic_num,
                    replay_fn=_replay,
                    initial_distance=distance,
                    max_reliable_distance=reliable_range,
                    refresh_panel_fn=_refresh_panel,
                )

                row: dict = {
                    "session_id": session_id,
                    "timestamp":  datetime.now().isoformat(),
                    "sample_num": idx,
                    "filename":   sample.path.name,
                    "label":      sample.label,
                    "distance_m": round(final_distance, 2),
                    "rms_dbfs":   round(sample_rms, 2),
                }
                for i, result in enumerate(mic_results, 1):
                    row[f"mic_{i}"] = result
                writer.writerow(row)
                samples_written += 1
                csv_file.flush()

    except KeyboardInterrupt:
        stop_playback()
        print()
        if samples_written == 0:
            csv_path.unlink(missing_ok=True)
            console.print("[yellow]Session interrupted. No samples recorded.[/yellow]")
        else:
            console.print(
                f"[yellow]Session interrupted.[/yellow] "
                f"{samples_written} sample(s) saved → [cyan]{csv_path}[/cyan]"
            )
        return 130

    console.print(
        f"\n[bold green]Session complete.[/bold green] "
        f"Results → [cyan]{csv_path}[/cyan]"
    )
    return 0
