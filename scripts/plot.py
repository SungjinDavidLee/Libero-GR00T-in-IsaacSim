#!/usr/bin/env python3
"""Generate every chart in assets/ from data/episodes.csv.

Usage
    python3 scripts/plot.py [--csv data/episodes.csv] [--out assets]

The script has no dependency beyond matplotlib and the standard library.
Labels are English so that the figures render identically on machines
without a Korean font installed.
"""

import argparse
import csv
import math
import os
import statistics as st

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

INK = "#1b1f24"
MUTE = "#6b7480"
GRID = "#e3e7ec"
BLUE = "#2f6feb"
TEAL = "#1f9d8f"
AMBER = "#d99000"
RED = "#cf3b3b"
GREY = "#9aa4b1"

# MuJoCo reference success, 10 episodes per task
REFERENCE = [8, 10, 10, 9, 10, 10, 10, 9, 10, 10]
REF_PLACE_ERR_M = 0.0129  # reference bowl-to-plate distance at success

TASK_LABEL = [
    "T0 between\nplate/ramekin",
    "T1 next to\nramekin",
    "T2 table\ncenter",
    "T3 on cookie\nbox",
    "T4 in top\ndrawer",
    "T5 on\nramekin",
    "T6 next to\ncookie box",
    "T7 on\nstove",
    "T8 next to\nplate",
    "T9 on wooden\ncabinet",
]


def num(row, key, default=None):
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return default


def load(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def style(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTE, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK, fontsize=13, fontweight="bold",
                     loc="left", pad=14)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTE, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTE, fontsize=10)


def save(fig, out, name):
    path = os.path.join(out, name)
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


# --------------------------------------------------------------------------
# stage definitions
# --------------------------------------------------------------------------

def stages(rows):
    """Cumulative pass counts for the five measurable pipeline stages."""
    total = len(rows)
    attempted = sum(1 for r in rows if num(r, "close_q", -1) >= 0)
    grasped = sum(1 for r in rows if (num(r, "maxlift", 0) or 0) > 0.017)
    reached = sum(1 for r in rows
                  if 0 <= (num(r, "holdd", -1) or -1) < 0.050)
    placed = sum(1 for r in rows if r["termhold"] == "1")
    clean = sum(1 for r in rows if r["strict"] == "1")
    return total, attempted, grasped, reached, placed, clean


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------

