#!/usr/bin/env python3
"""Parse run logs into data/episodes.csv.

Usage
    python3 scripts/mkcsv.py --runs <runs_dir> --out data/episodes.csv

Expects one directory per condition named b0 .. b9 (task index), each holding
log_r1.txt .. log_rN.txt. One CSV row per episode.
"""

import argparse
import csv
import glob
import os
import re

SCALARS = ("steps", "dPlate", "bowlz", "maxlift", "peaklift", "pmove", "refok",
           "refpm", "holdd", "holdz", "retq", "btilt", "bzmin", "bimp", "bpen",
           "pmax", "bpush", "slip", "ltilt", "ikfail", "rotacc", "nclose", "ok")
PAT = {k: re.compile(k + r"=([-+\d.]+)") for k in SCALARS}
RE_CLOSE = re.compile(r"CLOSE at s(\d+) gz=([\d.]+) .*d=\[\s*([-+\d.]+)\s+"
                      r"([-+\d.]+)\s+([-+\d.]+)\]\s+tip-rim=([-+\d.]+)")
RE_DIST = re.compile(r"distmax=([\d.]+)\((\w*)\)")
RE_STRICT = re.compile(r"strict=([01])\(([^)]*)\)")
RE_HOLD = re.compile(r"HOLD \d+q:.*drift=([\d.]+)")
RE_EP = re.compile(r"log_r(\d+)")


def parse(path, task):
    text = open(path, errors="ignore").read()
    result = [line for line in text.split("\n") if line.startswith("RESULT")]
    if not result:
        return None
    line = result[-1]
    row = {"task": task, "episode": int(RE_EP.search(path).group(1))}
    for key, pat in PAT.items():
        hit = pat.search(line)
        row[key] = float(hit.group(1)) if hit else ""
    hit = RE_DIST.search(line)
    row["distmax"] = float(hit.group(1)) if hit else ""
    row["distobj"] = hit.group(2) if hit else ""
    hit = RE_STRICT.search(line)
    row["strict"] = int(hit.group(1)) if hit else 0
    row["strict_why"] = hit.group(2) if hit else ""
    hit = RE_CLOSE.search(text)
    row["close_q"] = int(hit.group(1)) if hit else -1
    row["d_x"] = float(hit.group(3)) if hit else ""
    row["d_y"] = float(hit.group(4)) if hit else ""
    row["tip_rim"] = float(hit.group(6)) if hit else ""
    hit = RE_HOLD.search(text)
    row["hold_drift"] = float(hit.group(1)) if hit else ""
    row["lost_n"] = text.count(">>> LOST")
    row["termhold"] = 1 if "TERMHOLD ok" in text else 0
    row["reject_n"] = text.count("TERMHOLD reject")
    holdd = row["holdd"]
    for th in (0.013, 0.020, 0.030, 0.050):
        row["ok%03d" % int(th * 1000)] = int(
            isinstance(holdd, float) and 0 <= holdd < th)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default="data/episodes.csv")
    ap.add_argument("--prefix", default="b")
    args = ap.parse_args()

    rows = []
    for task in range(10):
        pattern = os.path.join(args.runs, "%s%d" % (args.prefix, task),
                               "log_r*.txt")
        for path in sorted(glob.glob(pattern)):
            row = parse(path, task)
            if row:
                rows.append(row)
    if not rows:
        print("no logs found under", args.runs)
        return
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="") as handle:
        writer = csv.DictWriter(handle, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("wrote %s  (%d episodes)" % (args.out, len(rows)))


if __name__ == "__main__":
    main()
