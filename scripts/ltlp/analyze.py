"""Stage: analyse. Joins every artifact into per-sample rows and aggregate contrasts.

Pairing structure: a (task, repetition) cell holds one response per condition, so a
contrast is computed as a paired difference within that cell. Those paired differences are
then averaged to the task level, and the task is the unit for both the permutation test and
the bootstrap, because responses to the same task are not independent.
"""
from __future__ import annotations

import collections
import csv
import os
from typing import Any, Dict, List, Optional

from . import generate, indicators, judge, manifest, runner, stats, util

JUDGE_DIMS = judge.DIMENSIONS
PRIMARY = "task_success"


def _load_dir(path: str) -> List[Dict[str, Any]]:
    if not os.path.isdir(path):
        return []
    return [util.read_json(os.path.join(path, n))
            for n in sorted(os.listdir(path)) if n.endswith(".json")]


def build_rows(cfg) -> List[Dict[str, Any]]:
    responses = generate.load_responses(cfg)
    objective_by_sample = {r["sample_id"]: r for r in _load_dir(cfg.p("objective"))}
    blind_by_sample = {r["sample_id"]: r for r in _load_dir(cfg.p("judge", "blind"))}

    rows = []
    for sid in sorted(responses):
        rec = responses[sid]
        obj = objective_by_sample.get(sid, {})
        blind = blind_by_sample.get(sid, {})
        row = {
            "sample_id": sid,
            "run_id": cfg.run_id,
            "task_id": rec["task_id"],
            "family": rec["family"],
            "condition_id": rec["condition_id"],
            "condition_name": rec["condition_name"],
            "repetition": rec["repetition"],
            "model": rec.get("model"),
            "backend": rec.get("backend"),
            "condition_echo": bool(rec.get("condition_echo")),
            "objective_score": (obj.get("objective") or {}).get("objective_score"),
            "earned_points": (obj.get("objective") or {}).get("earned_points"),
            "max_points": (obj.get("objective") or {}).get("max_points"),
            "planted_issue_recall": (obj.get("objective") or {}).get("planted_issue_recall"),
            "distractor_avoidance": (obj.get("objective") or {}).get("distractor_avoidance"),
        }
        for k, v in (obj.get("indicators") or {}).items():
            row[k] = v
        for d in JUDGE_DIMS:
            row["judge_%s" % d] = (blind.get("scores") or {}).get(d)
        rows.append(row)
    return rows


def _cell(rows, metric) -> Dict[tuple, Dict[str, float]]:
    """metric value indexed by (task, rep) -> {condition: value}."""
    cells: Dict[tuple, Dict[str, float]] = collections.defaultdict(dict)
    for r in rows:
        v = r.get(metric)
        if v is not None:
            cells[(r["task_id"], r["repetition"])][r["condition_id"]] = v
    return cells


def _by_condition(rows, metric) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = collections.defaultdict(list)
    for r in rows:
        if r.get(metric) is not None:
            out[r["condition_id"]].append(r[metric])
    return out


def _condition_summary(cfg, rows, metric, seed) -> Dict[str, Any]:
    per_cond = _by_condition(rows, metric)
    out = {}
    for cond in cfg.conditions:
        cid = cond["id"]
        values = per_cond.get(cid, [])
        clusters = collections.defaultdict(list)
        for r in rows:
            if r["condition_id"] == cid and r.get(metric) is not None:
                clusters[r["task_id"]].append(r[metric])
        ci = stats.cluster_bootstrap_ci(
            list(clusters.values()),
            seed=manifest.derived_seed(seed, "cond:%s:%s" % (metric, cid)))
        out[cid] = {
            "condition_name": cond["name"],
            "n": len(values),
            "mean": stats.mean(values),
            "sd": stats.stdev(values),
            "ci95": list(ci) if ci else None,
        }
    return out


