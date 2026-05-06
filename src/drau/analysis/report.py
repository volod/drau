"""Text report generation and mic interpretation for detection analysis."""

import math
import textwrap
from pathlib import Path

from drau.analysis.metrics import fmt, metrics, safe
from drau.settings.constants import (
    INTERP_HIGH_ERROR_RATE,
    INTERP_MODERATE_ACCURACY_MIN,
    INTERP_RELIABLE_ACCURACY_MIN,
    INTERP_STABLE_GRADE_DELTA,
    INTERP_STRONG_ACCURACY_MIN,
    INTERP_STRONG_FPR_MAX,
    INTERP_STRONG_RECALL_MIN,
    REPORT_WIDTH_DETECTION,
)


def _interpret_mic(
    mic: str,
    m: dict,
    mic_by_grade: dict,
    grades: list[tuple[float, float, str]],
) -> list[str]:
    """Return 2–4 sentences summarising one mic's results."""
    grade_labels = [gl for _, _, gl in grades]

    acc    = safe(m["accuracy"])
    recall = safe(m["recall"])
    fpr    = safe(m["fpr"])
    q = (
        "strong"   if acc >= INTERP_STRONG_ACCURACY_MIN and recall >= INTERP_STRONG_RECALL_MIN and fpr <= INTERP_STRONG_FPR_MAX
        else "moderate" if acc >= INTERP_MODERATE_ACCURACY_MIN
        else "weak"
    )
    sentences = [
        f"Overall performance is {q}: "
        f"accuracy {fmt(m['accuracy'])}, recall {fmt(m['recall'])}, FPR {fmt(m['fpr'])}."
    ]

    grade_accs = []
    for gl in grade_labels:
        c = dict(mic_by_grade.get(gl, {}))
        if sum(c.values()) == 0:
            continue
        grade_accs.append((gl, safe(metrics(c)["accuracy"])))

    if len(grade_accs) >= 2:
        first_gl, first_acc = grade_accs[0]
        last_gl,  last_acc  = grade_accs[-1]
        delta = last_acc - first_acc
        if delta < -INTERP_STABLE_GRADE_DELTA:
            sentences.append(
                f"Accuracy drops from {first_acc:.0%} at {first_gl} "
                f"to {last_acc:.0%} at {last_gl}."
            )
        elif abs(delta) <= INTERP_STABLE_GRADE_DELTA:
            sentences.append("Accuracy remains stable across all tested distance grades.")

    reliable = [gl for gl, a in grade_accs if a >= INTERP_RELIABLE_ACCURACY_MIN]
    if reliable:
        sentences.append(f"Reliable detection (≥70% accuracy) up to {reliable[-1]}.")
    elif grade_accs:
        sentences.append("Accuracy is below 70% across all tested distance grades.")

    if not math.isnan(m["fpr"]) and m["fpr"] > INTERP_HIGH_ERROR_RATE:
        sentences.append(
            f"High false positive rate ({fmt(m['fpr'])}): "
            "system frequently triggers on non-drone sounds."
        )
    if not math.isnan(m["fnr"]) and m["fnr"] > INTERP_HIGH_ERROR_RATE:
        sentences.append(
            f"High false negative rate ({fmt(m['fnr'])}): "
            "a significant share of drones go undetected."
        )
    return sentences


def _render_section(
    out: list[str],
    mic_cols: list[str],
    overall: dict,
    by_grade: dict,
    by_class: dict,
    grades: list[tuple[float, float, str]],
    W: int,
) -> None:
    """Append overall, by-distance, and interpretation blocks to *out*."""
    out.append("OVERALL RESULTS")
    out.append("-" * W)
    for mic in mic_cols:
        m = metrics(overall[mic])
        out.append(
            f"{mic:<8}  Acc {fmt(m['accuracy'])}  Recall {fmt(m['recall'])}"
            f"  F1 {fmt(m['f1'])}  FPR {fmt(m['fpr'])}  FNR {fmt(m['fnr'])}"
        )
    out.append("")

    out.append("PERFORMANCE BY DISTANCE GRADE  (Accuracy / Recall / FPR)")
    out.append("-" * W)
    has_undefined = False
    ref_mic = mic_cols[0] if mic_cols else None
    grade_labels = [gl for _, _, gl in grades]
    for gl in grade_labels:
        if ref_mic is None:
            continue
        n = sum(dict(by_grade[ref_mic].get(gl, {})).values())
        if n == 0:
            continue
        parts = [f"{gl:<10}  n={n:<4}"]
        for mic in mic_cols:
            c = dict(by_grade[mic].get(gl, {}))
            m = metrics(c)
            if math.isnan(m["recall"]) or math.isnan(m["fpr"]):
                has_undefined = True
            parts.append(
                f"{mic}: {fmt(m['accuracy'])} / {fmt(m['recall'])} / {fmt(m['fpr'])}"
            )
        out.append("  " + "  ".join(parts))
    if has_undefined:
        out.append(
            "  (—) = metric undefined: no drone samples played at this distance grade"
        )
    out.append("")

    out.append("INTERPRETATION")
    out.append("-" * W)
    for mic in mic_cols:
        m = metrics(overall[mic])
        out.append(f"{mic}:")
        for sentence in _interpret_mic(mic, m, by_grade[mic], grades):
            for line in textwrap.wrap(sentence, width=W - 4, subsequent_indent="    "):
                out.append(f"  {line}")
        out.append("")


def write_report(
    csv_path: Path,
    plots_dir: Path,
    mic_cols: list[str],
    rows: list[dict],
    overall: dict,
    by_grade: dict,
    by_class: dict,
    grades: list[tuple[float, float, str]],
    beyond_data: dict | None = None,
) -> Path:
    drone_count     = sum(1 for r in rows if r["label"] == "drone")
    non_drone_count = len(rows) - drone_count
    W = REPORT_WIDTH_DETECTION

    out: list[str] = []
    out.append("DRONE DETECTION TEST REPORT")
    out.append("=" * W)
    out.append(f"Session  : {csv_path.stem}")
    out.append(f"Samples  : {len(rows)}  ({drone_count} drone / {non_drone_count} non-drone)")
    if beyond_data:
        detect_max = rows[0].get("mic_detect_max_m", "?")
        n_in      = len(rows) - len(beyond_data["rows"])
        n_beyond  = len(beyond_data["rows"])
        out.append(f"Split at : {detect_max} m  ({n_in} within range / {n_beyond} beyond range)")
    out.append("")

    if beyond_data:
        detect_max = rows[0].get("mic_detect_max_m", "?")
        out.append(f"WITHIN DETECTION RANGE  (distance ≤ {detect_max} m)")
        out.append("=" * W)
    _render_section(out, mic_cols, overall, by_grade, by_class, grades, W)

    if beyond_data:
        detect_max = rows[0].get("mic_detect_max_m", "?")
        out.append(f"BEYOND DETECTION RANGE  (distance > {detect_max} m)")
        out.append("=" * W)
        out.append(
            "Note: false negatives here are expected — drone was beyond the microphone's"
        )
        out.append(
            "rated range.  Any true positives indicate detection beyond rated range."
        )
        out.append("")
        _render_section(
            out, mic_cols,
            beyond_data["overall"], beyond_data["by_grade"], beyond_data["by_class"],
            beyond_data["grades"], W,
        )

    report_path = plots_dir / "report.txt"
    report_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return report_path
