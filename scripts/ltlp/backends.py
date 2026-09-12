"""Model backends. One process or one request per generation, always a fresh context.

Three backends share one interface:

  claude_cli      the `claude` CLI in print mode. One OS process per sample, so each
                  generation genuinely starts from an empty conversation. No API key
                  needed. The CLI exposes no temperature or seed flag, so sampling
                  settings are recorded as "provider default, not exposed" rather than
                  claimed to be controlled.
  anthropic_api   direct Messages API call over urllib. Exact temperature control, needs
                  ANTHROPIC_API_KEY.
  mock            deterministic, seeded, offline. For testing the pipeline without
                  spending tokens. Every record it writes is tagged backend="mock" so a
                  mock run can never be mistaken for data.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class BackendError(RuntimeError):
    pass


class Backend:
    name = "base"

    def describe(self) -> Dict[str, Any]:
        raise NotImplementedError

    def complete(self, prompt: str, system: str, *, seed: Optional[int] = None) -> Dict[str, Any]:
        """Return {text, raw_meta, usage}. Must raise BackendError on failure."""
        raise NotImplementedError


class ClaudeCLIBackend(Backend):
    name = "claude_cli"

    def __init__(self, spec: Dict[str, Any]):
        self.model = spec["model"]
        self.binary = spec.get("binary", "claude")
        self.timeout = int(spec.get("timeout_seconds", 600))
        self.extra_args: List[str] = list(spec.get("extra_args", []))
        # Run from a neutral directory so the repository's own CLAUDE.md, skills and
        # plugins cannot leak into the generation context.
        self.cwd = spec.get("cwd") or os.path.expanduser("~")
        self.retries = int(spec.get("retries", 3))

    def argv(self, prompt: str, system: str) -> List[str]:
        return [self.binary, "-p", prompt,
                "--model", self.model,
                "--system-prompt", system,
                "--output-format", "json",
                "--no-session-persistence",
                "--strict-mcp-config",
                "--disable-slash-commands",
                "--restricted"] + self.extra_args

    def describe(self) -> Dict[str, Any]:
        return {
            "backend": self.name,
            "model": self.model,
            "argv_template": self.argv("<PROMPT>", "<SYSTEM>"),
            "cwd": self.cwd,
            "fresh_context": "one OS process per generation",
            "temperature": "provider default, not exposed by the CLI",
            "seed": "not exposed by the CLI",
        }

    def complete(self, prompt, system, *, seed=None):
        last = None
        for attempt in range(self.retries):
            if attempt:
                time.sleep(2 ** attempt)
            try:
                proc = subprocess.run(
                    self.argv(prompt, system), capture_output=True, text=True,
                    timeout=self.timeout, cwd=self.cwd)
            except subprocess.TimeoutExpired as exc:
                last = "timeout after %ss" % self.timeout
                continue
            if proc.returncode != 0:
                last = "exit %d: %s" % (proc.returncode, (proc.stderr or "")[-500:])
                continue
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError:
                last = "unparseable CLI output: %s" % proc.stdout[:300]
                continue
            if payload.get("is_error"):
                last = "CLI reported error: %s" % str(payload.get("result"))[:300]
                continue
            text = payload.get("result")
            if not isinstance(text, str) or not text.strip():
                last = "empty result from CLI"
                continue
            return {
                "text": text,
                "usage": payload.get("usage", {}),
                "raw_meta": {
                    "model": self.model,
                    "served_model": next(iter(payload.get("modelUsage", {})), None),
                    "cost_usd": payload.get("total_cost_usd"),
                    "duration_ms": payload.get("duration_ms"),
                    "num_turns": payload.get("num_turns"),
                    "stop_reason": payload.get("stop_reason"),
                    "attempt": attempt + 1,
                },
            }
        raise BackendError(last or "claude CLI failed")


class AnthropicAPIBackend(Backend):
    name = "anthropic_api"

    def __init__(self, spec: Dict[str, Any]):
        self.model = spec["model"]
        self.max_tokens = int(spec.get("max_tokens", 4096))
        self.temperature = spec.get("temperature", 1.0)
        self.base_url = (spec.get("base_url") or os.environ.get("ANTHROPIC_BASE_URL")
                         or "https://api.anthropic.com")
        self.api_key = os.environ.get(spec.get("api_key_env", "ANTHROPIC_API_KEY"), "")
        self.timeout = int(spec.get("timeout_seconds", 600))
        self.retries = int(spec.get("retries", 3))

    def describe(self):
        return {"backend": self.name, "model": self.model, "max_tokens": self.max_tokens,
                "temperature": self.temperature, "base_url": self.base_url,
                "fresh_context": "one request per generation, no conversation history"}

    def complete(self, prompt, system, *, seed=None):
        if not self.api_key:
            raise BackendError("ANTHROPIC_API_KEY is not set")
        body = json.dumps({
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/v1/messages", data=body, method="POST",
            headers={"content-type": "application/json",
                     "x-api-key": self.api_key,
                     "anthropic-version": "2023-06-01"})
        last = None
        for attempt in range(self.retries):
            if attempt:
                time.sleep(2 ** attempt)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last = "HTTP %s: %s" % (exc.code, exc.read()[:300])
                continue
            except Exception as exc:  # noqa: BLE001 - network failures are varied
                last = str(exc)
                continue
            text = "".join(b.get("text", "") for b in payload.get("content", [])
                           if b.get("type") == "text")
            if not text.strip():
                last = "empty response"
                continue
            return {"text": text, "usage": payload.get("usage", {}),
                    "raw_meta": {"model": payload.get("model"),
                                 "stop_reason": payload.get("stop_reason"),
                                 "attempt": attempt + 1}}
        raise BackendError(last or "anthropic API failed")


class MockBackend(Backend):
    """Deterministic offline stand-in. Produces plausible shapes, not real answers."""
    name = "mock"

    def __init__(self, spec: Dict[str, Any]):
        self.model = spec.get("model", "mock-model")

    def describe(self):
        return {"backend": self.name, "model": self.model,
                "warning": "synthetic output, never a scientific result"}

    def complete(self, prompt, system, *, seed=None):
        if seed is None:  # deterministic across processes, unlike hash()
            seed = int(hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:12], 16)
        rng = random.Random(seed)
        n = rng.randint(40, 160)
        words = ["analysis", "step", "check", "verify", "constraint", "however",
                 "alternative", "assumption", "risk", "therefore", "note", "caveat"]
        body = " ".join(rng.choice(words) for _ in range(n))
        text = ("Working through this task.\n\n" + body +
                "\n\nFINAL ANSWER: %d" % rng.randint(1, 999))
        if rng.random() < 0.5:
            text = '{"task_success": %d, "thoroughness": %d, "constraint_adherence": %d, ' \
                   '"error_checking": %d, "depth": %d, "usefulness": %d, ' \
                   '"reason": "mock", "preference": "%s"}' % (
                       rng.randint(1, 5), rng.randint(1, 5), rng.randint(1, 5),
                       rng.randint(1, 5), rng.randint(1, 5), rng.randint(1, 5),
                       rng.choice(["A", "B", "Tie"])) if "Return valid JSON" in prompt else text
        elif "Return valid JSON" in prompt:
            text = '{"task_success": 3, "thoroughness": 3, "constraint_adherence": 3, ' \
                   '"error_checking": 3, "depth": 3, "usefulness": 3, "reason": "mock", ' \
                   '"preference": "Tie"}'
        return {"text": text, "usage": {"output_tokens": n},
                "raw_meta": {"model": self.model, "mock": True}}


BACKENDS = {"claude_cli": ClaudeCLIBackend,
            "anthropic_api": AnthropicAPIBackend,
            "mock": MockBackend}


def build(spec: Dict[str, Any]) -> Backend:
    name = spec.get("backend")
    if name not in BACKENDS:
        raise BackendError("unknown backend %r (have: %s)" % (name, ", ".join(BACKENDS)))
    return BACKENDS[name](spec)
