"""Pure mathematical functions for detection metrics — no I/O, no side effects."""

import math

from drau.settings.constants import (
    GRADE_NICE_THRESHOLD_FINE,
    GRADE_NICE_THRESHOLD_LARGE,
    GRADE_NICE_THRESHOLD_MEDIUM,
    GRADE_NICE_THRESHOLD_XLARGE,
    GRADE_ZONE_FRACTION_B1,
    GRADE_ZONE_FRACTION_B2,
    GRADE_ZONE_FRACTION_B3,
)


def compute_grades(max_dist: float) -> list[tuple[float, float, str]]:
    """Return 4 distance zones scaled to the actual data range with round boundaries."""
    def _nice(v: float) -> int:
        if v < GRADE_NICE_THRESHOLD_FINE:   return max(1, round(v))
        if v < GRADE_NICE_THRESHOLD_MEDIUM: return round(v / 5)  * 5
        if v < GRADE_NICE_THRESHOLD_LARGE:  return round(v / 10) * 10
        if v < GRADE_NICE_THRESHOLD_XLARGE: return round(v / 25) * 25
        return                                     round(v / 100) * 100

    b1 = _nice(max_dist * GRADE_ZONE_FRACTION_B1)
    b2 = _nice(max_dist * GRADE_ZONE_FRACTION_B2)
    b3 = _nice(max_dist * GRADE_ZONE_FRACTION_B3)
    b1 = max(b1, 1)
    b2 = max(b2, b1 + 1)
    b3 = max(b3, b2 + 1)
    return [
        (0,   b1,           f"≤ {b1} m"),
        (b1,  b2,           f"{b1}–{b2} m"),
        (b2,  b3,           f"{b2}–{b3} m"),
        (b3,  float("inf"), f"> {b3} m"),
    ]


def grade(distance_m: float, grades: list[tuple[float, float, str]]) -> str:
    for lo, hi, label in grades:
        if lo <= distance_m < hi:
            return label
    return grades[-1][2]


def outcome(label: str, result: str) -> str:
    drone    = label == "drone"
    detected = result == "identified"
    if drone and detected:     return "TP"
    if drone and not detected: return "FN"
    if detected:               return "FP"
    return "TN"


def metrics(counts: dict[str, int]) -> dict[str, float]:
    tp = counts.get("TP", 0)
    fp = counts.get("FP", 0)
    tn = counts.get("TN", 0)
    fn = counts.get("FN", 0)
    total = tp + fp + tn + fn

    def div(a: int, b: int) -> float:
        return a / b if b else math.nan

    precision = div(tp, tp + fp)
    recall    = div(tp, tp + fn)
    denom     = precision + recall
    f1 = (
        2 * precision * recall / denom
        if not (math.isnan(precision) or math.isnan(recall) or denom == 0)
        else math.nan
    )
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn, "total": total,
        "accuracy":  div(tp + tn, total),
        "precision": precision,
        "recall":    recall,
        "f1":        f1,
        "fpr":       div(fp, fp + tn),
        "fnr":       div(fn, fn + tp),
    }


def fmt(v: float) -> str:
    return "—" if math.isnan(v) else f"{v:.1%}"


def safe(v: float) -> float:
    return 0.0 if math.isnan(v) else v
