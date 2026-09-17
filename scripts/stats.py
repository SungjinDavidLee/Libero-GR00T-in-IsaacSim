#!/usr/bin/env python3
"""Reproduce every statistical test quoted in README.md.

    python3 scripts/stats.py

Two-proportion comparisons use Fisher's exact test; the 95% confidence interval
on the difference uses Newcombe's hybrid score method. Correlations are reported
as both Pearson and Spearman, with the interval from Fisher's z transform.
"""

import csv
import math
import os
import statistics as st

from scipy.stats import fisher_exact, pearsonr, spearmanr

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def load(name):
    with open(os.path.join(DATA, name), newline="") as fp:
        return list(csv.DictReader(fp))


def num(row, key, default=None):
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return default


def wilson(x, n, z=1.96):
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def newcombe(a, na, b, nb):
    """95% CI on (a/na - b/nb), in percentage points."""
    l1, u1 = wilson(a, na)
    l2, u2 = wilson(b, nb)
    p1, p2 = a / na, b / nb
    lo = (p1 - p2) - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = (p1 - p2) + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return 100 * lo, 100 * hi


def compare(label, a, na, b, nb, name_a, name_b):
    _, p = fisher_exact([[a, na - a], [b, nb - b]])
    lo, hi = newcombe(a, na, b, nb)
    print(label)
    print("  %-22s %3d/%-3d  (%.1f%%)" % (name_a, a, na, 100 * a / na))
    print("  %-22s %3d/%-3d  (%.1f%%)" % (name_b, b, nb, 100 * b / nb))
    print("  차이 %+.1f%%p   95%% CI [%+.1f, %+.1f]   Fisher p = %s"
          % (100 * a / na - 100 * b / nb, lo, hi,
             ("%.2e" % p) if p < 0.001 else ("%.3f" % p)))
    print()


def corr(label, x, y):
    r, pr = pearsonr(x, y)
    rho, ps = spearmanr(x, y)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(len(x) - 3)
    lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    print(label)
    print("  n = %d" % len(x))
    print("  Pearson   r   = %+.3f   p = %.3f   95%% CI [%.2f, %.2f]"
          % (r, pr, lo, hi))
    print("  Spearman  rho = %+.3f   p = %.3f" % (rho, ps))
    print()


