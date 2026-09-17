#!/usr/bin/env python3
"""Generate every figure in assets/ from the CSV files in data/.

    python3 scripts/plot.py

Only matplotlib and the standard library are required. Labels are English so
the figures render the same on machines without a Korean font.
"""

import csv
import math
import os
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "assets")

INK, MUT, GRID = "#1b1f24", "#6b7480", "#e3e7ec"
BLUE, TEAL, AMBER, RED, GREY = "#2f6feb", "#1f9d8f", "#d99000", "#cf3b3b", "#9aa4b1"

# MuJoCo reference, 10 episodes per task
REFERENCE = [8, 10, 10, 9, 10, 10, 10, 9, 10, 10]

# placement successes per task, run 1 (no distractor except T0) and run 2
RUN1 = [45, 36, 35, 39, 0, 44, 28, 38, 46, 27]
RUN2 = [43, 32, 33, 40, 2, 42, 48, 36, 46, 26]

# end-effector tracking error with the policy switched off (mm), centre line
CONTROL = [(0.45, 1.41), (0.55, 2.08), (0.62, 2.80),
           (0.68, 3.76), (0.74, 5.35), (0.80, 8.97)]

# distractor-proximity experiment, 12 episodes per cell
PROX_GAPS = [125, 160, 210, 300]
PROX = {
    "select": [34, 34, 36, 36],      # correct bowl approached, out of 36
    "grasp": [34, 36, 36, 36],
    "place": [25, 24, 28, 32],
}
PROX_TASK = {0: [12, 9, 11, 12], 1: [5, 5, 9, 10], 8: [8, 10, 8, 10]}


def load(name):
    with open(os.path.join(DATA, name), newline="") as fp:
        return list(csv.DictReader(fp))


def num(row, key, default=None):
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return default


def style(ax, title=None, xlabel=None, ylabel=None, grid="y"):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUT, labelsize=9, length=0)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK, fontsize=13, fontweight="bold",
                     loc="left", pad=14)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUT, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUT, fontsize=10)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote assets/" + name)


# --------------------------------------------------------------------------

