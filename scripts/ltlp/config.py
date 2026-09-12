"""Configuration loading and the spec lock.

The spec lock is how the repository's rule "do not change hypotheses, tasks, scoring rules
or experimental conditions after results have been generated" is enforced rather than
merely promised. `prepare` hashes every spec file into the run directory. Every later stage
re-checks those hashes and refuses to run if one moved.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from . import util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Files whose content defines the experiment. Changing any of them invalidates a run.
SPEC_FILES = [
    "tasks",
    "conditions",
    "rubric",
    "judge_prompt_blind",
    "judge_prompt_pairwise",
    "preregistration",
]


class SpecLockError(RuntimeError):
    """Raised when a spec file changed after raw outputs were produced."""


def _abs(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


class Config:
    def __init__(self, raw: Dict[str, Any], path: str):
        self.raw = raw
        self.path = path
        self.experiment_dir = _abs(raw["experiment_dir"])
        self.run_id = raw["run_id"]
        self.mode = raw.get("mode", "full")
        self.seed = int(raw["seed"])
        self.repetitions = int(raw["repetitions"])
        self.task_filter = raw.get("tasks")  # None means every task
        self.generation = raw["generation"]
        self.judging = raw["judging"]
        self.versions = raw.get("versions", {})

        self.spec_paths = {k: _abs(v) for k, v in raw["spec"].items()}
        missing = [k for k in SPEC_FILES if k not in self.spec_paths]
        if missing:
            raise ValueError("config is missing spec entries: %s" % ", ".join(missing))

        self.tasks_doc = util.read_json(self.spec_paths["tasks"])
        self.conditions_doc = util.read_json(self.spec_paths["conditions"])
        self.rubric = util.read_json(self.spec_paths["rubric"])
        self.judge_prompt_blind = util.read_text(self.spec_paths["judge_prompt_blind"])
        self.judge_prompt_pairwise = util.read_text(self.spec_paths["judge_prompt_pairwise"])

        all_tasks = {t["id"]: t for t in self.tasks_doc["tasks"]}
        if self.task_filter:
            unknown = [t for t in self.task_filter if t not in all_tasks]
            if unknown:
                raise ValueError("config names unknown tasks: %s" % ", ".join(unknown))
            self.tasks = [all_tasks[t] for t in self.task_filter]
        else:
            self.tasks = list(self.tasks_doc["tasks"])

        self.conditions = list(self.conditions_doc["conditions"])
        self.join = self.conditions_doc.get("join", "\n\n")
        self.primary_contrasts = self.conditions_doc["primary_contrasts"]
        self.secondary_contrasts = self.conditions_doc.get("secondary_contrasts", [])

    # ---- derived paths -------------------------------------------------

    @property
    def run_dir(self) -> str:
        return os.path.join(self.experiment_dir, "runs", self.run_id)

    def p(self, *parts: str) -> str:
        return os.path.join(self.run_dir, *parts)

    @property
    def expected_generations(self) -> int:
        return len(self.tasks) * len(self.conditions) * self.repetitions

    def condition(self, cid: str) -> Dict[str, Any]:
        for c in self.conditions:
            if c["id"] == cid:
                return c
        raise KeyError(cid)

    def task(self, tid: str) -> Dict[str, Any]:
        for t in self.tasks:
            if t["id"] == tid:
                return t
        raise KeyError(tid)

    # ---- spec lock -----------------------------------------------------

    def spec_hashes(self) -> Dict[str, str]:
        return {name: util.sha256_file(self.spec_paths[name]) for name in SPEC_FILES}

    def spec_lock_document(self) -> Dict[str, Any]:
        return {
            "note": ("sha256 of every file that defines this experiment, recorded at prepare "
                     "time. Later stages refuse to run if any hash changed."),
            "files": {name: os.path.relpath(self.spec_paths[name], REPO_ROOT)
                      for name in SPEC_FILES},
            "hashes": self.spec_hashes(),
            "versions": {
                "tasks": self.tasks_doc.get("version"),
                "conditions": self.conditions_doc.get("version"),
                "rubric": self.rubric.get("version"),
                "prompt_version": self.versions.get("prompt_version"),
                "evaluation_version": self.versions.get("evaluation_version"),
                "workflow_version": self.versions.get("workflow_version"),
            },
        }

    def verify_spec_lock(self) -> None:
        lock_path = self.p("spec.lock.json")
        if not os.path.exists(lock_path):
            raise SpecLockError(
                "no spec.lock.json in %s - run the prepare stage first" % self.run_dir)
        locked = util.read_json(lock_path)["hashes"]
        current = self.spec_hashes()
        drifted = [n for n in SPEC_FILES if locked.get(n) != current.get(n)]
        if drifted:
            raise SpecLockError(
                "spec files changed after this run was prepared: %s\n"
                "The experiment's own rule is that tasks, conditions, scoring rules and "
                "hypotheses are fixed once results exist. Either restore the files, or "
                "start a new run_id with a new spec version."
                % ", ".join(sorted(drifted)))


def load(path: str) -> Config:
    path = _abs(path)
    return Config(util.read_json(path), path)
