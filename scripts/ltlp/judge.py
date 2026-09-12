"""Stages: blind judging and pairwise judging.

The judge never receives a condition, a sample id, or the condition-augmented prompt. It
sees the BASE task and the response text, under an opaque item id. Handing it the rendered
prompt would print the treatment phrase directly into the judge's context and destroy the
blind, so `build_blind_judge_prompt` takes the base prompt and there is no code path that
passes anything else.
"""
from __future__ import annotations

from typing import Any, Dict, List

from . import backends, generate, manifest, prompts, runner, util

DIMENSIONS = ["task_success", "thoroughness", "constraint_adherence",
              "error_checking", "depth", "usefulness"]


def blind_path(cfg, item_id: str) -> str:
    return cfg.p("judge", "blind", "%s.json" % item_id)


def pairwise_path(cfg, pair_id: str) -> str:
    return cfg.p("judge", "pairwise", "%s.json" % pair_id)


def _coerce_score(value) -> int:
    n = int(round(float(value)))
    if n < 1 or n > 5:
        raise ValueError("score %r outside 1..5" % value)
    return n


def run_blind(cfg, *, workers: int = 1, limit: int = None) -> Dict[str, Any]:
    cfg.verify_spec_lock()
    responses = generate.load_responses(cfg)
    blind_map = util.read_json(cfg.p("state", "blind_map.json"))["map"]
    backend = backends.build(cfg.judging)
    template = cfg.judge_prompt_blind

    units = []
    for sid in sorted(responses):
        units.append({"unit_id": blind_map[sid], "sample_id": sid, "item_id": blind_map[sid]})

    def work(unit: Dict[str, Any]) -> Dict[str, Any]:
        rec = responses[unit["sample_id"]]
        task = cfg.task(rec["task_id"])
        # Base prompt only. Never rec's rendered prompt.
        payload = prompts.build_blind_judge_prompt(template, task["base_prompt"], rec["response"])
        result = backend.complete(payload, prompts.JUDGE_SYSTEM_PROMPT)
        parsed = util.extract_json_object(result["text"])
        scores = {d: _coerce_score(parsed[d]) for d in DIMENSIONS}
        return {
            "item_id": unit["item_id"],
            # Recorded for analysis only; it was never in the judge's context.
            "sample_id": rec["sample_id"],
            "task_id": rec["task_id"],
            "family": rec["family"],
            "condition_id": rec["condition_id"],
            "repetition": rec["repetition"],
            "scores": scores,
            "reason": str(parsed.get("reason", ""))[:1000],
            "judge_model": cfg.judging.get("model"),
            "judge_backend": backend.name,
            "judge_prompt_version": cfg.versions.get("judge_prompt_version"),
            "rubric_version": cfg.rubric.get("version"),
            "judged_at": runner.now_iso(),
        }

    summary = runner.run_units(
        units, lambda u: blind_path(cfg, u["item_id"]), work,
        stage="judge-blind", failures_dir=cfg.p("state", "failures", "judge-blind"),
        workers=workers, limit=limit)
    runner.record_stage(cfg, "judge-blind", summary)
    return summary


def run_pairwise(cfg, *, workers: int = 1, limit: int = None) -> Dict[str, Any]:
    cfg.verify_spec_lock()
    responses = generate.load_responses(cfg)
    pairs = util.read_json(cfg.p("pairs.json"))["pairs"]
    backend = backends.build(cfg.judging)
    template = cfg.judge_prompt_pairwise

    ready = [p for p in pairs
             if p["slot_a_sample_id"] in responses and p["slot_b_sample_id"] in responses]

    def work(pair: Dict[str, Any]) -> Dict[str, Any]:
        task = cfg.task(pair["task_id"])
        a = responses[pair["slot_a_sample_id"]]["response"]
        b = responses[pair["slot_b_sample_id"]]["response"]
        payload = prompts.build_pairwise_judge_prompt(template, task["base_prompt"], a, b)
        result = backend.complete(payload, prompts.JUDGE_SYSTEM_PROMPT)
        parsed = util.extract_json_object(result["text"])
        pref = str(parsed.get("preference", "")).strip().title()
        if pref not in ("A", "B", "Tie"):
            raise ValueError("judge returned preference %r" % parsed.get("preference"))
        # Map the presentation slot back to a condition. The judge chose a slot; only we
        # know which condition sat in it.
        if pref == "Tie":
            winner_condition = None
            treatment_won = None
        else:
            winner_condition = pair["slot_a_condition"] if pref == "A" else pair["slot_b_condition"]
            treatment_won = winner_condition == pair["treatment_condition"]
        return {
            "pair_id": pair["pair_id"],
            "contrast_id": pair["contrast_id"],
            "task_id": pair["task_id"],
            "family": pair["family"],
            "repetition": pair["repetition"],
            "treatment_condition": pair["treatment_condition"],
            "reference_condition": pair["reference_condition"],
            "treatment_in_slot": pair["treatment_in_slot"],
            "preference_slot": pref,
            "winner_condition": winner_condition,
            "treatment_won": treatment_won,
            "tie": pref == "Tie",
            "reason": str(parsed.get("reason", ""))[:1000],
            "judge_model": cfg.judging.get("model"),
            "judge_backend": backend.name,
            "judge_prompt_version": cfg.versions.get("judge_prompt_version"),
            "judged_at": runner.now_iso(),
        }

    for p in ready:
        p["unit_id"] = p["pair_id"]

    summary = runner.run_units(
        ready, lambda p: pairwise_path(cfg, p["pair_id"]), work,
        stage="judge-pairwise", failures_dir=cfg.p("state", "failures", "judge-pairwise"),
        workers=workers, limit=limit)
    summary["pairs_without_both_responses"] = len(pairs) - len(ready)
    runner.record_stage(cfg, "judge-pairwise", summary)
    return summary
