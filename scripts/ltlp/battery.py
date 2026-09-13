"""Stage: battery-analyze. Phrase-level, family-level and cross-phrase analysis.

`analyze.py` computes every contrast this repository knows how to compute, for one
experiment, and applies the multiplicity structure of a four-condition ladder. A battery
asks three further questions that a ladder never has to:

  1. which of many phrases worked, corrected for having looked at many of them;
  2. whether a behavioural FAMILY moves the numbers when its member phrases are pooled,
     which is the only way to say anything about a family rather than about one phrase;
  3. whether appending a phrase AND an effort instruction beats the instruction alone by
     more than appending irrelevant filler and the same instruction does.

Every contrast here is computed with `analyze.contrast_for` and `stats`, never with a second
implementation, so a number in the battery report and a number in `summary.json` cannot
disagree about what a paired difference is.

Nothing in this module chooses a threshold after seeing a result. The decision rule, the
classification table and all three multiplicity levels are fixed in PREREGISTRATION.md.
"""
from __future__ import annotations

import collections
import csv
import os
from typing import Any, Dict, List, Optional

from . import analyze, indicators, judge, manifest, runner, stats, util

PRIMARY = "judge_%s" % analyze.PRIMARY          # judge_task_success
CONFIRMATORY = "objective_score"
OUTCOMES = [PRIMARY, CONFIRMATORY]
ALPHA = 0.05
FDR_Q = 0.05

# The three references every treatment arm is measured against.
CORE_REFERENCES = ["A", "B", "D"]


# --------------------------------------------------------------------------- helpers

def _demonstrated(contrast: Dict[str, Any], adj_p: Optional[float]) -> str:
    """Apply the pre-registered decision rule to one contrast.

    Returns "treatment", "reference" or "not_demonstrated". A contrast counts only if the
    direction, the interval and the adjusted p all agree; a positive-looking difference
    whose interval spans zero is a direction, never an effect.
    """
    diff = contrast.get("task_level_mean_difference")
    ci = contrast.get("ci95_task_level")
    if diff is None or not contrast.get("n_pairs"):
        return "not_demonstrated"
    excludes_zero = bool(ci) and (ci[0] > 0 or ci[1] < 0)
    significant = adj_p is not None and adj_p < ALPHA
    if not (excludes_zero and significant):
        return "not_demonstrated"
    return "treatment" if diff > 0 else "reference" if diff < 0 else "not_demonstrated"


def _task_level_diffs(cells, treatment: str, reference: str) -> Dict[str, float]:
    """Mean paired difference per task, pairing inside (task, repetition) cells."""
    per_task: Dict[str, List[float]] = collections.defaultdict(list)
    for (task_id, _rep), by_cond in cells.items():
        if treatment in by_cond and reference in by_cond:
            per_task[task_id].append(by_cond[treatment] - by_cond[reference])
    return {t: stats.mean(v) for t, v in per_task.items() if v}


def _test_task_level(values_by_task: Dict[str, float], *, seed: int, key: str) -> Dict[str, Any]:
    """Bootstrap interval, exact sign-flip p and dz over task-level values.

    Identical machinery to `analyze._contrast`; the difference is only that the task-level
    values are supplied rather than derived from one pair of conditions, which is what lets
    a family pool its member arms and a combo arm be compared against the placebo combo.
    """
    vals = [v for v in values_by_task.values() if v is not None]
    if not vals:
        return {"n_tasks": 0}
    s = manifest.derived_seed(seed, key)
    ci = stats.cluster_bootstrap_ci([[v] for v in vals], seed=s)
    return {
        "n_tasks": len(vals),
        "task_level_mean_difference": stats.mean(vals),
        "ci95_task_level": list(ci) if ci else None,
        "cohens_dz_task_level": stats.cohens_dz(vals),
        "p_permutation_task_level": stats.paired_permutation_test(vals, seed=s),
        # Consistency: the share of tasks pointing the same way as the point estimate.
        "tasks_favouring_treatment": sum(1 for v in vals if v > 0),
        "tasks_favouring_reference": sum(1 for v in vals if v < 0),
        "tasks_tied": sum(1 for v in vals if v == 0),
    }


