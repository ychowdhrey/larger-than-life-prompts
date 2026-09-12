"""Shared resumable work loop.

Every stage is a list of units, each with a deterministic id and one output file. A unit
whose output already exists is skipped, so interrupting a stage and re-running it never
regenerates completed work and never rewrites a raw output.
"""
from __future__ import annotations

import datetime
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List

from . import util


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def run_units(units: List[Dict[str, Any]],
              output_path: Callable[[Dict[str, Any]], str],
              work: Callable[[Dict[str, Any]], Dict[str, Any]],
              *,
              stage: str,
              failures_dir: str,
              workers: int = 1,
              limit: int = None,
              progress: bool = True) -> Dict[str, Any]:
    pending = [u for u in units if not os.path.exists(output_path(u))]
    skipped = len(units) - len(pending)
    if limit is not None:
        pending = pending[:limit]

    lock = threading.Lock()
    counters = {"done": 0, "failed": 0}
    failures: List[Dict[str, Any]] = []
    total = len(pending)

    def _one(unit):
        uid = unit.get("unit_id") or unit.get("sample_id") or unit.get("pair_id")
        try:
            record = work(unit)
        except Exception as exc:  # noqa: BLE001 - a failed unit must not kill the stage
            with lock:
                counters["failed"] += 1
                failures.append({"unit_id": uid, "error": "%s: %s" % (type(exc).__name__, exc)})
            util.write_json(os.path.join(failures_dir, "%s.json" % uid),
                            {"unit_id": uid, "stage": stage, "at": now_iso(),
                             "error": "%s: %s" % (type(exc).__name__, exc)})
            if progress:
                with lock:
                    sys.stderr.write("  [%s] FAILED %s: %s\n" % (stage, uid, exc))
            return
        path = output_path(unit)
        try:
            util.write_json_once(path, record)
        except util.ImmutableWriteError:
            # Another worker or an earlier run produced it first. Keep theirs.
            pass
        with lock:
            counters["done"] += 1
            n = counters["done"]
        if progress:
            sys.stderr.write("  [%s] %d/%d %s\n" % (stage, n, total, uid))
            sys.stderr.flush()

    if pending:
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                list(pool.map(_one, pending))
        else:
            for unit in pending:
                _one(unit)

    return {"stage": stage, "total_units": len(units), "already_done": skipped,
            "attempted": total, "completed": counters["done"],
            "failed": counters["failed"], "failures": failures[:20],
            "finished_at": now_iso()}


def record_stage(cfg, stage: str, summary: Dict[str, Any]) -> None:
    path = cfg.p("state", "stages.json")
    ledger = util.read_json(path) if os.path.exists(path) else {}
    ledger[stage] = summary
    util.write_json(path, ledger)
