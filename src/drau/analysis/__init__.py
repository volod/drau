"""Detection analysis subpackage — compute metrics and generate reports from session CSVs."""

import csv
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.rule import Rule

from drau.analysis.display import print_tables, print_visual_summary
from drau.analysis.metrics import compute_grades, grade, outcome
from drau.analysis.plots import save_plots
from drau.analysis.report import write_report

__all__ = ["analyse"]


def _aggregate(
    rows: list[dict],
    mic_cols: list[str],
    grades: list[tuple[float, float, str]],
) -> tuple[dict, dict, dict]:
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
            overall[mic][o]             += 1
            by_grade[mic][grade_lbl][o] += 1
            by_class[mic][label][o]     += 1
    return overall, by_grade, by_class


def analyse(csv_path: Path, console: Console) -> None:
    with open(csv_path, newline="") as f:
        reader     = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        mic_cols   = [c for c in fieldnames if c.startswith("mic_")]
        rows       = list(reader)

    if not rows:
        console.print("[red]CSV is empty.[/red]")
        return

    any_beyond  = any(r.get("beyond_detect_max") == "true" for r in rows)
    rows_in     = [r for r in rows if r.get("beyond_detect_max") != "true"] if any_beyond else rows
    rows_beyond = [r for r in rows if r.get("beyond_detect_max") == "true"] if any_beyond else []

    max_dist_in = max(float(r["distance_m"]) for r in rows_in) if rows_in else 1.0
    grades_in   = compute_grades(max_dist_in)
    overall_in, by_grade_in, by_class_in = _aggregate(rows_in, mic_cols, grades_in)

    detect_max = rows[0].get("mic_detect_max_m", "?")
    console.print(
        f"\n[bold]Session:[/bold] [cyan]{csv_path.name}[/cyan]  "
        f"[bold]Samples:[/bold] {len(rows)}"
        + (f"  [bold]Detection range:[/bold] ≤ {detect_max} m" if any_beyond else "")
        + "\n"
    )

    if any_beyond:
        console.print(Rule(
            f"Within Detection Range  ≤ {detect_max} m  ({len(rows_in)} samples)",
            style="bold green",
        ))
    print_tables(console, mic_cols, overall_in, by_grade_in, by_class_in, grades_in)
    print_visual_summary(console, mic_cols, overall_in)

    beyond_data = None
    if rows_beyond:
        max_dist_bey = max(float(r["distance_m"]) for r in rows_beyond)
        grades_bey   = compute_grades(max_dist_bey)
        overall_bey, by_grade_bey, by_class_bey = _aggregate(rows_beyond, mic_cols, grades_bey)

        console.print(Rule(
            f"Beyond Detection Range  > {detect_max} m  ({len(rows_beyond)} samples)",
            style="bold yellow",
        ))
        console.print(
            "[dim]False negatives here are expected — drone was beyond rated range.\n"
            "True positives indicate detection beyond rated range.[/dim]\n"
        )
        print_tables(console, mic_cols, overall_bey, by_grade_bey, by_class_bey, grades_bey)
        print_visual_summary(console, mic_cols, overall_bey)

        beyond_data = {
            "overall":  overall_bey,
            "by_grade": by_grade_bey,
            "by_class": by_class_bey,
            "grades":   grades_bey,
            "rows":     rows_beyond,
        }

    plots_dir = save_plots(
        csv_path, mic_cols, overall_in, by_grade_in, by_class_in, grades_in,
        subdir="in_range" if any_beyond else None,
    )
    console.print(f"[bold]Plots saved to:[/bold] [cyan]{plots_dir}/[/cyan]")

    if beyond_data:
        plots_dir_bey = save_plots(
            csv_path, mic_cols,
            beyond_data["overall"], beyond_data["by_grade"], beyond_data["by_class"],
            beyond_data["grades"],
            subdir="beyond_range",
        )
        console.print(f"[bold]Beyond-range plots:[/bold] [cyan]{plots_dir_bey}/[/cyan]")

    report_path = write_report(
        csv_path, plots_dir, mic_cols, rows,
        overall_in, by_grade_in, by_class_in, grades_in,
        beyond_data=beyond_data,
    )
    console.print(f"[bold]Report saved to:[/bold] [cyan]{report_path}[/cyan]\n")