def _consistency(values_by_task: Dict[str, float]) -> Optional[float]:
    """Share of DISCRIMINATING tasks that agree with the overall direction.

    Tied tasks are excluded from the denominator. On a saturated measure most tasks tie, and
    counting them would report a real, perfectly consistent effect on five tasks as 25%
    consistent. Experiment 001 measured that saturation on this task set; see
    PREREGISTRATION.md section 4.1.
    """
    vals = [v for v in values_by_task.values() if v is not None and v != 0]
    if not vals:
        return None
    m = stats.mean(vals)
    if m == 0:
        return None
    agree = sum(1 for v in vals if (v > 0) == (m > 0))
    return agree / len(vals)


# --------------------------------------------------------------------------- main

def run(cfg) -> Dict[str, Any]:
    cfg.verify_spec_lock()
    summary_path = cfg.p("analysis", "summary.json")
    if not os.path.exists(summary_path):
        raise RuntimeError("no analysis/summary.json - run the analyze stage first")
    summary = util.read_json(summary_path)
    registry = util.read_json(cfg.spec_paths["phrases"])
    rows = analyze.build_rows(cfg)

    arms = {c["id"]: c for c in cfg.conditions}
    treatments = [t for t in registry["treatments"] if t["id"] in arms]
    combos = [k for k in registry["combos"] if k["id"] in arms]
    families = {f["id"]: f for f in registry["families"]}

    cells = {m: analyze.cells_for(rows, m) for m in OUTCOMES}
    task_family = {r["task_id"]: r["family"] for r in rows}
    task_families = sorted(set(task_family.values()))

    # ---------------------------------------------------------------- 1. battery FDR
    # Level 2 multiplicity: BH across all core contrasts, per outcome. Computed first
    # because the per-phrase record carries each contrast's q value.
    core_ids = ["%s_vs_%s" % (t["id"], r) for t in treatments for r in CORE_REFERENCES]
    battery_fdr: Dict[str, Dict[str, Optional[float]]] = {}
    for metric in OUTCOMES:
        pvals = {cid: summary["contrasts"][metric].get(cid, {}).get("p_permutation_task_level")
                 for cid in core_ids}
        battery_fdr[metric] = stats.benjamini_hochberg(pvals)

    # ---------------------------------------------------------------- 2. per phrase
    echo_by_arm = collections.Counter()
    n_by_arm = collections.Counter()
    for r in rows:
        n_by_arm[r["condition_id"]] += 1
        if r["condition_echo"]:
            echo_by_arm[r["condition_id"]] += 1

    phrases: Dict[str, Any] = {}
    for t in treatments:
        aid = t["id"]
        rec: Dict[str, Any] = {
            "arm_id": aid,
            "phrase": t["phrase"],
            "role": t.get("role", "treatment"),
            "family": t["family"],
            "family_name": families[t["family"]]["name"],
            "secondary_family": t.get("secondary_family"),
            "secondary_family_name": (families[t["secondary_family"]]["name"]
                                      if t.get("secondary_family") else None),
            "hypothesis": t["hypothesis"],
            "mechanism": t["mechanism"],
            "suffix_chars": len(arms[aid]["suffix"]),
            "n_generations": n_by_arm[aid],
            "condition_echo_count": echo_by_arm[aid],
            "contrasts": {},
            "by_task_family": {},
        }

        # Level 1 multiplicity, the decision rule: Holm within this arm's own three
        # contrasts, separately per outcome. Byte-for-byte the rule Experiment 001 used.
        for metric in OUTCOMES:
            pvals = {}
            for ref in CORE_REFERENCES:
                cid = "%s_vs_%s" % (aid, ref)
                pvals[cid] = summary["contrasts"][metric].get(cid, {}).get(
                    "p_permutation_task_level")
            holm = stats.holm(pvals)
            rec["contrasts"][metric] = {}
            for ref in CORE_REFERENCES:
                cid = "%s_vs_%s" % (aid, ref)
                c = dict(summary["contrasts"][metric].get(cid, {}))
                diffs = _task_level_diffs(cells[metric], aid, ref)
                c["holm_p_within_phrase"] = holm.get(cid)
                c["bh_q_across_battery"] = battery_fdr[metric].get(cid)
                c["verdict"] = _demonstrated(c, holm.get(cid))
                c["survives_battery_fdr"] = (
                    battery_fdr[metric].get(cid) is not None
                    and battery_fdr[metric][cid] < FDR_Q)
                c["consistency_across_discriminating_tasks"] = _consistency(diffs)
                c["discriminating_tasks"] = sum(1 for v in diffs.values() if v)
                rec["contrasts"][metric][cid] = c

        # Per task family, against the empty control. Reported for both outcomes; the
        # best/worst labels use the objective score because it is the measure with
        # headroom on this task set.
        for metric in OUTCOMES:
            diffs = _task_level_diffs(cells[metric], aid, "A")
            per_fam = collections.defaultdict(list)
            for tid, v in diffs.items():
                per_fam[task_family[tid]].append(v)
            rec["by_task_family"][metric] = {
                f: stats.mean(per_fam.get(f, [])) for f in task_families}
        obj_fam = {f: v for f, v in rec["by_task_family"][CONFIRMATORY].items()
                   if v is not None}
        rec["best_task_family_objective"] = (max(obj_fam, key=obj_fam.get)
                                             if obj_fam else None)
        rec["worst_task_family_objective"] = (min(obj_fam, key=obj_fam.get)
                                              if obj_fam else None)

        pw = summary["pairwise"].get("%s_vs_A" % aid, {})
        rec["pairwise_vs_A"] = {
            "n": pw.get("n"), "wins": pw.get("treatment_wins"),
            "losses": pw.get("reference_wins"), "ties": pw.get("ties"),
            "win_rate_excluding_ties": pw.get("treatment_win_rate_excluding_ties"),
            "ci95": pw.get("ci95_win_rate"),
            "p_binomial": pw.get("p_binomial_excluding_ties"),
        }

        rec["classification"], rec["classification_reason"], rec["caveats"] = _classify(rec)
        phrases[aid] = rec

    # ---------------------------------------------------------------- 3. families
    family_results: Dict[str, Any] = {}
    for fid, fam in families.items():
        members = [t["id"] for t in treatments if t["family"] == fid]
        entry = {
            "family_id": fid, "name": fam["name"], "definition": fam["definition"],
            "family_hypothesis": fam["family_hypothesis"],
            "members": members, "n_members": len(members),
            "note": ("Shared control arms A, B and D are references in this battery, not "
                     "pooled members, even where they belong to this family by definition."),
            "contrasts": {},
        }
        for metric in OUTCOMES:
            entry["contrasts"][metric] = {}
            for ref in CORE_REFERENCES:
                # Pool by averaging member arms WITHIN each task, then treat the task as
                # the unit. Concatenating arms instead would count one task many times and
                # report an interval that is too narrow.
                per_task = collections.defaultdict(list)
                for aid in members:
                    for tid, v in _task_level_diffs(cells[metric], aid, ref).items():
                        per_task[tid].append(v)
                pooled = {t: stats.mean(v) for t, v in per_task.items() if v}
                res = _test_task_level(pooled, seed=cfg.seed,
                                       key="family:%s:%s:%s" % (fid, ref, metric))
                res["consistency_across_discriminating_tasks"] = _consistency(pooled)
                entry["contrasts"][metric]["%s_vs_%s" % (fid, ref)] = res
        family_results[fid] = entry

    # Level 3 multiplicity: BH across the nine families, per outcome, on the vs_A contrast.
    family_fdr: Dict[str, Dict[str, Optional[float]]] = {}
    for metric in OUTCOMES:
        pvals = {fid: family_results[fid]["contrasts"][metric]["%s_vs_A" % fid].get(
            "p_permutation_task_level") for fid in family_results}
        family_fdr[metric] = stats.benjamini_hochberg(pvals)
        for fid in family_results:
            c = family_results[fid]["contrasts"][metric]["%s_vs_A" % fid]
            c["bh_q_across_families"] = family_fdr[metric].get(fid)
            c["survives_family_fdr"] = (family_fdr[metric].get(fid) is not None
                                        and family_fdr[metric][fid] < FDR_Q)

    # ---------------------------------------------------------------- 4. combos
    placebo_combo = next((k["id"] for k in combos
                          if next(t for t in treatments if t["id"] == k["phrase_arm"]
                                  ).get("role") == "placebo"), None)
    placebo_lift = {}
    if placebo_combo:
        for metric in OUTCOMES:
            placebo_lift[metric] = _task_level_diffs(cells[metric], placebo_combo, "D")

    combo_results: Dict[str, Any] = {}
    for k in combos:
        kid, parent = k["id"], k["phrase_arm"]
        p = next(t for t in treatments if t["id"] == parent)
        entry = {
            "arm_id": kid, "phrase_arm": parent, "phrase": p["phrase"],
            "family": p["family"], "family_name": families[p["family"]]["name"],
            "role": "placebo_combo" if kid == placebo_combo else "combo",
            "suffix_chars": len(arms[kid]["suffix"]),
            "contrasts": {},
        }
        for metric in OUTCOMES:
            entry["contrasts"][metric] = {}
            for ref in ("D", parent, "A"):
                cid = "%s_vs_%s" % (kid, ref)
                entry["contrasts"][metric][cid] = dict(
                    summary["contrasts"][metric].get(cid, {}))
            # The question the placebo combo exists to answer: does THIS phrase plus the
            # instruction beat the instruction by more than irrelevant filler plus the
            # same instruction does? A difference in differences at the task level.
            if placebo_combo and kid != placebo_combo:
                own = _task_level_diffs(cells[metric], kid, "D")
                ref_lift = placebo_lift.get(metric, {})
                did = {t: own[t] - ref_lift[t] for t in own if t in ref_lift}
                entry["contrasts"][metric]["%s_vs_%s_lift_over_placebo" % (kid, placebo_combo)] = \
                    _test_task_level(did, seed=cfg.seed,
                                     key="did:%s:%s" % (kid, metric))
        combo_results[kid] = entry

    # ---------------------------------------------------------------- 5. leaderboards
    def _lb_key(rec):
        v = rec["contrasts"][PRIMARY]["%s_vs_A" % rec["arm_id"]].get(
            "task_level_mean_difference")
        o = rec["contrasts"][CONFIRMATORY]["%s_vs_A" % rec["arm_id"]].get(
            "task_level_mean_difference")
        return (-(v if v is not None else -9e9), -(o if o is not None else -9e9))

    leaderboard = [_lb_row(r) for r in sorted(phrases.values(), key=_lb_key)]
    family_leaderboard = _family_lb(family_results)

    doc = {
        "run_id": cfg.run_id,
        "mode": cfg.mode,
        "analysed_at": runner.now_iso(),
        "experiment_id": registry["experiment_id"],
        "primary_outcome": PRIMARY,
        "confirmatory_outcome": CONFIRMATORY,
        "alpha": ALPHA,
        "fdr_q": FDR_Q,
        "multiplicity": {
            "level_1_decision_rule": "Holm within each phrase's own three core contrasts",
            "level_2_screening": "Benjamini-Hochberg across all %d core contrasts" % len(core_ids),
            "level_3_families": "Benjamini-Hochberg across the %d families" % len(families),
            "also_reported": ("summary.json carries a battery-wide Holm across every primary "
                              "contrast; it is the most conservative view and is reported, "
                              "not the decision rule"),
        },
        "counts": {
            "arms": len(cfg.conditions),
            "treatment_arms": len(treatments),
            "combo_arms": len(combos),
            "families": len(families),
            "core_contrasts": len(core_ids),
            "generations": summary["counts"]["generations_present"],
            "blind_judged": summary["counts"]["blind_judged"],
            "pairwise_judged": summary["counts"]["pairwise_judged"],
            "tasks": summary["counts"]["tasks"],
            "repetitions": summary["counts"]["repetitions"],
        },
        "arm_means": {m: summary["conditions"][m] for m in OUTCOMES},
        "indicator_means": {f: summary["conditions"].get(f, {})
                            for f in indicators.INDICATOR_FIELDS},
        "judge_dimension_means": {"judge_%s" % d: summary["conditions"].get("judge_%s" % d, {})
                                  for d in judge.DIMENSIONS},
        "phrases": phrases,
        "families": family_results,
        "combos": combo_results,
        "placebo_combo": placebo_combo,
        "battery_fdr": battery_fdr,
        "family_fdr": family_fdr,
        "leaderboard": leaderboard,
        "family_leaderboard": family_leaderboard,
        "blinding": summary["blinding"],
        "echo_by_arm": {a: {"n": n_by_arm[a], "echoes": echo_by_arm[a]}
                        for a in sorted(n_by_arm)},
        "seed": cfg.seed,
        "spec_lock": summary["spec_lock"],
        "run_meta": summary["run_meta"],
    }

    util.ensure_dir(cfg.p("analysis"))
    util.write_json(cfg.p("analysis", "battery_summary.json"), doc)
    _write_phrase_csv(cfg, doc)
    _write_family_csv(cfg, doc)
    runner.record_stage(cfg, "battery-analyze",
                        {"stage": "battery-analyze", "phrases": len(phrases),
                         "families": len(family_results), "combos": len(combo_results),
                         "finished_at": runner.now_iso()})
    return doc


