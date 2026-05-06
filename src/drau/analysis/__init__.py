"""Detection analysis subpackage — compute metrics and generate reports from session CSVs."""

import csv
from collections import defaultdict
from pathlib import Path

from rich.console import Console

from drau.analysis.display import print_tables, print_visual_summary
from drau.analysis.metrics import compute_grades, grade, outcome
from drau.analysis.plots import save_plots
from drau.analysis.report import write_report

__all__ = ["analyse"]


def analyse(csv_path: Path, console: Console) -> None:
    with open(csv_path, newline="") as f:
        reader     = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        mic_cols   = [c for c in fieldnames if c.startswith("mic_")]
        rows       = list(reader)

    if not rows:
        console.print("[red]CSV is empty.[/red]")
        return

    console.print(
        f"\n[bold]Session:[/bold] [cyan]{csv_path.name}[/cyan]  "
        f"[bold]Samples:[/bold] {len(rows)}\n"
    )

    max_dist = max(float(r["distance_m"]) for r in rows)
    grades   = compute_grades(max_dist)

    overall:  dict[str, dict[str, int]] = {m: defaultdict(int) for m in mic_cols}
    by_grade: dict[str, dict[str, dict[str, int]]] = {
        m: defaultdict(lambda: defaultdict(int)) for m in mic_cols
    }
    by_class: dict[str, dict[str, dict[str, int]]] = {
        m: defaultdict(lambda: defaultdict(int)) for m in mic_cols
    }

    for row in rows:
        label     = row["label"]
        grade_lbl = grade(float(row["distance_m"]), grades)
        for mic in mic_cols:
            result = row.get(mic, "")
            if not result:
                continue
            o = outcome(label, result)
            overall[mic][o]                 += 1
            by_grade[mic][grade_lbl][o]     += 1
            by_class[mic][label][o]         += 1

    print_tables(console, mic_cols, overall, by_grade, by_class, grades)
    print_visual_summary(console, mic_cols, overall)

    plots_dir = save_plots(csv_path, mic_cols, overall, by_grade, by_class, grades)
    console.print(f"[bold]Plots saved to:[/bold] [cyan]{plots_dir}/[/cyan]")

    report_path = write_report(csv_path, plots_dir, mic_cols, rows, overall, by_grade, by_class, grades)
    console.print(f"[bold]Report saved to:[/bold] [cyan]{report_path}[/cyan]\n")
