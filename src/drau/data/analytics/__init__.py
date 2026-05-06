"""Audio analytics subpackage — analyse WAV files and persist results to SQLite."""

from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from drau.data.analytics.features import AudioFeatures, analyse_file
from drau.data.analytics.report import REPORT_FILENAME, print_duration_stats, write_report
from drau.data.analytics.store import DB_FILENAME, _LABEL_SUBDIRS, insert, open_db, query_eligible_counts

__all__ = [
    "AudioFeatures",
    "analyse_file",
    "DB_FILENAME",
    "REPORT_FILENAME",
    "query_eligible_counts",
    "print_duration_stats",
    "run_analytics",
]


def run_analytics(audio_dir: Path, console: Console) -> Path:
    """Analyse all WAV files; store to SQLite; write text report. Returns DB path."""
    db_path = audio_dir / DB_FILENAME
    conn    = open_db(db_path)

    pending: list[tuple[Path, str]] = []
    for label, subdir in _LABEL_SUBDIRS.items():
        subdir_path = audio_dir / subdir
        if not subdir_path.is_dir():
            continue
        analysed = {
            r[0] for r in conn.execute(
                "SELECT filename FROM audio_files WHERE label = ?", (label,)
            ).fetchall()
        }
        for p in sorted(subdir_path.glob("*.wav")):
            if p.name not in analysed:
                pending.append((p, label))

    if not pending:
        console.print("[dim]Audio analytics: all files already analysed.[/dim]")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as bar:
            task = bar.add_task("Analysing audio files…", total=len(pending))
            for path, label in pending:
                insert(conn, analyse_file(path, label))
                bar.advance(task)
        conn.commit()
        console.print(f"[green]Analytics complete.[/green] DB → [cyan]{db_path}[/cyan]")

    report_path = audio_dir / REPORT_FILENAME
    write_report(conn, report_path, console)
    conn.close()
    return db_path