def _classify(rec: Dict[str, Any]):
    """Apply the pre-registered classification table. Numbers in, label out."""
    aid = rec["arm_id"]
    prim = rec["contrasts"][PRIMARY]
    vs = {ref: prim["%s_vs_%s" % (aid, ref)] for ref in CORE_REFERENCES}
    if not any(v.get("n_pairs") for v in vs.values()):
        return "Inconclusive", "no contrast could be computed", []

    won = [r for r in CORE_REFERENCES if vs[r]["verdict"] == "treatment"]
    lost = [r for r in CORE_REFERENCES if vs[r]["verdict"] == "reference"]
    caveats = ["%s_vs_%s favours the reference and meets the decision rule" % (aid, r)
               for r in lost]

    if lost and "A" not in won:
        return ("Negative",
                "a contrast meets the decision rule in the reference's favour (%s) and the "
                "phrase does not beat the empty control"
                % ", ".join("%s_vs_%s" % (aid, r) for r in lost), caveats)
    if "A" in won:
        active = [r for r in won if r in ("B", "D")]
        if active and vs["A"].get("survives_battery_fdr"):
            return ("Positive",
                    "beats the empty control, beats %s, and survives the battery-wide FDR "
                    "correction for having screened many phrases"
                    % " and ".join("condition %s" % r for r in active), caveats)
        why = []
        if not active:
            why.append("it does not beat either active control, so the effect belongs to "
                       "appended text rather than to this phrase")
        if not vs["A"].get("survives_battery_fdr"):
            why.append("it does not survive the battery-wide FDR correction")
        return "Weak positive", "beats the empty control, but " + " and ".join(why), caveats
    if won:
        return ("Weak positive",
                "meets the decision rule against %s but not against the empty control"
                % ", ".join("condition %s" % r for r in won), caveats)
    return "Neutral", "no contrast meets the decision rule in either direction", caveats


