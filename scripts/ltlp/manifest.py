"""The run manifest: every sample and every pairwise comparison, fixed before generation.

Randomisation happens here and nowhere else, from one recorded master seed:

  * execution order is shuffled so that condition is not confounded with wall clock
    position, model drift, or load;
  * each sample gets a derived per-sample seed;
  * the A/B presentation order for every pairwise comparison is drawn now, at prepare
    time, rather than at judging time. That makes it a pre-registered randomisation which
    anyone can recompute from the seed.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List

from . import prompts


def sample_id(task_id: str, condition_id: str, rep: int) -> str:
    return "%s-%s-r%d" % (task_id, condition_id, rep)


def pair_id(task_id: str, contrast_id: str, rep: int) -> str:
    return "%s-%s-r%d" % (task_id, contrast_id, rep)


def derived_seed(master_seed: int, key: str) -> int:
    digest = hashlib.sha256(("%d:%s" % (master_seed, key)).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def build_samples(cfg) -> List[Dict[str, Any]]:
    samples = []
    for task in cfg.tasks:
        for cond in cfg.conditions:
            for rep in range(1, cfg.repetitions + 1):
                sid = sample_id(task["id"], cond["id"], rep)
                rendered = prompts.render_prompt(task["base_prompt"], cond["suffix"], cfg.join)
                samples.append({
                    "sample_id": sid,
                    "task_id": task["id"],
                    "family": task["family"],
                    "condition_id": cond["id"],
                    "condition_name": cond["name"],
                    "repetition": rep,
                    "sample_seed": derived_seed(cfg.seed, sid),
                    "prompt_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                    "prompt_chars": len(rendered),
                })
    rng = random.Random(derived_seed(cfg.seed, "execution-order"))
    order = list(range(len(samples)))
    rng.shuffle(order)
    for position, idx in enumerate(order):
        samples[idx]["execution_index"] = position
    samples.sort(key=lambda s: s["execution_index"])
    return samples


def build_pairs(cfg) -> List[Dict[str, Any]]:
    """One comparison per (task, repetition, contrast), with slots drawn from the seed."""
    pairs = []
    for contrast in cfg.primary_contrasts:
        for task in cfg.tasks:
            for rep in range(1, cfg.repetitions + 1):
                pid = pair_id(task["id"], contrast["id"], rep)
                rng = random.Random(derived_seed(cfg.seed, "pair:" + pid))
                treatment_first = rng.random() < 0.5
                ref_sid = sample_id(task["id"], contrast["reference"], rep)
                trt_sid = sample_id(task["id"], contrast["treatment"], rep)
                pairs.append({
                    "pair_id": pid,
                    "contrast_id": contrast["id"],
                    "task_id": task["id"],
                    "family": task["family"],
                    "repetition": rep,
                    "treatment_condition": contrast["treatment"],
                    "reference_condition": contrast["reference"],
                    # slot_a / slot_b are presentation positions shown to the judge.
                    "slot_a_sample_id": trt_sid if treatment_first else ref_sid,
                    "slot_b_sample_id": ref_sid if treatment_first else trt_sid,
                    "slot_a_condition": (contrast["treatment"] if treatment_first
                                         else contrast["reference"]),
                    "slot_b_condition": (contrast["reference"] if treatment_first
                                         else contrast["treatment"]),
                    "treatment_in_slot": "A" if treatment_first else "B",
                })
    rng = random.Random(derived_seed(cfg.seed, "pair-order"))
    order = list(range(len(pairs)))
    rng.shuffle(order)
    for position, idx in enumerate(order):
        pairs[idx]["execution_index"] = position
    pairs.sort(key=lambda p: p["execution_index"])
    return pairs


def blind_key(cfg) -> str:
    """Key for the judge-facing opaque item ids. Derived from the seed, so reproducible."""
    return hashlib.sha256(("blind:%d:%s" % (cfg.seed, cfg.run_id)).encode("utf-8")).hexdigest()


def build_blind_map(cfg, samples) -> Dict[str, str]:
    key = blind_key(cfg)
    return {s["sample_id"]: prompts.blind_item_id(key, s["sample_id"]) for s in samples}
