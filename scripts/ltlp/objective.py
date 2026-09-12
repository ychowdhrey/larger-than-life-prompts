"""Deterministic, condition-blind scoring of a response against a task's checks.

Nothing in this module can see which condition produced a response, so the objective score
is blind by construction rather than by procedure. Every check type is documented in
tasks.json under `check_types`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

FLAGS = re.IGNORECASE | re.DOTALL
TABLE_LINE = re.compile(r"^\s*\|.*\|\s*$")


# ---------------------------------------------------------------- helpers

def _strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", " ", text, flags=re.DOTALL)


def _strip_tables(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not TABLE_LINE.match(l))


def _words(text: str) -> List[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _sentences(text: str) -> List[str]:
    flat = _strip_tables(_strip_code_fences(text))
    flat = re.sub(r"\s+", " ", flat).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", flat)
    return [p.strip() for p in parts if p.strip()]


def _final_sentence(text: str) -> str:
    sents = _sentences(text)
    return sents[-1] if sents else ""


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`#]", "", text or "")).strip()


# ------------------------------------------------------- check evaluators

def _c_regex_any(check, text) -> Tuple[bool, str]:
    for p in check["patterns"]:
        if re.search(p, text, FLAGS):
            return True, "matched %s" % p
    return False, "no pattern matched"


def _c_regex_all(check, text) -> Tuple[bool, str]:
    missing = [p for p in check["patterns"] if not re.search(p, text, FLAGS)]
    return (not missing), ("all matched" if not missing else "missing: %s" % "; ".join(missing))


def _c_forbidden(check, text) -> Tuple[bool, str]:
    hits = [p for p in check["patterns"] if re.search(p, text, FLAGS)]
    return (not hits), ("clean" if not hits else "triggered: %s" % "; ".join(hits))


def _c_count_matches(check, text) -> Tuple[bool, str]:
    n = len(re.findall(check["pattern"], text, FLAGS if "(?m)" not in check["pattern"] else re.IGNORECASE))
    lo, hi = check.get("min"), check.get("max")
    ok = (lo is None or n >= lo) and (hi is None or n <= hi)
    return ok, "found %d (allowed %s..%s)" % (n, lo, hi)


def _c_word_count(check, text) -> Tuple[bool, str]:
    body = text
    if check.get("exclude_tables"):
        body = _strip_tables(body)
    n = len(_words(_strip_code_fences(body)))
    lo, hi = check.get("min"), check.get("max")
    ok = (lo is None or n >= lo) and (hi is None or n <= hi)
    return ok, "%d words (allowed %s..%s)" % (n, lo, hi)


def _c_max_sentence_words(check, text) -> Tuple[bool, str]:
    worst, worst_n = "", 0
    for s in _sentences(text):
        n = len(_words(s))
        if n > worst_n:
            worst, worst_n = s, n
    ok = worst_n <= check["max"]
    return ok, "longest sentence %d words (max %d)" % (worst_n, check["max"])


def _c_ordering(check, text) -> Tuple[bool, str]:
    m1 = re.search(check["first"], text, FLAGS)
    m2 = re.search(check["second"], text, FLAGS)
    if m2 is None:
        if check.get("allow_missing_second"):
            return (m1 is not None), "second element absent, first %spresent" % ("" if m1 else "also ab")
        return False, "second element absent"
    if m1 is None:
        return False, "first element absent"
    return m1.start() < m2.start(), "first at %d, second at %d" % (m1.start(), m2.start())


def _c_ends_with(check, text) -> Tuple[bool, str]:
    want = _normalise(check["text"]).rstrip(".").lower()
    got = _normalise(_final_sentence(text)).rstrip(".").lower()
    return got == want, "final sentence was %r" % got[:120]


def _c_subject_line(check, text) -> Tuple[bool, str]:
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return False, "empty response"
    first = _normalise(lines[0])
    if not first.lower().startswith("subject:"):
        return False, "first line is not a Subject line: %r" % first[:80]
    ok = len(first) <= check["max_chars"]
    return ok, "subject line is %d characters (max %d)" % (len(first), check["max_chars"])


def _c_paragraph_count(check, text) -> Tuple[bool, str]:
    body = text.strip()
    if check.get("skip_first_line"):
        lines = body.splitlines()
        body = "\n".join(lines[1:]).strip() if lines else ""
    paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    n = len(paras)
    ok = n == check["count"]
    return ok, "%d paragraphs (need %d)" % (n, check["count"])


def _c_markdown_table(check, text) -> Tuple[bool, str]:
    rows = [l.strip() for l in text.splitlines() if TABLE_LINE.match(l)]
    if len(rows) < 3:
        return False, "no markdown table found"
    cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
    header = [h.lower().strip(" *_") for h in cells(rows[0])]
    want = [h.lower() for h in check["headers"]]
    if header != want:
        return False, "headers were %s, need %s" % (header, want)
    data = [r for r in rows[1:] if not re.match(r"^\s*\|[\s:|-]+\|\s*$", r)]
    n = len(data)
    ok = n == check["rows"]
    return ok, "%d data rows (need %d)" % (n, check["rows"])


# ------------------------------------------- P03: schedule feasibility

SCHEDULE_LINE = re.compile(r"(?mi)^\s*DAY\s*(\d+)\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*$")

P03_SPEC = {
    "durations": {"T1": 2, "T2": 2, "T3": 2, "T4": 3, "T5": 2, "T6": 3},
    "deps": {"T1": [], "T2": ["T1"], "T3": ["T1"], "T4": ["T2"], "T5": ["T3"],
             "T6": ["T4", "T5"]},
    "engineers": 2,
    "last_day": 10,
}


def _c_schedule_valid(check, text) -> Tuple[bool, str]:
    spec = P03_SPEC
    entries = []
    for m in SCHEDULE_LINE.finditer(text):
        day = int(m.group(1))
        eng = m.group(2).strip().upper().replace(" ", "")
        task = m.group(3).strip().upper().replace(" ", "")
        entries.append((day, eng, task))
    if not entries:
        return False, "no schedule lines in the required format"

    problems = []
    by_task: Dict[str, List[int]] = {}
    by_eng_day: Dict[Tuple[str, int], List[str]] = {}
    task_engineer: Dict[str, set] = {}
    for day, eng, task in entries:
        if day < 1 or day > spec["last_day"]:
            problems.append("day %d is outside Day 1..%d" % (day, spec["last_day"]))
        by_task.setdefault(task, []).append(day)
        by_eng_day.setdefault((eng, day), []).append(task)
        task_engineer.setdefault(task, set()).add(eng)

    unknown = sorted(set(by_task) - set(spec["durations"]))
    if unknown:
        problems.append("unknown tasks: %s" % ", ".join(unknown))
    missing = sorted(set(spec["durations"]) - set(by_task))
    if missing:
        problems.append("tasks never scheduled: %s" % ", ".join(missing))

    if len({e for _, e, _ in entries}) > spec["engineers"]:
        problems.append("more than %d engineers used" % spec["engineers"])
    for (eng, day), tasks in sorted(by_eng_day.items()):
        if len(set(tasks)) > 1:
            problems.append("%s works on %s on day %d" % (eng, "+".join(sorted(set(tasks))), day))

    finish: Dict[str, int] = {}
    start: Dict[str, int] = {}
    for task, days in by_task.items():
        if task not in spec["durations"]:
            continue
        days = sorted(set(days))
        if len(task_engineer[task]) > 1:
            problems.append("%s is split across engineers %s"
                            % (task, ", ".join(sorted(task_engineer[task]))))
        if len(days) != spec["durations"][task]:
            problems.append("%s scheduled for %d days, needs %d"
                            % (task, len(days), spec["durations"][task]))
        if days and days[-1] - days[0] + 1 != len(days):
            problems.append("%s is not on consecutive days (%s)"
                            % (task, ", ".join(map(str, days))))
        if days:
            start[task], finish[task] = days[0], days[-1]

    for task, deps in spec["deps"].items():
        for dep in deps:
            if task in start and dep in finish and start[task] <= finish[dep]:
                problems.append("%s starts on day %d but %s only finishes on day %d"
                                % (task, start[task], dep, finish[dep]))

    if problems:
        return False, "; ".join(problems[:6])
    return True, "feasible schedule, last day %d" % max(finish.values())


# ----------------------------------------- P04: budget self-consistency

ITEM_LINE = re.compile(r"(?mi)^\s*ITEM\s*:\s*([^|\n]+?)\s*\|\s*([\d,]+(?:\.\d+)?)\s*$")
TOTAL_LINE = re.compile(r"(?mi)^\s*TOTAL\s*:\s*([\d,]+(?:\.\d+)?)\s*$")


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _c_sum_consistency(check, text) -> Tuple[bool, str]:
    items = [(m.group(1).strip(), _num(m.group(2))) for m in ITEM_LINE.finditer(text)]
    totals = TOTAL_LINE.findall(text)
    if not items:
        return False, "no ITEM lines in the required format"
    if not totals:
        return False, "no TOTAL line"
    stated = _num(totals[-1])
    summed = round(sum(a for _, a in items), 2)
    problems = []
    if abs(summed - stated) > 0.01:
        problems.append("line items sum to %.2f but TOTAL says %.2f" % (summed, stated))
    cap = check.get("cap")
    if cap is not None and stated > cap + 0.01:
        problems.append("TOTAL %.2f exceeds the cap of %.2f" % (stated, cap))
    cpat = check.get("contingency_pattern")
    if cpat:
        cont = sum(a for name, a in items if re.search(cpat, name, re.IGNORECASE))
        need = check.get("contingency_min_frac", 0.0) * stated
        if cont <= 0:
            problems.append("no contingency line item")
        elif cont < need - 0.01:
            problems.append("contingency %.2f is below %.0f%% of the total (%.2f)"
                            % (cont, check["contingency_min_frac"] * 100, need))
    if problems:
        return False, "; ".join(problems)
    return True, "%d items summing to %.2f, consistent and within budget" % (len(items), summed)


EVALUATORS = {
    "regex_any": _c_regex_any,
    "regex_all": _c_regex_all,
    "forbidden": _c_forbidden,
    "count_matches": _c_count_matches,
    "word_count": _c_word_count,
    "max_sentence_words": _c_max_sentence_words,
    "ordering": _c_ordering,
    "ends_with": _c_ends_with,
    "subject_line": _c_subject_line,
    "paragraph_count": _c_paragraph_count,
    "markdown_table": _c_markdown_table,
    "schedule_valid": _c_schedule_valid,
    "sum_consistency": _c_sum_consistency,
}


def score(task: Dict[str, Any], response: str) -> Dict[str, Any]:
    """Score one response against one task. Deterministic and condition-blind."""
    results = []
    earned = 0.0
    for check in task["checks"]:
        evaluator = EVALUATORS.get(check["type"])
        if evaluator is None:
            raise ValueError("unknown check type %r in task %s" % (check["type"], task["id"]))
        try:
            passed, detail = evaluator(check, response or "")
        except Exception as exc:  # a malformed response must not crash the stage
            passed, detail = False, "check raised %s: %s" % (type(exc).__name__, exc)
        if passed:
            earned += check["points"]
        results.append({"check_id": check["id"], "label": check["label"],
                        "type": check["type"], "points": check["points"],
                        "passed": bool(passed), "detail": detail,
                        "constraint": check.get("constraint", False),
                        "planted": check.get("planted", False),
                        "distractor": check.get("distractor", False)})

    def _frac(pred):
        sel = [r for r in results if pred(r)]
        if not sel:
            return None
        got = sum(r["points"] for r in sel if r["passed"])
        tot = sum(r["points"] for r in sel)
        return round(got / tot, 6) if tot else None

    return {
        "max_points": task["max_points"],
        "earned_points": round(earned, 4),
        "objective_score": round(earned / task["max_points"], 6) if task["max_points"] else None,
        "constraint_completion": _frac(lambda r: r["constraint"]),
        "planted_issue_recall": _frac(lambda r: r["planted"]),
        "distractor_avoidance": _frac(lambda r: r["distractor"]),
        "checks": results,
    }
