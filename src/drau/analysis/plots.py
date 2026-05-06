"""Matplotlib plot generation for detection analysis results."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np

from drau.analysis.metrics import metrics, safe
from drau.settings.constants import (
    PLOT_CLASS_CAPTION_BOTTOM,
    PLOT_CONFUSION_COLOR_THRESHOLD,
    PLOT_DISTANCE_CAPTION_BOTTOM,
    PLOT_DPI,
    PLOT_GRID_ALPHA,
    PLOT_MIC_COLORS,
    PLOT_METRICS_YLIM_MAX,
)


def _style() -> None:
    plt.rcParams.update({
        "font.family":      "sans-serif",
        "axes.spines.top":  False,
        "axes.spines.right":False,
        "axes.grid":        True,
        "axes.grid.axis":   "y",
        "grid.alpha":       PLOT_GRID_ALPHA,
        "figure.facecolor": "white",
    })


def _plot_confusion_matrices(plots_dir: Path, mic_cols: list[str], overall: dict) -> None:
    n = len(mic_cols)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    if n == 1:
        axes = [axes]

    for ax, mic in zip(axes, mic_cols):
        c   = overall[mic]
        mat = np.array([
            [c.get("TP", 0), c.get("FN", 0)],
            [c.get("FP", 0), c.get("TN", 0)],
        ], dtype=float)
        im = ax.imshow(mat, cmap="Blues", aspect="auto", vmin=0)
        fig.colorbar(im, ax=ax, shrink=0.75)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Identified", "Not\nIdentified"])
        ax.set_yticklabels(["Drone", "Non-Drone"])
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(mic, fontweight="bold")
        labels = [["TP", "FN"], ["FP", "TN"]]
        for i in range(2):
            for j in range(2):
                ax.text(
                    j, i,
                    f"{labels[i][j]}\n{int(mat[i, j])}",
                    ha="center", va="center", fontsize=13, fontweight="bold",
                    color="white" if mat[i, j] > mat.max() * PLOT_CONFUSION_COLOR_THRESHOLD else "black",
                )

    fig.suptitle("Confusion Matrices", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(plots_dir / "confusion_matrix.png", dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)


def _plot_metrics_overview(plots_dir: Path, mic_cols: list[str], overall: dict) -> None:
    METRIC_KEYS   = ["accuracy", "precision", "recall", "f1", "fpr", "fnr"]
    METRIC_LABELS = ["Accuracy", "Precision", "Recall", "F1", "FPR", "FNR"]
    x     = np.arange(len(METRIC_KEYS))
    n     = len(mic_cols)
    width = 0.75 / max(n, 1)

    fig, ax = plt.subplots(figsize=(11, 5))
    for i, mic in enumerate(mic_cols):
        m      = metrics(overall[mic])
        values = [safe(m[k]) for k in METRIC_KEYS]
        offset = (i - (n - 1) / 2) * width
        ax.bar(x + offset, values, width * 0.9,
               label=mic, color=PLOT_MIC_COLORS[i % len(PLOT_MIC_COLORS)], alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(METRIC_LABELS, fontsize=11)
    ax.set_ylim(0, PLOT_METRICS_YLIM_MAX)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Detection Metrics Overview", fontsize=13, fontweight="bold")
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.6, alpha=0.5)
    ax.legend(fontsize=10)

    if n == 1:
        m = metrics(overall[mic_cols[0]])
        for xi, key in enumerate(METRIC_KEYS):
            v = safe(m[key])
            ax.text(xi, v + 0.02, f"{v:.0%}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(plots_dir / "metrics_overview.png", dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)


def _plot_by_distance(
    plots_dir: Path,
    mic_cols: list[str],
    by_grade: dict,
    grades: list[tuple[float, float, str]],
) -> None:
    grade_labels = [gl for _, _, gl in grades]
    METRIC_KEYS  = ["accuracy", "recall", "fpr", "fnr"]
    METRIC_NAMES = ["Accuracy", "Recall (TPR)", "FPR", "FNR"]
    LINE_COLORS  = ["#2ecc71", "#3498db", "#e74c3c", "#e67e22"]
    LINE_STYLES  = ["-", "-", "--", "--"]

    n    = len(mic_cols)
    fig, axes = plt.subplots(n, 1, figsize=(9, 4 * n), squeeze=False)

    for row, mic in enumerate(mic_cols):
        ax = axes[row, 0]
        grade_counts = [sum(dict(by_grade[mic].get(gl, {})).values()) for gl in grade_labels]

        for mk, mname, color, ls in zip(METRIC_KEYS, METRIC_NAMES, LINE_COLORS, LINE_STYLES):
            values = []
            for gl in grade_labels:
                c = dict(by_grade[mic].get(gl, {}))
                m = metrics(c)
                values.append(m[mk])  # keep nan → plotted as a gap, not 0
            ax.plot(grade_labels, values, marker="o", label=mname,
                    color=color, linestyle=ls, linewidth=2.2, markersize=7)

        for xi, (gl, cnt) in enumerate(zip(grade_labels, grade_counts)):
            if cnt:
                ax.annotate(f"n={cnt}", (xi, -0.07), ha="center", va="top",
                            fontsize=8, color="gray", annotation_clip=False)

        ax.set_ylim(-0.05, 1.15)
        ax.set_ylabel("Score", fontsize=10)
        ax.set_title(f"{mic} — Performance by Distance Grade", fontsize=11, fontweight="bold")
        ax.legend(loc="upper right", fontsize=9)

    caption = (
        "Solid lines: higher is better (Accuracy, Recall).  "
        "Dashed lines: lower is better (FPR, FNR).\n"
        "A gap means no samples of the relevant class were played at that distance "
        "— the metric is undefined there, not zero.\n"
        "n= labels show total observations per grade; "
        "grades with few samples are less statistically reliable."
    )
    fig.text(0.5, 0.01, caption, ha="center", va="bottom",
             fontsize=8, color="#555555", style="italic")
    fig.tight_layout(rect=[0, PLOT_DISTANCE_CAPTION_BOTTOM, 1, 1])
    fig.savefig(plots_dir / "performance_by_distance.png", dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)


def _plot_by_class(plots_dir: Path, mic_cols: list[str], by_class: dict) -> None:
    classes       = ["drone", "non_drone"]
    class_labels  = ["Drone", "Non-Drone"]
    METRIC_KEYS   = ["recall", "fpr", "fnr"]
    METRIC_NAMES  = ["Recall (TPR)", "FPR", "FNR"]
    METRIC_COLORS = ["#3498db", "#e74c3c", "#e67e22"]

    x     = np.arange(len(classes))
    n     = len(mic_cols)
    width = 0.22

    fig, axes = plt.subplots(1, n, figsize=(6 * n, 4.5), squeeze=False)

    for col, mic in enumerate(mic_cols):
        ax = axes[0, col]
        for mi, (mk, mname, color) in enumerate(zip(METRIC_KEYS, METRIC_NAMES, METRIC_COLORS)):
            values = []
            for cls in classes:
                c = dict(by_class[mic].get(cls, {}))
                m = metrics(c)
                values.append(safe(m[mk]))
            offset = (mi - (len(METRIC_KEYS) - 1) / 2) * width
            ax.bar(x + offset, values, width * 0.9, label=mname, color=color, alpha=0.85)

        for xi, cls in enumerate(classes):
            c   = dict(by_class[mic].get(cls, {}))
            cnt = sum(c.values())
            if cnt:
                ax.annotate(f"n={cnt}", (xi, -0.07), ha="center", va="top",
                            fontsize=8, color="gray", annotation_clip=False)

        ax.set_xticks(x)
        ax.set_xticklabels(class_labels, fontsize=11)
        ax.set_ylim(-0.05, 1.15)
        ax.set_ylabel("Rate", fontsize=10)
        ax.set_title(f"{mic} — Performance by Sound Class", fontsize=11, fontweight="bold")
        ax.legend(fontsize=9)

    fig.tight_layout(rect=[0, PLOT_CLASS_CAPTION_BOTTOM, 1, 1])
    fig.savefig(plots_dir / "performance_by_class.png", dpi=PLOT_DPI, bbox_inches="tight")
    plt.close(fig)


def save_plots(
    csv_path: Path,
    mic_cols: list[str],
    overall: dict,
    by_grade: dict,
    by_class: dict,
    grades: list[tuple[float, float, str]],
    subdir: str | None = None,
) -> Path:
    plots_dir = csv_path.parent / f"{csv_path.stem}_plots"
    if subdir:
        plots_dir = plots_dir / subdir
    plots_dir.mkdir(parents=True, exist_ok=True)
    _style()
    _plot_confusion_matrices(plots_dir, mic_cols, overall)
    _plot_metrics_overview(plots_dir, mic_cols, overall)
    _plot_by_distance(plots_dir, mic_cols, by_grade, grades)
    _plot_by_class(plots_dir, mic_cols, by_class)
    return plots_dir