def fig_funnel(rows):
    n = len(rows)
    stages = [
        ("Episodes", n),
        ("S1 target selected", sum(1 for r in rows if r["sel_target"] == "1")),
        ("S2 grasp attempted", sum(1 for r in rows if num(r, "close_q", -1) >= 0)),
        ("S3 pre-grasp aligned", sum(1 for r in rows
                                     if (num(r, "d_xy") or 9) < 0.080)),
        ("S6 object lifted", sum(1 for r in rows if (num(r, "maxlift") or 0) > 0.017)),
        ("S8 reached the plate", sum(1 for r in rows
                                     if 0 <= (num(r, "holdd", -1) or -1) < 0.050)),
        ("S10 placed", sum(1 for r in rows if r["termhold"] == "1")),
    ]
    colors = [GREY, BLUE, BLUE, BLUE, TEAL, TEAL, AMBER]
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    y = list(range(len(stages)))[::-1]
    ax.barh(y, [v for _, v in stages], color=colors, height=0.62)
    for yi, (_, v) in zip(y, stages):
        ax.text(v + 6, yi, "%d  (%.1f%%)" % (v, 100 * v / n), va="center",
                color=INK, fontsize=10, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([s for s, _ in stages])
    ax.set_xlim(0, n * 1.24)
    style(ax, "Pipeline funnel — run 2, %d episodes" % n,
          xlabel="episodes passing the stage", grid="x")
    save(fig, "funnel-run2.png")


def fig_run_compare():
    x = list(range(10))
    fig, ax = plt.subplots(figsize=(10.6, 4.6))
    ax.bar([i - 0.27 for i in x], [v * 2 for v in REFERENCE], width=0.26,
           color=GREY, label="MuJoCo reference (n=10)")
    ax.bar([i for i in x], [v * 2 for v in RUN1], width=0.26,
           color=BLUE, label="run 1 — no distractor (n=50)")
    ax.bar([i + 0.27 for i in x], [v * 2 for v in RUN2], width=0.26,
           color=TEAL, label="run 2 — distractor restored (n=50)")
    ax.set_xticks(x)
    ax.set_xticklabels(["T%d" % i for i in x])
    ax.set_ylim(0, 112)
    style(ax, "Placement success per task", ylabel="success rate (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="lower left")
    ax.annotate("scene port incomplete", xy=(4, 4), xytext=(4.3, 40),
                fontsize=8.5, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1))
    ax.annotate("layout also changed", xy=(6, 96), xytext=(6.4, 62),
                fontsize=8.5, color=AMBER,
                arrowprops=dict(arrowstyle="->", color=AMBER, lw=1))
    save(fig, "run-compare.png")


def fig_thresholds(rows):
    lifted = [r for r in rows if (num(r, "maxlift") or 0) > 0.017]
    reached = [r for r in rows if 0 <= (num(r, "holdd", -1) or -1)]
    series = [
        ("pre-grasp alignment (mm)", [1000 * (num(r, "d_xy") or 9) for r in rows
                                      if num(r, "d_xy") is not None],
         [50, 60, 70, 80, 90, 100, 120], 80),
        ("post-grasp slip (mm)", [1000 * (num(r, "slip") or 9) for r in lifted],
         [100, 120, 150, 200, 250, 300, 500], 150),
        ("unrelated object moved (mm)", [1000 * (num(r, "distmax") or 9)
                                         for r in lifted],
         [5, 10, 20, 30, 50, 100, 200], 5),
        ("impact count", [num(r, "bimp") or 99 for r in reached],
         [8, 10, 12, 15, 20, 30, 50], 12),
        ("placement radius (mm)", [1000 * (num(r, "holdd") or 9) for r in reached],
         [13, 20, 30, 40, 50, 60, 70], 50),
    ]
    fig, axes = plt.subplots(1, 5, figsize=(19.0, 3.9))
    for ax, (lab, vals, ths, chosen) in zip(axes, series):
        if not vals:
            continue
        rate = [100 * sum(1 for v in vals if v < t) / len(vals) for t in ths]
        ax.plot(ths, rate, color=BLUE, linewidth=2.2, marker="o", markersize=5)
        ax.axvline(chosen, color=RED, linestyle="--", linewidth=1.4)
        ax.axvline(st.median(vals), color=AMBER, linestyle=":", linewidth=1.4)
        ax.set_ylim(0, 105)
        style(ax, lab, xlabel="threshold", ylabel="pass rate (%)")
        ax.text(0.98, 0.06, "median %.4g" % st.median(vals), transform=ax.transAxes,
                ha="right", fontsize=8, color=AMBER)
    fig.suptitle("Threshold sensitivity — run 2.  red dashed: value used,  "
                 "amber dotted: median of the data",
                 x=0.055, y=1.04, ha="left", fontsize=13,
                 fontweight="bold", color=INK)
    save(fig, "threshold-sensitivity.png")


def fig_reach(rows):
    per = {}
    for r in rows:
        d = num(r, "d_xy")
        if d is None:
            continue
        per.setdefault(int(r["task"]), []).append((num(r, "reach"), d))
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    xs, ys = [], []
    for t in sorted(per):
        reach = per[t][0][0]
        med = st.median(v for _, v in per[t])
        xs.append(reach)
        ys.append(1000 * med)
        ax.scatter([reach], [1000 * med], s=90, color=BLUE, zorder=5)
        ax.text(reach + 0.006, 1000 * med, "T%d" % t, fontsize=9, color=INK,
                va="center")
    mx, my = st.mean(xs), st.mean(ys)
    sx, sy = st.pstdev(xs), st.pstdev(ys)
    r = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / len(xs) / (sx * sy)
    b1 = r * sy / sx
    lo, hi = min(xs) - 0.02, max(xs) + 0.03
    ax.plot([lo, hi], [my + b1 * (lo - mx), my + b1 * (hi - mx)],
            color=GREY, linewidth=1.4, linestyle="--", zorder=1)
    cx = [c[0] for c in CONTROL]
    cy = [c[1] for c in CONTROL]
    ax.plot(cx, cy, color=RED, linewidth=2.0, marker="s", markersize=5,
            label="control-only tracking error (policy off)")
    ax.scatter([], [], s=90, color=BLUE, label="median alignment error per task")
    ax.set_xlim(lo, hi)
    style(ax, "Alignment error against reach   (task level, r = %+.3f, n = %d)"
          % (r, len(xs)),
          xlabel="distance from the robot base (m)",
          ylabel="error (mm)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="upper left")
    ax.text(0.86, 2.0, "IK fails\nbeyond 0.80 m", fontsize=8.5, color=RED,
            ha="right")
    save(fig, "reach-alignment.png")


def fig_control():
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    x = [c[0] for c in CONTROL]
    y = [c[1] for c in CONTROL]
    ax.plot(x, y, color=RED, linewidth=2.4, marker="o", markersize=6)
    ax.axvspan(0.80, 0.90, color=GREY, alpha=0.25)
    ax.text(0.845, 6.0, "IK failures\nwith lateral offset", ha="center",
            fontsize=9, color="#4b5563")
    for xi, yi in CONTROL:
        ax.text(xi, yi + 0.35, "%.1f" % yi, ha="center", fontsize=8.5, color=INK)
    ax.set_xlim(0.42, 0.90)
    style(ax, "End-effector tracking error with the policy switched off",
          xlabel="distance from the robot base (m)",
          ylabel="commanded to achieved (mm)")
    save(fig, "control-error.png")


def fig_proximity():
    fig, axes = plt.subplots(1, 2, figsize=(15.4, 4.4))
    fig.subplots_adjust(wspace=0.28)
    ax = axes[0]
    for key, col, lab in (("select", BLUE, "correct bowl approached"),
                          ("grasp", TEAL, "object lifted"),
                          ("place", AMBER, "placed")):
        ax.plot(PROX_GAPS, [100 * v / 36 for v in PROX[key]], color=col,
                linewidth=2.2, marker="o", markersize=6, label=lab)
    ax.set_ylim(0, 108)
    style(ax, "Distractor proximity — pooled (12 episodes per cell)",
          xlabel="distance between the two bowls (mm)", ylabel="rate (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="lower right")
    ax.axvline(112, color=GREY, linestyle=":", linewidth=1.2)
    ax.text(114, 10, "bowls touch\nat 112 mm", fontsize=8, color=MUT)

    ax = axes[1]
    for t, col in ((0, BLUE), (1, RED), (8, TEAL)):
        ax.plot(PROX_GAPS, [100 * v / 12 for v in PROX_TASK[t]], color=col,
                linewidth=2.0, marker="o", markersize=6, label="T%d" % t)
    ax.set_ylim(0, 108)
    style(ax, "Placement success per task",
          xlabel="distance between the two bowls (mm)", ylabel="rate (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="lower right")
    save(fig, "distractor-proximity.png")


def fig_layout(rows):
    easy = [r for r in rows if r["difficulty"] == "easy"]
    hard = [r for r in rows if r["difficulty"] == "hard"]
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 4.4))

    ax = axes[0]
    for g, col, lab in ((easy, BLUE, "near the training layout"),
                        (hard, AMBER, "far from it")):
        x = [1000 * float(r["mean_disp"]) for r in g]
        y = [int(r["S10"]) + (0.04 if col == BLUE else -0.04) for r in g]
        ax.scatter(x, y, s=55, color=col, alpha=0.8, label=lab)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["failed", "placed"])
    ax.set_ylim(-0.4, 1.4)
    style(ax, "Layout experiment — outcome against displacement",
          xlabel="mean displacement from the training layout (mm)", grid="x")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="center right")

    ax = axes[1]
    names = ["mean_disp", "d_target", "d_target_plate", "path_clearance",
             "approach_azimuth_deg", "reach_distance"]
    lab = ["displacement", "bowl moved", "transport dist.", "path clearance",
           "azimuth", "reach"]
    ys = [float(r["S10"]) for r in rows]
    my, sy = st.mean(ys), st.pstdev(ys)
    rs = []
    for k in names:
        v = [float(r[k]) for r in rows]
        mv, sv = st.mean(v), st.pstdev(v)
        rs.append(sum((a - mv) * (b - my) for a, b in zip(v, ys))
                  / len(v) / (sv * sy) if sv * sy else 0.0)
    cols = [RED if abs(x) > 0.36 else GREY for x in rs]
    ax.barh(range(len(rs)), rs, color=cols, height=0.6)
    ax.axvline(0.36, color=GREY, linestyle=":", linewidth=1.0)
    ax.axvline(-0.36, color=GREY, linestyle=":", linewidth=1.0)
    ax.set_yticks(range(len(rs)))
    ax.set_yticklabels(lab)
    ax.set_xlim(-0.8, 0.8)
    style(ax, "Correlation with placement success (n = 30)",
          xlabel="point-biserial r   (dotted: p = 0.05)", grid="x")
    save(fig, "layout-hypothesis.png")


