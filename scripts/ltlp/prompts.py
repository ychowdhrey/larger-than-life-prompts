"""Prompt assembly and judge payload construction.

This module carries the experiment's central validity claim: across conditions the prompt
differs ONLY by the appended suffix. Everything here is deliberately small enough to read
in one sitting, and is covered by scripts/tests/test_prompts.py.
"""
from __future__ import annotations

import hashlib
import hmac
import re
from typing import Optional

# The system prompt is held constant across every condition and every sample. It is
# deliberately bland: it must not hint at effort, care, or thoroughness, because those are
# exactly the behaviours under test.
GENERATION_SYSTEM_PROMPT = (
    "You are completing a written task. Respond to the task directly. "
    "Do not ask clarifying questions and do not describe what you are about to do."
)

JUDGE_SYSTEM_PROMPT = (
    "You are an impartial evaluator. Follow the instructions exactly and return only the "
    "JSON object requested."
)


def render_prompt(base_prompt: str, suffix: str, join: str = "\n\n") -> str:
    """Build the full prompt for one condition.

    An empty suffix returns the base prompt byte-for-byte, with no join and no trailing
    whitespace, so the control condition is genuinely the untouched task.
    """
    if suffix is None or suffix == "":
        return base_prompt
    return base_prompt + join + suffix


def strip_suffix(rendered: str, suffix: str, join: str = "\n\n") -> str:
    """Inverse of render_prompt, used by the verify stage."""
    if suffix is None or suffix == "":
        return rendered
    tail = join + suffix
    if not rendered.endswith(tail):
        raise ValueError("rendered prompt does not end with its condition suffix")
    return rendered[: -len(tail)]


def blind_item_id(blind_key: str, sample_id: str) -> str:
    """Opaque, stable, unguessable-from-content identifier shown to judges."""
    return hmac.new(blind_key.encode("utf-8"), sample_id.encode("utf-8"),
                    hashlib.sha256).hexdigest()[:16]


def build_blind_judge_prompt(template: str, base_prompt: str, response: str) -> str:
    """Render the single-response judge prompt.

    The judge is given the BASE prompt, never the condition-augmented one. Passing the
    rendered prompt here would hand the judge the treatment text verbatim and destroy the
    blind. There is no parameter for a condition, by construction.
    """
    return (template
            .replace("{{TASK}}", base_prompt)
            .replace("{{RESPONSE}}", response))


def build_pairwise_judge_prompt(template: str, base_prompt: str,
                                response_a: str, response_b: str) -> str:
    """Render the pairwise judge prompt. A and B are presentation slots, not conditions."""
    return (template
            .replace("{{TASK}}", base_prompt)
            .replace("{{RESPONSE_A}}", response_a)
            .replace("{{RESPONSE_B}}", response_b))


def condition_echo(response: str, suffixes) -> Optional[str]:
    """Detect a response echoing condition text back (a real blinding leak).

    We never edit the output. We flag it, count it, and report it as a confound.
    """
    if not response:
        return None
    low = response.lower()
    for suffix in suffixes:
        if not suffix:
            continue
        core = re.sub(r"[^\w\s]", "", suffix.lower()).strip()
        if core and core in re.sub(r"[^\w\s]", "", low):
            return suffix
    return None
