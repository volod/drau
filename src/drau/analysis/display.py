"""Rich terminal output for detection analysis results."""

import math

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from drau.analysis.metrics import fmt, metrics, safe
from drau.settings.constants import DISPLAY_BAR_WIDTH


def _bar(v: float, width: int = DISPLAY_BAR_WIDTH) -> str:
    if math.isnan(v):
        return "░" * width + "   —   "
    filled = round(max(0.0, min(1.0, v)) * width)
    return "█" * filled + "░" * (width - filled) + f"  {v:.1%}"


def _table(console: Console, title: str, headers: list[str], rows: list[tuple]) -> None:
    t = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
    for i, h in enumerate(headers):
        t.add_column(h, justify="left" if i < 2 else "right")
    for row in rows:
        t.add_row(*[str(c) for c in row])
    console.print(t)
    console.print()


def print_tables(
    console: Console,
    mic_cols: list[str],
    overall: dict,
    by_grade: dict,
    by_class: dict,
    grades: list[tuple[float, float, str]],
) -> None:
    hdrs = ["Mic", "TP", "FP", "TN", "FN", "Accuracy", "Precision", "Recall", "F1", "FPR", "FNR"]
    rows = []
    for mic in mic_cols:
        m = metrics(overall[mic])
        rows.append((
            mic, m["tp"], m["fp"], m["tn"], m["fn"],
            fmt(m["accuracy"]), fmt(m["precision"]),
            fmt(m["recall"]),   fmt(m["f1"]),
            fmt(m["fpr"]),      fmt(m["fnr"]),
        ))
    _table(console, "Overall Detection Statistics", hdrs, rows)

    hdrs_d    = ["Mic", "Grade", "N", "TP", "FP", "TN", "FN", "Accuracy", "Recall", "FPR", "FNR"]
    grade_rows = []
    for mic in mic_cols:
        for _, _, gl in grades:
            counts = dict(by_grade[mic].get(gl, {}))
            if not any(counts.values()):
                continue
            m = metrics(counts)
            grade_rows.append((
                mic, gl, int(m["total"]),
                m["tp"], m["fp"], m["tn"], m["fn"],
                fmt(m["accuracy"]), fmt(m["recall"]),
                fmt(m["fpr"]),      fmt(m["fnr"]),
            ))
    if grade_rows:
        _table(console, "Statistics by Distance Grade", hdrs_d, grade_rows)

    hdrs_c    = ["Mic", "Class", "N", "TP", "FP", "TN", "FN", "Accuracy", "Recall", "FPR", "FNR"]
    class_rows = []
    for mic in mic_cols:
        for cls in ("drone", "non_drone"):
            counts = dict(by_class[mic].get(cls, {}))
            if not any(counts.values()):
                continue
            m = metrics(counts)
            class_rows.append((
                mic, cls, int(m["total"]),
                m["tp"], m["fp"], m["tn"], m["fn"],
                fmt(m["accuracy"]), fmt(m["recall"]),
                fmt(m["fpr"]),      fmt(m["fnr"]),
            ))
    if class_rows:
        _table(console, "Statistics by Sound Class", hdrs_c, class_rows)


def print_visual_summary(
    console: Console,
    mic_cols: list[str],
    overall: dict,
) -> None:
    BARS = [
        ("accuracy",  "Accuracy ", "green"),
        ("precision", "Precision", "cyan"),
        ("recall",    "Recall   ", "cyan"),
        ("f1",        "F1       ", "cyan"),
        ("fpr",       "FPR      ", "red"),
        ("fnr",       "FNR      ", "red"),
    ]
    lines = []
    for mic in mic_cols:
        m = metrics(overall[mic])
        lines.append(f"[bold]{mic}[/bold]  "
                     f"n={int(m['total'])}  "
                     f"TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']}")
        for key, label, color in BARS:
            lines.append(f"  {label}  [{color}]{_bar(m[key])}[/{color}]")
        lines.append("")

    console.print(Panel(
        "\n".join(lines).rstrip(),
        title="[bold yellow]Visual Summary[/bold yellow]",
        border_style="yellow",
    ))
    console.print()