def _lb_row(rec: Dict[str, Any]) -> Dict[str, Any]:
    aid = rec["arm_id"]
    row = {"arm_id": aid, "phrase": rec["phrase"], "role": rec["role"],
           "family": rec["family"], "family_name": rec["family_name"],
           "classification": rec["classification"]}
    for ref in CORE_REFERENCES:
        cid = "%s_vs_%s" % (aid, ref)
        row["primary_vs_%s" % ref] = rec["contrasts"][PRIMARY][cid].get(
            "task_level_mean_difference")
        row["objective_vs_%s" % ref] = rec["contrasts"][CONFIRMATORY][cid].get(
            "task_level_mean_difference")
    row["primary_ci_vs_A"] = rec["contrasts"][PRIMARY]["%s_vs_A" % aid].get("ci95_task_level")
    row["holm_p_vs_A"] = rec["contrasts"][PRIMARY]["%s_vs_A" % aid].get("holm_p_within_phrase")
    row["bh_q_vs_A"] = rec["contrasts"][PRIMARY]["%s_vs_A" % aid].get("bh_q_across_battery")
    row["win_rate_vs_A"] = rec["pairwise_vs_A"].get("win_rate_excluding_ties")
    row["best_task_family"] = rec["best_task_family_objective"]
    row["worst_task_family"] = rec["worst_task_family_objective"]
    row["consistency_vs_A"] = rec["contrasts"][PRIMARY]["%s_vs_A" % aid].get(
        "consistency_across_discriminating_tasks")
    return row


