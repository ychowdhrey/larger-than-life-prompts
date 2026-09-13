#!/usr/bin/env python3
"""Regenerate the repository's PHRASES.csv from completed experiment results.

PHRASES.csv is the index of every phrase this repository has tested. Its `impact` and
`confidence` columns are conclusions, and a conclusion typed by hand next to a number
computed by a script is a conclusion free to drift from it. So the file is generated: the
impact label comes from the battery's own classification, and the confidence stage follows
one stated rule rather than a judgement call per row.

Confidence follows METHODOLOGY.md's ladder. "Tested" is defined there as "survived an
initial controlled evaluation", so it is awarded only where a controlled evaluation
actually produced a finding to carry:

    Positive / Weak positive / Negative  ->  Tested    (a demonstrated effect exists)
    Neutral / Inconclusive               ->  Observed  (nothing survived to carry up)

That is the rule Experiment 001 applied to itself by hand: its result was Neutral and it
stayed at Observed, because "there is simply no effect to carry up the ladder".

Usage:
    python3 scripts/update_phrases_csv.py            # rewrite PHRASES.csv
    python3 scripts/update_phrases_csv.py --check    # exit 1 if it is out of date
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(REPO, "PHRASES.csv")

FIELDS = ["id", "phrase", "category", "situation", "position", "impact",
          "confidence", "model", "runs", "eval_link"]

SITUATION = "Reasoning, critique, planning, writing"
POSITION = "End of prompt"

TESTED = {"Positive", "Weak positive", "Negative"}


def confidence_for(impact: str) -> str:
    return "Tested" if impact in TESTED else "Observed"


def rows_from_experiment_001() -> list:
    """Experiment 001 predates the battery and has no battery_summary.json.

    Its row is read from its own results rather than restated: the impact label it
    concluded is Neutral, and the run size comes from the run's analysis.
    """
    path = os.path.join(REPO, "experiments", "001-may-the-force-be-with-you",
                        "runs", "full-001", "analysis", "summary.json")
    if not os.path.exists(path):
        return []
    s = json.load(open(path, encoding="utf-8"))
    c = s["contrasts"]["judge_task_success"]
    holm = s["holm_adjusted_primary_contrasts"]["judge_task_success"]
    demonstrated = any(
        (c[cid].get("ci95_task_level") or [0, 0])[0] > 0
        and (holm.get(cid) or 1) < 0.05
        for cid in c if cid.startswith("C_vs_"))
    impact = "Positive" if demonstrated else "Neutral"
    return [{
        "id": "001",
        "phrase": s["run_meta"]["phrase"],
        "category": "Motivational cinematic framing",
        "situation": SITUATION,
        "position": POSITION,
        "impact": impact,
        "confidence": confidence_for(impact),
        "model": s["run_meta"]["generation"]["model"],
        "runs": s["counts"]["generations_present"],
        "eval_link": "experiments/001-may-the-force-be-with-you/",
    }]


def rows_from_battery(run_dir: str, exp_link: str) -> list:
    path = os.path.join(run_dir, "analysis", "battery_summary.json")
    if not os.path.exists(path):
        return []
    doc = json.load(open(path, encoding="utf-8"))
    if doc.get("mode") == "pilot":
        raise SystemExit("refusing to index a pilot run: a pilot is not evidence")
    if (doc.get("run_meta", {}).get("generation", {}) or {}).get("backend") == "mock":
        raise SystemExit("refusing to index a mock run: synthetic output is never a result")
    model = doc["run_meta"]["generation"]["model"]
    per_arm = doc["counts"]["tasks"] * doc["counts"]["repetitions"]
    out = []
    for rec in sorted(doc["phrases"].values(), key=lambda r: r["arm_id"]):
        impact = rec["classification"]
        out.append({
            "id": "%s-%s" % (doc["experiment_id"], rec["arm_id"]),
            "phrase": rec["phrase"],
            "category": rec["family_name"],
            "situation": SITUATION,
            "position": POSITION,
            "impact": impact,
            "confidence": confidence_for(impact),
            "model": model,
            "runs": per_arm,
            "eval_link": exp_link,
        })
    return out


def build() -> str:
    rows = rows_from_experiment_001()
    rows += rows_from_battery(
        os.path.join(REPO, "experiments", "002-phrase-battery", "runs", "full-002"),
        "experiments/002-phrase-battery/")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    payload = build()
    if args.check:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != payload:
            print("PHRASES.csv is out of date; run scripts/update_phrases_csv.py",
                  file=sys.stderr)
            return 1
        print("PHRASES.csv is current")
        return 0
    open(OUT, "w", encoding="utf-8").write(payload)
    print("wrote PHRASES.csv (%d phrase rows)" % (payload.count("\n") - 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