def fig_calibration():
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
    style(ax, "Open-loop calibration \u2014 replaying reference actions",
          xlabel="PSCALE (mm per unit action)",
          ylabel="our displacement / reference displacement")
    ax.set_ylim(0.6, 1.35)
    save(fig, "calibration.png")


def fig_reach_success(rows):
    """C experiment: only the distance from the base changes."""
    import collections
    per = collections.defaultdict(list)
    for r in rows:
        per[float(r["reach"])].append(r)
    xs = sorted(per)
    place = [100 * sum(1 for r in per[x] if r["termhold"] == "1") / len(per[x])
             for x in xs]
    lift = [100 * sum(1 for r in per[x] if float(r["maxlift"]) > 0.017) / len(per[x])
            for x in xs]
    align = [1000 * st.median(float(r["d_xy"]) for r in per[x] if r["d_xy"])
             for x in xs]
    corrected = [a - ctrl_at(x) for a, x in zip(align, xs)]

    fig, axes = plt.subplots(1, 2, figsize=(16.0, 4.4))
    fig.subplots_adjust(wspace=0.30)

    ax = axes[0]
    ax.plot(xs, lift, color=TEAL, linewidth=2.2, marker="s", markersize=6,
            label="object lifted")
    ax.plot(xs, place, color=AMBER, linewidth=2.6, marker="o", markersize=7,
            label="placed")
    for x, v in zip(xs, place):
        ax.text(x, v + 4, "%.0f%%" % v, ha="center", fontsize=8.5, color=INK)
    ax.set_ylim(-6, 112)
    style(ax, "Only the base distance changes (20 episodes per level)",
          xlabel="distance from the robot base (m)", ylabel="rate (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="lower left")

    ax = axes[1]
    ax.plot(xs, align, color=BLUE, linewidth=2.2, marker="o", markersize=6,
            label="alignment error")
    ax.plot(xs, corrected, color=TEAL, linewidth=2.0, marker="^", markersize=6,
            linestyle="--", label="after removing control error")
    ax.plot([c[0] for c in CONTROL], [c[1] for c in CONTROL], color=RED,
            linewidth=1.8, marker="s", markersize=4,
            label="control-only error (policy off)")
    ax.set_xlim(min(xs) - 0.02, max(xs) + 0.02)
    style(ax, "Grasp alignment error, same axis",
          xlabel="distance from the robot base (m)", ylabel="median error (mm)")
    ax.legend(frameon=False, fontsize=9, labelcolor=MUT, loc="upper left")
    save(fig, "reach-success.png")


def fig_setup_map(setups):
    """Plan view of the 30 randomised layouts."""
    RAMEKIN, STOVE, CABINET = (-0.2000, 0.2000), (-0.2671, -0.1311), (0.0356, -0.2776)
    TRAIN = {"plate": (0.060, 0.200), "cookies": (0.070, 0.030),
             "target": (0.130, -0.070)}
    mark = {"plate": ("o", 120), "cookies": ("s", 90), "target": ("o", 70)}
    fig, ax = plt.subplots(figsize=(7.6, 7.6))
    for p, r, nm in ((RAMEKIN, 0.055, "ramekin"), (STOVE, 0.075, "stove"),
                     (CABINET, 0.110, "cabinet")):
        ax.add_patch(plt.Circle(p, r, facecolor=GREY, alpha=0.30,
                                edgecolor=GREY, zorder=1))
        ax.text(p[0], p[1], nm, ha="center", va="center", fontsize=7.5,
                color="#4b5563", zorder=2)
    for r in setups:
        c = BLUE if r["difficulty"] == "easy" else AMBER
        px, py = float(r["plate_x"]), float(r["plate_y"])
        tx, ty = float(r["target_x"]), float(r["target_y"])
        ax.plot([px, tx], [py, ty], color=c, linewidth=0.7, alpha=0.30, zorder=4)
        for k in ("plate", "cookies", "target"):
            m, sz = mark[k]
            ax.scatter([float(r[k + "_x"])], [float(r[k + "_y"])], marker=m,
                       s=sz * 0.35, color=c, alpha=0.7, edgecolor="none", zorder=5)
    for k, (x, y) in TRAIN.items():
        m, sz = mark[k]
        ax.scatter([x], [y], marker=m, s=sz, facecolor="none", edgecolor=INK,
                   linewidth=1.8, zorder=6)
        ax.text(x + 0.018, y, k, fontsize=8.5, color=INK, va="center", zorder=6)
    ax.scatter([], [], marker="o", s=45, color=BLUE, label="near the training layout")
    ax.scatter([], [], marker="o", s=45, color=AMBER, label="far from it")
    ax.scatter([], [], marker="o", s=60, facecolor="none", edgecolor=INK,
               label="training layout")
    ax.legend(frameon=False, fontsize=8.5, labelcolor=MUT, loc="lower left")
    ax.set_aspect("equal")
    ax.set_xlim(-0.34, 0.26)
    ax.set_ylim(-0.34, 0.38)
    style(ax, "The 30 randomised layouts — plan view (m)",
          xlabel="x  (towards the viewer)", ylabel="y  (left in the camera image)",
          grid="both")
    save(fig, "setup-map.png")


def fig_setup_grid(setups):
    RAMEKIN, STOVE, CABINET = (-0.2000, 0.2000), (-0.2671, -0.1311), (0.0356, -0.2776)
    rows = sorted(setups, key=lambda r: int(r["set_id"]))
    fig, axes = plt.subplots(5, 6, figsize=(16.5, 14.0))
    for ax, r in zip(axes.ravel(), rows):
        c = BLUE if r["difficulty"] == "easy" else AMBER
        for p, rad in ((RAMEKIN, 0.055), (STOVE, 0.075), (CABINET, 0.110)):
            ax.add_patch(plt.Circle(p, rad, facecolor=GREY, alpha=0.25,
                                    edgecolor="none", zorder=1))
        px, py = float(r["plate_x"]), float(r["plate_y"])
        tx, ty = float(r["target_x"]), float(r["target_y"])
        cx, cy = float(r["cookies_x"]), float(r["cookies_y"])
        ax.plot([px, tx], [py, ty], color=c, linewidth=1.2, alpha=0.5, zorder=4)
        ax.scatter([px], [py], marker="o", s=55, color=c, zorder=5)
        ax.scatter([cx], [cy], marker="s", s=42, color=c, zorder=5)
        ax.scatter([tx], [ty], marker="o", s=34, color=c, zorder=5)
        for x, y, lab in ((px, py, "P"), (cx, cy, "C"), (tx, ty, "B")):
            ax.text(x + 0.022, y, lab, fontsize=8, color=INK)
        ax.set_aspect("equal")
        ax.set_xlim(-0.34, 0.26)
        ax.set_ylim(-0.34, 0.38)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        style(ax, "", grid=None)
        ax.set_title("#%s  %s\nreach %.0f mm"
                     % (r["set_id"], r["difficulty"],
                        1000 * float(r["reach_distance"])),
                     fontsize=8.5, color=INK, pad=6)
    fig.suptitle("Per-set layouts   P plate · C cookie box · B target bowl",
                 x=0.06, y=0.995, ha="left", fontsize=14, fontweight="bold",
                 color=INK)
    save(fig, "setup-grid.png")


def ctrl_at(r):
    if r <= CONTROL[0][0]:
        return CONTROL[0][1]
    for (a, fa), (b, fb) in zip(CONTROL, CONTROL[1:]):
        if r <= b:
            return fa + (fb - fa) * (r - a) / (b - a)
    return CONTROL[-1][1]


def main():
    run2 = load("episodes_run2.csv")
    layout = load("layout2_results.csv")
    fig_funnel(run2)
    fig_run_compare()
    fig_thresholds(run2)
    fig_reach(run2)
    fig_control()
    fig_proximity()
    fig_layout(layout)
    fig_calibration()
    fig_reach_success(load("reach_results.csv"))
    setups = load("layout2_setups.csv")
    fig_setup_map(setups)
    fig_setup_grid(setups)


if __name__ == "__main__":
    main()