def _family_lb(family_results) -> List[Dict[str, Any]]:
    out = []
    for fid, f in family_results.items():
        c = f["contrasts"][PRIMARY]["%s_vs_A" % fid]
        o = f["contrasts"][CONFIRMATORY]["%s_vs_A" % fid]
        out.append({
            "family_id": fid, "name": f["name"], "n_members": f["n_members"],
            "primary_vs_A": c.get("task_level_mean_difference"),
            "primary_ci_vs_A": c.get("ci95_task_level"),
            "primary_bh_q": c.get("bh_q_across_families"),
            "objective_vs_A": o.get("task_level_mean_difference"),
            "objective_ci_vs_A": o.get("ci95_task_level"),
            "objective_bh_q": o.get("bh_q_across_families"),
            "primary_vs_B": f["contrasts"][PRIMARY]["%s_vs_B" % fid].get(
                "task_level_mean_difference"),
            "primary_vs_D": f["contrasts"][PRIMARY]["%s_vs_D" % fid].get(
                "task_level_mean_difference"),
            "objective_vs_B": f["contrasts"][CONFIRMATORY]["%s_vs_B" % fid].get(
                "task_level_mean_difference"),
            "objective_vs_D": f["contrasts"][CONFIRMATORY]["%s_vs_D" % fid].get(
                "task_level_mean_difference"),
            "consistency_vs_A": c.get("consistency_across_discriminating_tasks"),
        })
    out.sort(key=lambda r: -(r["objective_vs_A"] if r["objective_vs_A"] is not None else -9e9))
    return out


