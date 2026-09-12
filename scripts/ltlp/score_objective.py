"""Stage: objective scoring. Deterministic, no model calls, no condition visible."""
from __future__ import annotations

from typing import Any, Dict

from . import generate, indicators, objective, runner, util


def out_path(cfg, sample_id: str) -> str:
    return cfg.p("objective", "%s.json" % sample_id)


def run(cfg, *, workers: int = 1, limit: int = None) -> Dict[str, Any]:
    cfg.verify_spec_lock()
    responses = generate.load_responses(cfg)
    units = [{"unit_id": sid, "sample_id": sid} for sid in sorted(responses)]

    def work(unit: Dict[str, Any]) -> Dict[str, Any]:
        rec = responses[unit["sample_id"]]
        task = cfg.task(rec["task_id"])
        scored = objective.score(task, rec["response"])
        ind = indicators.compute(task, rec["response"], scored)
        return {
            "sample_id": rec["sample_id"],
            "task_id": rec["task_id"],
            "family": rec["family"],
            "condition_id": rec["condition_id"],
            "repetition": rec["repetition"],
            "response_sha256": rec["response_sha256"],
            "objective": scored,
            "indicators": ind,
            "scored_at": runner.now_iso(),
            "evaluation_version": cfg.versions.get("evaluation_version"),
        }

    summary = runner.run_units(
        units, lambda u: out_path(cfg, u["sample_id"]), work,
        stage="score-objective", failures_dir=cfg.p("state", "failures", "objective"),
        workers=workers, limit=limit, progress=False)
    runner.record_stage(cfg, "score-objective", summary)
    return summary