def fig_funnel(rows, out):
    total, attempted, grasped, reached, placed, clean = stages(rows)
    names = ["Episodes", "S2 approach", "S5 grasp", "S8 transport",
             "S10 placement", "S10+ no disturbance"]
    vals = [total, attempted, grasped, reached, placed, clean]
    colors = [GREY, BLUE, BLUE, TEAL, TEAL, AMBER]

    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    y = list(range(len(vals)))[::-1]
    ax.barh(y, vals, color=colors, height=0.62)
    for yi, v in zip(y, vals):
        ax.text(v + 8, yi, "%d  (%.1f%%)" % (v, 100 * v / total),
                va="center", color=INK, fontsize=10, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlim(0, total * 1.22)
    style(ax, "Pipeline funnel — 500 episodes, 10 tasks x 50",
          xlabel="episodes passing the stage")
    ax.grid(axis="y", linewidth=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    save(fig, out, "funnel.png")


def fig_task_success(rows, out):
    ours, ref = [], []
    for t in range(10):
        sub = [r for r in rows if r["task"] == str(t)]
        ours.append(100.0 * sum(1 for r in sub if r["termhold"] == "1") / len(sub))
        ref.append(10.0 * REFERENCE[t])

    x = list(range(10))
    fig, ax = plt.subplots(figsize=(10.6, 4.6))
    ax.bar([i - 0.2 for i in x], ref, width=0.38, color=GREY,
           label="MuJoCo reference (n=10)")
    ax.bar([i + 0.2 for i in x], ours, width=0.38, color=BLUE,
           label="Isaac Sim + adapter (n=50)")
    for i, v in enumerate(ours):
        ax.text(i + 0.2, v + 2, "%.0f" % v, ha="center", color=INK,
                fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([lab.replace("\n", " ") for lab in TASK_LABEL],
                       rotation=32, ha="right", fontsize=8.5)
    ax.set_ylim(0, 112)
    style(ax, "Task success — placement verified by 2 s physics hold",
          ylabel="success rate (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUTE, loc="upper right")
    ax.annotate("scene port incomplete\n(drawer transport)", xy=(4, 4),
                xytext=(4, 42), ha="center", fontsize=8.5, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1))
    save(fig, out, "task-success.png")


def fig_threshold(rows, out):
    ths = [0.005 * i for i in range(1, 13)]
    counts = []
    for t in ths:
        counts.append(sum(1 for r in rows
                          if 0 <= (num(r, "holdd", -1) or -1) < t))
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.plot([t * 1000 for t in ths], [100 * c / len(rows) for c in counts],
            color=BLUE, linewidth=2.4, marker="o", markersize=5)
    ax.axvline(REF_PLACE_ERR_M * 1000, color=RED, linestyle="--", linewidth=1.4)
    ax.text(REF_PLACE_ERR_M * 1000 + 1.2, 6,
            "reference placement\nerror  12.9 mm", color=RED, fontsize=9)
    ax.axvline(50, color=TEAL, linestyle=":", linewidth=1.4)
    ax.text(50 - 1.5, 6, "physical seating\nlimit  50 mm", color=TEAL,
            fontsize=9, ha="right")
    style(ax, "Success rate depends on the placement-radius threshold",
          xlabel="accepted bowl-to-plate distance (mm)",
          ylabel="episodes accepted (%)")
    ax.set_ylim(0, 80)
    save(fig, out, "threshold-sensitivity.png")


def fig_precision(rows, out):
    vals = [1000 * v for v in
            (num(r, "holdd", -1) for r in rows) if v is not None and v >= 0]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.hist(vals, bins=28, range=(0, 70), color=BLUE, alpha=0.85)
    ax.axvline(REF_PLACE_ERR_M * 1000, color=RED, linewidth=1.8)
    ax.text(REF_PLACE_ERR_M * 1000 + 1.5, ax.get_ylim()[1] * 0.86,
            "reference  12.9 mm", color=RED, fontsize=9)
    med = st.median(vals)
    ax.axvline(med, color=AMBER, linewidth=1.8)
    ax.text(med + 1.5, ax.get_ylim()[1] * 0.72, "ours  %.1f mm" % med,
            color=AMBER, fontsize=9)
    style(ax, "Placement precision after the physics hold",
          xlabel="bowl centre to plate centre (mm)",
          ylabel="episodes")
    save(fig, out, "placement-precision.png")


def fig_failure(rows, out):
    tally = {}
    for r in rows:
        for token in r["strict_why"].split(","):
            if token:
                key = token.split("=")[0]
                tally[key] = tally.get(key, 0) + 1
    label = {"pmax": "plate pushed\n> 5 mm",
             "dist": "unrelated object\nmoved > 5 mm",
             "bpen": "bowl pressed\n> 3 mm",
             "bimp": "repeated impact\n> 12",
             "ret": "gripper did not\nwithdraw"}
    keys = sorted(tally, key=lambda k: -tally[k])
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    ax.bar([label.get(k, k) for k in keys], [tally[k] for k in keys],
           color=[RED, AMBER, TEAL, GREY, BLUE][:len(keys)], width=0.55)
    for i, k in enumerate(keys):
        ax.text(i, tally[k] + 1.5, str(tally[k]), ha="center", color=INK,
                fontsize=10, fontweight="bold")
    style(ax, "Why episodes fail the no-disturbance criterion",
          ylabel="occurrences across 500 episodes")
    ax.tick_params(axis="x", labelsize=9)
    save(fig, out, "failure-breakdown.png")


def fig_calibration(out):
    """Open-loop replay: displacement ratio against the reference."""
    scale = [0.020, 0.024, 0.028, 0.031]
    ratio = [0.806, 0.979, 1.151, 1.279]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.plot([s * 1000 for s in scale], ratio, color=BLUE, linewidth=2.4,
            marker="o", markersize=6)
    ax.axhline(1.0, color=GRID, linewidth=1.4)
    ax.axvline(24.5, color=TEAL, linestyle="--", linewidth=1.6)
    ax.text(24.9, 0.83, "calibrated\nPSCALE = 0.0245", color=TEAL, fontsize=9)
    ax.scatter([16], [0.66], color=RED, zorder=5, s=45)
    ax.annotate("previous value 0.016\nreached 66% of the\nreference motion",
                xy=(16, 0.66), xytext=(17.5, 0.70), fontsize=9, color=RED)
    ax.add_patch(Rectangle((15, 0.95), 18, 0.10, color=TEAL, alpha=0.08))
    style(ax, "Open-loop calibration — replaying reference actions",
          xlabel="PSCALE (mm per unit action)",
          ylabel="our displacement / reference displacement")
    ax.set_ylim(0.6, 1.35)
    save(fig, out, "calibration.png")


def fig_stage_matrix(rows, out):
    grid, labels = [], ["S2 approach", "S5 grasp", "S8 transport",
                        "S10 placement", "S10+ clean"]
    for t in range(10):
        sub = [r for r in rows if r["task"] == str(t)]
        _, a, g, rr, p, c = stages(sub)
        grid.append([100 * v / len(sub) for v in (a, g, rr, p, c)])

    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    im = ax.imshow(grid, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(5))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticks(range(10))
    ax.set_yticklabels([lab.replace("\n", " ") for lab in TASK_LABEL],
                       fontsize=8.5)
    for i in range(10):
        for j in range(5):
            v = grid[i][j]
            ax.text(j, i, "%.0f" % v, ha="center", va="center", fontsize=9,
                    color="white" if v > 55 else INK)
    ax.set_title("Stage pass rate per task (%)", color=INK, fontsize=13,
                 fontweight="bold", loc="left", pad=14)
    ax.tick_params(colors=MUTE, length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.028, pad=0.02)
    save(fig, out, "stage-matrix.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/episodes.csv")
    ap.add_argument("--out", default="assets")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rows = load(args.csv)
    print("loaded %d episodes" % len(rows))
    fig_funnel(rows, args.out)
    fig_task_success(rows, args.out)
    fig_threshold(rows, args.out)
    fig_precision(rows, args.out)
    fig_failure(rows, args.out)
    fig_calibration(args.out)
    fig_stage_matrix(rows, args.out)


if __name__ == "__main__":
    main()