def _contrast(cfg, rows, metric, contrast, seed) -> Dict[str, Any]:
    cells = _cell(rows, metric)
    t, ref = contrast["treatment"], contrast["reference"]
    paired = []
    task_diffs: Dict[str, List[float]] = collections.defaultdict(list)
    for (task_id, rep), by_cond in cells.items():
        if t in by_cond and ref in by_cond:
            d = by_cond[t] - by_cond[ref]
            paired.append(d)
            task_diffs[task_id].append(d)
    if not paired:
        return {"contrast_id": contrast["id"], "n_pairs": 0}
    task_level = [stats.mean(v) for v in task_diffs.values()]
    seed_i = manifest.derived_seed(seed, "contrast:%s:%s" % (contrast["id"], metric))
    ci = stats.cluster_bootstrap_ci([[v] for v in task_level], seed=seed_i)
    return {
        "contrast_id": contrast["id"],
        "treatment": t,
        "reference": ref,
        "n_pairs": len(paired),
        "n_tasks": len(task_level),
        "mean_difference": stats.mean(paired),
        "task_level_mean_difference": stats.mean(task_level),
        "ci95_task_level": list(ci) if ci else None,
        "cohens_dz_task_level": stats.cohens_dz(task_level),
        "p_permutation_task_level": stats.paired_permutation_test(task_level, seed=seed_i),
        "favours": ("treatment" if (stats.mean(paired) or 0) > 0
                    else "reference" if (stats.mean(paired) or 0) < 0 else "neither"),
    }


def _pairwise_summary(cfg, seed) -> Dict[str, Any]:
    records = _load_dir(cfg.p("judge", "pairwise"))
    out = {}
    for contrast in cfg.primary_contrasts:
        rs = [r for r in records if r["contrast_id"] == contrast["id"]]
        wins = sum(1 for r in rs if r.get("treatment_won") is True)
        losses = sum(1 for r in rs if r.get("treatment_won") is False)
        ties = sum(1 for r in rs if r.get("tie"))
        decided = wins + losses
        slot_a_pref = sum(1 for r in rs if r.get("preference_slot") == "A")
        ci = stats.wilson_ci(wins, decided) if decided else None
        out[contrast["id"]] = {
            "treatment": contrast["treatment"],
            "reference": contrast["reference"],
            "n": len(rs),
            "treatment_wins": wins,
            "reference_wins": losses,
            "ties": ties,
            "decided": decided,
            "treatment_win_rate_excluding_ties": (wins / decided) if decided else None,
            "ci95_win_rate": list(ci) if ci else None,
            "p_binomial_excluding_ties": (stats.binom_test_two_sided(wins, decided)
                                          if decided else None),
            "slot_a_preference_rate": (slot_a_pref / len(rs)) if rs else None,
        }
    return out


