#!/usr/bin/env python3
"""Experiment runner for larger-than-life-prompts.

Stages, in order:

  prepare          build the randomised manifest, pairs and spec lock (write once)
  generate         one fresh model context per sample
  score-objective  deterministic scoring and behavioural indicators
  judge-blind      per response, six dimensions, condition never shown
  judge-pairwise   head to head, A/B order fixed at prepare time
  analyze          join everything, compute contrasts and uncertainty
  report           render analysis.md

  status           what exists so far
  verify           re-hash raw outputs and re-check prompt equivalence
  all              run the seven stages in order

Every stage is resumable: work whose output file already exists is skipped, and raw
outputs are never overwritten.

Examples:
  python3 scripts/experiment.py prepare --config experiments/001-may-the-force-be-with-you/config/pilot.json
  python3 scripts/experiment.py generate --config .../pilot.json --workers 4
  python3 scripts/experiment.py all --config .../pilot.json --workers 4
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ltlp import (analyze, config, generate, judge, manifest, prompts,  # noqa: E402
                  report, runner, score_objective, util)


def cmd_prepare(cfg, args):
    if os.path.exists(cfg.p("manifest.json")) and not args.force:
        print("manifest already exists for run %s - nothing to do" % cfg.run_id)
        print("(a prepared run is immutable; use a new run_id to change the design)")
        return 0
    util.ensure_dir(cfg.run_dir)
    util.ensure_dir(cfg.p("raw"))
    util.ensure_dir(cfg.p("state"))

    samples = manifest.build_samples(cfg)
    pairs = manifest.build_pairs(cfg)
    blind_map = manifest.build_blind_map(cfg, samples)

    util.write_json(cfg.p("spec.lock.json"), cfg.spec_lock_document())
    util.write_json(cfg.p("manifest.json"), {
        "run_id": cfg.run_id,
        "mode": cfg.mode,
        "seed": cfg.seed,
        "prepared_at": runner.now_iso(),
        "randomisation": {
            "execution_order": "seeded shuffle, so condition is not confounded with time",
            "pair_slots": "A/B presentation order drawn at prepare time from the master seed",
            "derivation": "sha256(master_seed:key)",
        },
        "n_tasks": len(cfg.tasks),
        "n_conditions": len(cfg.conditions),
        "repetitions": cfg.repetitions,
        "expected_generations": cfg.expected_generations,
        "samples": samples,
    })
    util.write_json(cfg.p("pairs.json"), {
        "run_id": cfg.run_id,
        "seed": cfg.seed,
        "n_pairs": len(pairs),
        "note": ("Presentation slots were drawn before any response existed. The judge sees "
                 "slot A and slot B and is never told which condition sits in either."),
        "pairs": pairs,
    })
    util.write_json(cfg.p("state", "blind_map.json"), {
        "note": ("sample_id -> opaque judge-facing item id. This file is NEVER passed to a "
                 "judge; it exists only so analysis can rejoin judgments to conditions."),
        "map": blind_map,
    })

    gen_backend_desc = {}
    try:
        from ltlp import backends
        gen_backend_desc = backends.build(cfg.generation).describe()
    except Exception as exc:  # a missing API key must not block prepare
        gen_backend_desc = {"error": str(exc)}

    util.write_json(cfg.p("run_meta.json"), {
        "run_id": cfg.run_id,
        "mode": cfg.mode,
        "experiment_id": "001",
        "phrase": "May the Force be with you.",
        "prepared_at": runner.now_iso(),
        "seed": cfg.seed,
        "generation": dict(cfg.generation, **{"resolved": gen_backend_desc}),
        "judging": cfg.judging,
        "versions": cfg.versions,
        "system_prompt_generation": prompts.GENERATION_SYSTEM_PROMPT,
        "system_prompt_judging": prompts.JUDGE_SYSTEM_PROMPT,
        "tasks": [t["id"] for t in cfg.tasks],
        "conditions": [{"id": c["id"], "name": c["name"], "suffix": c["suffix"]}
                       for c in cfg.conditions],
        "python": sys.version.split()[0],
        "config_file": os.path.relpath(cfg.path, config.REPO_ROOT),
    })
    print("prepared run %s" % cfg.run_id)
    print("  %d tasks x %d conditions x %d repetitions = %d generations"
          % (len(cfg.tasks), len(cfg.conditions), cfg.repetitions, cfg.expected_generations))
    print("  %d pairwise comparisons" % len(pairs))
    print("  seed %s, spec locked at %s" % (cfg.seed, cfg.p("spec.lock.json")))
    return 0


def cmd_verify(cfg, args):
    problems = []

    # 1. the spec has not moved since prepare
    try:
        cfg.verify_spec_lock()
        print("spec lock: OK")
    except Exception as exc:
        problems.append(str(exc))
        print("spec lock: FAILED")

    # 2. prompts differ only by the condition suffix
    bad = []
    for task in cfg.tasks:
        for cond in cfg.conditions:
            rendered = prompts.render_prompt(task["base_prompt"], cond["suffix"], cfg.join)
            if prompts.strip_suffix(rendered, cond["suffix"], cfg.join) != task["base_prompt"]:
                bad.append("%s/%s" % (task["id"], cond["id"]))
    if bad:
        problems.append("prompt equivalence failed for: %s" % ", ".join(bad))
    print("prompt equivalence: %s (%d tasks x %d conditions)"
          % ("OK" if not bad else "FAILED", len(cfg.tasks), len(cfg.conditions)))

    # 3. raw outputs match their recorded hashes
    index = util.read_jsonl(cfg.p("raw", "INDEX.jsonl"))
    drift = []
    for entry in index:
        path = cfg.p("raw", entry["file"])
        if not os.path.exists(path):
            drift.append("%s missing" % entry["file"])
        elif util.sha256_file(path) != entry["file_sha256"]:
            drift.append("%s changed" % entry["file"])
    if drift:
        problems.append("raw output drift: %s" % "; ".join(drift[:10]))
    print("raw immutability: %s (%d files in ledger)"
          % ("OK" if not drift else "FAILED", len(index)))

    # 4. no judge payload contains condition text
    leaked = []
    suffixes = [c["suffix"] for c in cfg.conditions if c["suffix"]]
    for sub in ("blind", "pairwise"):
        d = cfg.p("judge", sub)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            rec = util.read_json(os.path.join(d, name))
            blob = json.dumps({k: v for k, v in rec.items()
                               if k in ("reason",)}).lower()
            for suf in suffixes:
                if suf.lower().rstrip(".") in blob:
                    leaked.append("%s/%s" % (sub, name))
    print("judge record cleanliness: %s" % ("OK" if not leaked else
                                            "WARNING - condition text in %d judge reasons"
                                            % len(leaked)))

    if problems:
        print("\nVERIFY FAILED")
        for p in problems:
            print("  - %s" % p)
        return 1
    print("\nVERIFY PASSED")
    return 0


def cmd_status(cfg, args):
    def count(path, suffix=".json"):
        if not os.path.isdir(path):
            return 0
        return sum(1 for n in os.listdir(path) if n.endswith(suffix) and n != "INDEX.jsonl")

    exp = cfg.expected_generations
    npairs = len(cfg.tasks) * cfg.repetitions * len(cfg.primary_contrasts)
    print("run %s (%s)" % (cfg.run_id, cfg.mode))
    print("  prepared        : %s" % ("yes" if os.path.exists(cfg.p("manifest.json")) else "NO"))
    print("  generations     : %d / %d" % (count(cfg.p("raw")), exp))
    print("  objective scored: %d / %d" % (count(cfg.p("objective")), exp))
    print("  blind judged    : %d / %d" % (count(cfg.p("judge", "blind")), exp))
    print("  pairwise judged : %d / %d" % (count(cfg.p("judge", "pairwise")), npairs))
    print("  analysis        : %s" % ("yes" if os.path.exists(cfg.p("analysis", "summary.json")) else "no"))
    print("  report          : %s" % ("yes" if os.path.exists(cfg.p("analysis", "analysis.md")) else "no"))
    for stage in ("generate", "judge-blind", "judge-pairwise"):
        fdir = cfg.p("state", "failures", stage if stage != "generate" else "generate")
        n = count(fdir)
        if n:
            print("  ! %d recorded failures in %s (re-run the stage to retry)" % (n, stage))
    return 0


def cmd_generate(cfg, args):
    s = generate.run(cfg, workers=args.workers, limit=args.limit)
    print("generate: %d already done, %d attempted, %d completed, %d failed"
          % (s["already_done"], s["attempted"], s["completed"], s["failed"]))
    return 1 if s["failed"] and not args.keep_going else 0


def cmd_score_objective(cfg, args):
    s = score_objective.run(cfg, workers=args.workers, limit=args.limit)
    print("score-objective: %d already done, %d completed, %d failed"
          % (s["already_done"], s["completed"], s["failed"]))
    return 0


def cmd_judge_blind(cfg, args):
    s = judge.run_blind(cfg, workers=args.workers, limit=args.limit)
    print("judge-blind: %d already done, %d attempted, %d completed, %d failed"
          % (s["already_done"], s["attempted"], s["completed"], s["failed"]))
    return 1 if s["failed"] and not args.keep_going else 0


def cmd_judge_pairwise(cfg, args):
    s = judge.run_pairwise(cfg, workers=args.workers, limit=args.limit)
    print("judge-pairwise: %d already done, %d attempted, %d completed, %d failed"
          % (s["already_done"], s["attempted"], s["completed"], s["failed"]))
    return 1 if s["failed"] and not args.keep_going else 0


def cmd_analyze(cfg, args):
    s = analyze.run(cfg)
    print("analyze: %d generations, %d blind judged, %d pairwise"
          % (s["counts"]["generations_present"], s["counts"]["blind_judged"],
             s["counts"]["pairwise_judged"]))
    print("  -> %s" % cfg.p("analysis", "summary.json"))
    return 0


def cmd_report(cfg, args):
    report.run(cfg)
    print("report -> %s" % cfg.p("analysis", "analysis.md"))
    return 0


def cmd_all(cfg, args):
    for fn in (cmd_prepare, cmd_generate, cmd_score_objective, cmd_judge_blind,
               cmd_judge_pairwise, cmd_analyze, cmd_report):
        rc = fn(cfg, args)
        if rc and not args.keep_going:
            print("stopping: %s returned %d" % (fn.__name__, rc))
            return rc
    return 0


COMMANDS = {
    "prepare": cmd_prepare,
    "generate": cmd_generate,
    "score-objective": cmd_score_objective,
    "judge-blind": cmd_judge_blind,
    "judge-pairwise": cmd_judge_pairwise,
    "analyze": cmd_analyze,
    "report": cmd_report,
    "status": cmd_status,
    "verify": cmd_verify,
    "all": cmd_all,
}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=sorted(COMMANDS))
    ap.add_argument("--config", required=True, help="path to a run config JSON file")
    ap.add_argument("--workers", type=int, default=1,
                    help="parallel model calls (generation and judging only)")
    ap.add_argument("--limit", type=int, default=None,
                    help="stop after this many new units, for a cautious first pass")
    ap.add_argument("--force", action="store_true",
                    help="prepare only: rebuild a manifest that already exists")
    ap.add_argument("--keep-going", action="store_true",
                    help="continue to the next stage even if units failed")
    args = ap.parse_args(argv)
    cfg = config.load(args.config)
    return COMMANDS[args.stage](cfg, args)


if __name__ == "__main__":
    raise SystemExit(main())
