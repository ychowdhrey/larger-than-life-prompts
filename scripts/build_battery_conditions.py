#!/usr/bin/env python3
"""Generate experiments/002-phrase-battery/conditions.json from phrases.json.

conditions.json is a spec file: it is hashed into spec.lock.json at prepare time and can
never be edited once a run has produced generations. It is generated rather than written by
hand so that the arm list, the combo suffixes and the contrast list cannot drift away from
the registry that documents them.

`--check` re-derives the file and exits non-zero if the committed copy differs. That is what
scripts/tests/test_battery_conditions.py asserts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXP = os.path.join(REPO, "experiments", "002-phrase-battery")
PHRASES = os.path.join(EXP, "phrases.json")
CONDITIONS = os.path.join(EXP, "conditions.json")

# The three references every treatment arm is measured against, mirroring Experiment 001.
CORE_REFERENCES = [
    ("A", "Does the phrase beat no added text?"),
    ("B", "Does it beat generic encouragement?"),
    ("D", "Does it beat an explicit effort instruction?"),
]


def build(reg: dict) -> dict:
    conditions = []
    for c in reg["shared_controls"]:
        conditions.append({"id": c["id"], "name": c["name"], "role": c["role"],
                           "family": c["family"], "suffix": c["suffix"]})

    effort = next(c["suffix"] for c in reg["shared_controls"] if c["id"] == "D")
    by_id = {t["id"]: t for t in reg["treatments"]}

    for t in reg["treatments"]:
        conditions.append({
            "id": t["id"], "name": "phrase_%s" % t["id"].lower(),
            "role": t.get("role", "treatment"),
            "family": t["family"], "suffix": t["phrase"],
        })
    for k in reg["combos"]:
        parent = by_id[k["phrase_arm"]]
        conditions.append({
            "id": k["id"], "name": "combo_%s" % k["id"].lower(),
            "role": "combo", "family": parent["family"],
            "phrase_arm": k["phrase_arm"],
            # phrase then the canonical effort instruction, one space between them
            "suffix": "%s %s" % (parent["phrase"], effort),
        })

    primary, pairwise = [], []
    for t in reg["treatments"]:
        for ref, question in CORE_REFERENCES:
            cid = "%s_vs_%s" % (t["id"], ref)
            primary.append({"id": cid, "treatment": t["id"], "reference": ref,
                            "phrase_arm": t["id"], "question": question})
            if ref == "A":
                pairwise.append({"id": cid, "treatment": t["id"], "reference": ref,
                                 "question": question})

    secondary = [
        {"id": "B_vs_A", "treatment": "B", "reference": "A"},
        {"id": "D_vs_A", "treatment": "D", "reference": "A"},
    ]
    for k in reg["combos"]:
        parent = k["phrase_arm"]
        secondary.append({"id": "%s_vs_D" % k["id"], "treatment": k["id"], "reference": "D",
                          "question": "Does the phrase add anything on top of a plain effort instruction?"})
        secondary.append({"id": "%s_vs_%s" % (k["id"], parent), "treatment": k["id"],
                          "reference": parent,
                          "question": "Does the effort instruction add anything on top of the phrase?"})
        secondary.append({"id": "%s_vs_A" % k["id"], "treatment": k["id"], "reference": "A"})

    return {
        "version": "1.0.0",
        "experiment_id": "002",
        "generated_by": "scripts/build_battery_conditions.py from phrases.json",
        "independent_variable": "text appended to the end of an otherwise identical base task prompt",
        "join": "\n\n",
        "note": ("The base prompt is byte-identical across every arm. The ONLY difference is "
                 "the appended suffix. Condition A appends nothing at all (no join, no "
                 "trailing whitespace). Arms A, B and D are byte-identical to Experiment "
                 "001's conditions A, B and D and are shared across every treatment "
                 "comparison in this battery."),
        "shared_control_note": ("A, B and D are generated once and serve as the reference for "
                                "all %d treatment arms. Execution order is shuffled globally "
                                "from the master seed, so control and treatment generations "
                                "are interleaved in time and no arm sits in its own time "
                                "window. The cost is that contrasts sharing a reference are "
                                "statistically correlated with one another; that affects "
                                "across-phrase claims, not the within-phrase paired tests, "
                                "and is handled by the battery-level FDR control declared in "
                                "PREREGISTRATION.md." % len(reg["treatments"])),
        "conditions": conditions,
        "primary_contrasts": primary,
        "pairwise_contrasts": pairwise,
        "pairwise_note": ("Pairwise preference is a SECONDARY outcome and is scoped, before "
                          "any run, to each treatment arm against the empty control. That is "
                          "the contrast the project's premise actually makes a claim about. "
                          "The vs-B and vs-D questions are decided on the primary outcome and "
                          "the objective score, which is where the pre-registered decision "
                          "rule lives in Experiment 001 too."),
        "secondary_contrasts": secondary,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the committed conditions.json differs")
    args = ap.parse_args()

    with open(PHRASES, encoding="utf-8") as fh:
        reg = json.load(fh)
    doc = build(reg)
    payload = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not os.path.exists(CONDITIONS):
            print("conditions.json does not exist", file=sys.stderr)
            return 1
        with open(CONDITIONS, encoding="utf-8") as fh:
            current = fh.read()
        if current != payload:
            print("conditions.json is not what phrases.json generates", file=sys.stderr)
            return 1
        print("conditions.json matches phrases.json")
        return 0

    with open(CONDITIONS, "w", encoding="utf-8") as fh:
        fh.write(payload)
    print("wrote %s" % os.path.relpath(CONDITIONS, REPO))
    print("  %d arms, %d primary contrasts, %d pairwise contrasts, %d secondary contrasts"
          % (len(doc["conditions"]), len(doc["primary_contrasts"]),
             len(doc["pairwise_contrasts"]), len(doc["secondary_contrasts"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