def run(cfg) -> Dict[str, Any]:
    cfg.verify_spec_lock()
    rows = build_rows(cfg)
    if not rows:
        raise RuntimeError("no generations found - run the generate stage first")

    metrics = ["objective_score", "judge_%s" % PRIMARY] + \
              ["judge_%s" % d for d in JUDGE_DIMS if d != PRIMARY] + \
              [m for m in indicators.INDICATOR_FIELDS] + \
              ["planted_issue_recall", "distractor_avoidance"]
    metrics = [m for m in dict.fromkeys(metrics)]

    conditions_summary = {m: _condition_summary(cfg, rows, m, cfg.seed) for m in metrics}
    contrasts: Dict[str, Any] = {}
    all_contrasts = list(cfg.primary_contrasts) + list(cfg.secondary_contrasts)
    for m in metrics:
        contrasts[m] = {c["id"]: _contrast(cfg, rows, m, c, cfg.seed) for c in all_contrasts}

    # Holm correction across the three pre-registered primary contrasts, on the primary
    # outcome and on the objective score.
    holm_families = {}
    for m in ("judge_%s" % PRIMARY, "objective_score"):
        pvals = {c["id"]: contrasts[m][c["id"]].get("p_permutation_task_level")
                 for c in cfg.primary_contrasts}
        holm_families[m] = stats.holm(pvals)

    pairwise = _pairwise_summary(cfg, cfg.seed)

    by_family: Dict[str, Any] = {}
    for fam in sorted({r["family"] for r in rows}):
        fam_rows = [r for r in rows if r["family"] == fam]
        by_family[fam] = {
            "n": len(fam_rows),
            "objective_score": _condition_summary(cfg, fam_rows, "objective_score", cfg.seed),
            "judge_task_success": _condition_summary(cfg, fam_rows, "judge_task_success", cfg.seed),
        }

    manifest_doc = util.read_json(cfg.p("manifest.json"))
    run_meta = util.read_json(cfg.p("run_meta.json"))
    echo_count = sum(1 for r in rows if r["condition_echo"])

    summary = {
        "run_id": cfg.run_id,
        "mode": cfg.mode,
        "analysed_at": runner.now_iso(),
        "primary_outcome": "judge_%s" % PRIMARY,
        "counts": {
            "expected_generations": cfg.expected_generations,
            "generations_present": len(rows),
            "objective_scored": sum(1 for r in rows if r["objective_score"] is not None),
            "blind_judged": sum(1 for r in rows if r["judge_task_success"] is not None),
            "pairwise_judged": sum(v["n"] for v in pairwise.values()),
            "tasks": len(cfg.tasks),
            "conditions": len(cfg.conditions),
            "repetitions": cfg.repetitions,
        },
        "blinding": {
            "condition_echo_count": echo_count,
            "condition_echo_rate": echo_count / len(rows) if rows else None,
            "note": ("A response that repeats its condition's text back could in principle "
                     "be identified by a judge. Outputs are never edited; the rate is "
                     "reported as a confound."),
        },
        "conditions": conditions_summary,
        "contrasts": contrasts,
        "holm_adjusted_primary_contrasts": holm_families,
        "pairwise": pairwise,
        "by_family": by_family,
        "run_meta": run_meta,
        "seed": cfg.seed,
        "spec_lock": util.read_json(cfg.p("spec.lock.json")),
    }

    util.ensure_dir(cfg.p("analysis"))
    util.write_json(cfg.p("analysis", "summary.json"), summary)
    _write_samples_csv(cfg, rows)
    _write_results_csv(cfg, summary, metrics)
    runner.record_stage(cfg, "analyze", {"stage": "analyze", "rows": len(rows),
                                         "finished_at": runner.now_iso()})
    return summary


def _write_samples_csv(cfg, rows) -> None:
    fields = ["run_id", "sample_id", "task_id", "family", "condition_id", "condition_name",
              "repetition", "model", "backend", "condition_echo", "objective_score",
              "earned_points", "max_points", "planted_issue_recall", "distractor_avoidance"] + \
             ["judge_%s" % d for d in JUDGE_DIMS] + \
             [f for f in indicators.INDICATOR_FIELDS if f != "constraint_completion"] + \
             ["constraint_completion"]
    path = cfg.p("analysis", "samples.csv")
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda x: x["sample_id"]):
            w.writerow(r)


def _write_results_csv(cfg, summary, metrics) -> None:
    path = cfg.p("analysis", "results.csv")
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["run_id", "metric", "scope", "condition_or_contrast", "n",
                    "value", "ci_low", "ci_high", "p_value", "effect_size"])
        for metric in metrics:
            for cid, s in summary["conditions"][metric].items():
                ci = s["ci95"] or [None, None]
                w.writerow([cfg.run_id, metric, "condition_mean", cid, s["n"],
                            s["mean"], ci[0], ci[1], "", ""])
            for contrast_id, c in summary["contrasts"][metric].items():
                if not c.get("n_pairs"):
                    continue
                ci = c.get("ci95_task_level") or [None, None]
                w.writerow([cfg.run_id, metric, "contrast", contrast_id, c["n_pairs"],
                            c["mean_difference"], ci[0], ci[1],
                            c.get("p_permutation_task_level"), c.get("cohens_dz_task_level")])
        for contrast_id, p in summary["pairwise"].items():
            ci = p.get("ci95_win_rate") or [None, None]
            w.writerow([cfg.run_id, "pairwise_preference", "contrast", contrast_id,
                        p["decided"], p["treatment_win_rate_excluding_ties"], ci[0], ci[1],
                        p["p_binomial_excluding_ties"], ""])