def _write_phrase_csv(cfg, doc) -> None:
    path = cfg.p("analysis", "phrase_results.csv")
    fields = ["run_id", "arm_id", "phrase", "role", "family", "family_name",
              "classification", "primary_vs_A", "primary_vs_B", "primary_vs_D",
              "objective_vs_A", "objective_vs_B", "objective_vs_D",
              "primary_ci_low_vs_A", "primary_ci_high_vs_A", "holm_p_vs_A", "bh_q_vs_A",
              "win_rate_vs_A", "consistency_vs_A", "best_task_family", "worst_task_family"]
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in doc["leaderboard"]:
            ci = row.get("primary_ci_vs_A") or [None, None]
            out = dict(row, run_id=doc["run_id"],
                       primary_ci_low_vs_A=ci[0], primary_ci_high_vs_A=ci[1])
            w.writerow(out)


def _write_family_csv(cfg, doc) -> None:
    path = cfg.p("analysis", "family_results.csv")
    fields = ["run_id", "family_id", "name", "n_members",
              "primary_vs_A", "primary_ci_low", "primary_ci_high", "primary_bh_q",
              "objective_vs_A", "objective_ci_low", "objective_ci_high", "objective_bh_q",
              "primary_vs_B", "primary_vs_D", "objective_vs_B", "objective_vs_D",
              "consistency_vs_A"]
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in doc["family_leaderboard"]:
            pci = row.get("primary_ci_vs_A") or [None, None]
            oci = row.get("objective_ci_vs_A") or [None, None]
            w.writerow(dict(row, run_id=doc["run_id"],
                            primary_ci_low=pci[0], primary_ci_high=pci[1],
                            objective_ci_low=oci[0], objective_ci_high=oci[1]))