def main():
    run1 = load("episodes_run1.csv")
    run2 = load("episodes_run2.csv")
    lay1 = load("layout1_results.csv")
    lay2 = load("layout2_results.csv")

    print("=" * 66)
    print("README 에 인용된 모든 검정값")
    print("=" * 66)
    print()

    # --- 벤치마크 요약 -----------------------------------------------------
    p1 = sum(1 for r in run1 if r["termhold"] == "1")
    p2 = sum(1 for r in run2 if r["termhold"] == "1")
    print("벤치마크 배치 성공")
    print("  1차 %d/%d (%.1f%%)   2차 %d/%d (%.1f%%)"
          % (p1, len(run1), 100 * p1 / len(run1),
             p2, len(run2), 100 * p2 / len(run2)))
    print()

    # --- 1. 방해 물체 유무 (T6 제외) ---------------------------------------
    a = sum(1 for r in run2 if r["task"] != "6" and r["termhold"] == "1")
    na = sum(1 for r in run2 if r["task"] != "6")
    b = sum(1 for r in run1 if r["task"] != "6" and r["termhold"] == "1")
    nb = sum(1 for r in run1 if r["task"] != "6")
    compare("[1] 방해 물체 유무 — T6 제외 9개 태스크",
            a, na, b, nb, "방해 물체 복원", "방해 물체 없음")

    # --- 2. 배치 무작위화 --------------------------------------------------
    la = sum(int(r["S10"]) for r in lay2)
    compare("[2] 배치 무작위화 — 원배치 대비",
            la, len(lay2), p2, len(run2), "무작위 배치", "원배치")

    # --- 3. 난이도 축 ------------------------------------------------------
    for label, rows in (("[3a] 난이도 축 — 기하학적 난이도", lay1),
                        ("[3b] 난이도 축 — 학습 배치 거리", lay2)):
        e = [r for r in rows if r["difficulty"] == "easy"]
        h = [r for r in rows if r["difficulty"] == "hard"]
        compare(label,
                sum(int(r["S10"]) for r in e), len(e),
                sum(int(r["S10"]) for r in h), len(h),
                "쉬움", "변이")

    # --- 4. 방해 물체 근접 -------------------------------------------------
    # 3 태스크 × 4 거리 × 12판. 집계값은 docs/distractor.md 참조.
    compare("[4] 방해 물체 근접 — 배치 성공",
            49, 72, 60, 72, "가까움 (125+160 mm)", "멂 (210+300 mm)")
    compare("[4b] 방해 물체 근접 — 목표 물체 선택",
            68, 72, 72, 72, "가까움 (125+160 mm)", "멂 (210+300 mm)")

    # --- 5. 정렬 오차와 성공 ----------------------------------------------
    lo = [r for r in lay2 if float(r["d_xy"]) <= 0.080]
    hi = [r for r in lay2 if float(r["d_xy"]) > 0.080]
    compare("[5] 파지 정렬 오차와 성공 — 배치 실험 2차",
            sum(int(r["S10"]) for r in lo), len(lo),
            sum(int(r["S10"]) for r in hi), len(hi),
            "정렬 오차 <= 80 mm", "정렬 오차 > 80 mm")

    # --- 6. reach 와 정렬 오차 --------------------------------------------
    per = {}
    for r in run2:
        d = num(r, "d_xy")
        if d is None:
            continue
        per.setdefault(int(r["task"]), []).append((num(r, "reach"), d))
    xs = [per[t][0][0] for t in sorted(per)]
    ys = [st.median(v for _, v in per[t]) for t in sorted(per)]
    corr("[6] 로봇 베이스까지 거리 ~ 정렬 오차 — 태스크 수준 (벤치마크 2차)",
         xs, ys)

    xr = [float(r["reach_distance"]) for r in lay2]
    yr = [float(r["d_xy"]) for r in lay2]
    corr("[7] 같은 상관 — 배치 실험 2차, 세트 수준", xr, yr)

    keep = [r for r in lay2 if float(r["d_xy"]) < 0.20]
    corr("[7b] 같은 상관 — 이상치 1세트 제외",
         [float(r["reach_distance"]) for r in keep],
         [float(r["d_xy"]) for r in keep])

    # --- 8. 성공과의 점이연 상관 ------------------------------------------
    print("[8] 배치 실험 2차 — 성공과의 점이연 상관 (n = %d)" % len(lay2))
    y = [float(r["S10"]) for r in lay2]
    my, sy = st.mean(y), st.pstdev(y)
    for k, lab in (("mean_disp", "학습 배치 거리"),
                   ("d_target", "목표 이동량"),
                   ("d_target_plate", "이송 거리"),
                   ("d_target_cookies", "그릇-과자 거리"),
                   ("path_clearance", "경로 여유"),
                   ("approach_azimuth_deg", "방위각"),
                   ("reach_distance", "베이스까지 거리")):
        v = [float(r[k]) for r in lay2]
        mv, sv = st.mean(v), st.pstdev(v)
        if sv * sy == 0:
            continue
        c = sum((a - mv) * (b - my) for a, b in zip(v, y)) / len(v) / (sv * sy)
        print("  %-16s %+.3f" % (lab, c))
    print()
    print("[8b] 배치 실험 1차 — 성공과의 점이연 상관 (n = %d)" % len(lay1))
    y1 = [float(r["S10"]) for r in lay1]
    my1, sy1 = st.mean(y1), st.pstdev(y1)
    for k, lab in (("transport", "이송 거리"), ("path_clr", "경로 여유"),
                   ("gap", "그릇-과자 거리"), ("azim", "방위각")):
        v = [float(r[k]) for r in lay1]
        mv, sv = st.mean(v), st.pstdev(v)
        if sv * sy1 == 0:
            continue
        c = sum((a - mv) * (b - my1) for a, b in zip(v, y1)) / len(v) / (sv * sy1)
        print("  %-16s %+.3f" % (lab, c))
    print()
    print("  n = 30 유의 기준  |r| > 0.36 (p = 0.05),  |r| > 0.46 (p = 0.01)")
    print()

    # --- 9. 제어 오차 ------------------------------------------------------
    control = [(0.45, 1.41), (0.55, 2.08), (0.62, 2.80),
               (0.68, 3.76), (0.74, 5.35), (0.80, 8.97)]
    corr("[9] 베이스까지 거리 ~ 제어 오차 (정책 미사용)",
         [c[0] for c in control], [c[1] for c in control])


if __name__ == "__main__":
    main()
