"""Stage: generate. One fresh model context per sample."""
from __future__ import annotations

import os
from typing import Any, Dict

from . import backends, manifest, prompts, runner, util


def raw_path(cfg, sample_id: str) -> str:
    return cfg.p("raw", "%s.json" % sample_id)


def run(cfg, *, workers: int = 1, limit: int = None) -> Dict[str, Any]:
    cfg.verify_spec_lock()
    samples = util.read_json(cfg.p("manifest.json"))["samples"]
    backend = backends.build(cfg.generation)
    suffixes = [c["suffix"] for c in cfg.conditions if c["suffix"]]
    index_path = cfg.p("raw", "INDEX.jsonl")

    def work(sample: Dict[str, Any]) -> Dict[str, Any]:
        task = cfg.task(sample["task_id"])
        cond = cfg.condition(sample["condition_id"])
        rendered = prompts.render_prompt(task["base_prompt"], cond["suffix"], cfg.join)
        if util.sha256_text(rendered) != sample["prompt_sha256"]:
            raise RuntimeError("rendered prompt does not match the manifest hash - the "
                               "task set or conditions changed after prepare")
        started = runner.now_iso()
        result = backend.complete(rendered, prompts.GENERATION_SYSTEM_PROMPT,
                                  seed=sample["sample_seed"])
        echo = prompts.condition_echo(result["text"], suffixes)
        record = {
            "sample_id": sample["sample_id"],
            "run_id": cfg.run_id,
            "task_id": sample["task_id"],
            "family": sample["family"],
            "condition_id": sample["condition_id"],
            "condition_name": sample["condition_name"],
            "repetition": sample["repetition"],
            "execution_index": sample["execution_index"],
            "sample_seed": sample["sample_seed"],
            "prompt_sha256": sample["prompt_sha256"],
            "prompt_chars": len(rendered),
            "response": result["text"],
            "response_sha256": util.sha256_text(result["text"]),
            "backend": backend.name,
            "model": cfg.generation.get("model"),
            "usage": result.get("usage", {}),
            "meta": result.get("raw_meta", {}),
            "condition_echo": echo,
            "started_at": started,
            "finished_at": runner.now_iso(),
            "versions": cfg.versions,
        }
        return record

    def after(sample, record):
        pass

    summary = runner.run_units(
        samples, lambda s: raw_path(cfg, s["sample_id"]), work,
        stage="generate", failures_dir=cfg.p("state", "failures", "generate"),
        workers=workers, limit=limit)

    # Rebuild the tamper-evident ledger from whatever now exists on disk.
    rebuild_index(cfg)
    summary["index"] = os.path.relpath(index_path, cfg.run_dir)
    runner.record_stage(cfg, "generate", summary)
    return summary


def rebuild_index(cfg) -> int:
    raw_dir = cfg.p("raw")
    index_path = cfg.p("raw", "INDEX.jsonl")
    if os.path.exists(index_path):
        os.unlink(index_path)
    n = 0
    for name in sorted(os.listdir(raw_dir)) if os.path.isdir(raw_dir) else []:
        if not name.endswith(".json"):
            continue
        path = os.path.join(raw_dir, name)
        rec = util.read_json(path)
        util.append_jsonl(index_path, {
            "sample_id": rec["sample_id"],
            "file": name,
            "file_sha256": util.sha256_file(path),
            "response_sha256": rec.get("response_sha256"),
            "bytes": os.path.getsize(path),
        })
        n += 1
    return n


def load_responses(cfg) -> Dict[str, Dict[str, Any]]:
    raw_dir = cfg.p("raw")
    out = {}
    if not os.path.isdir(raw_dir):
        return out
    for name in sorted(os.listdir(raw_dir)):
        if name.endswith(".json"):
            rec = util.read_json(os.path.join(raw_dir, name))
            out[rec["sample_id"]] = rec
    return out
