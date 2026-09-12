# Preregistration: Experiment 001

**Locked: 2026-09-12, before any generation existed.**

This file is hashed into `runs/<run_id>/spec.lock.json` at the prepare stage. Every later
stage re-checks that hash and refuses to run if this file changed. That is the mechanism by
which the repository's rule — do not change hypotheses, tasks, scoring rules or conditions
after results have been generated — is enforced rather than merely promised.

If something here turns out to be wrong, the correct response is a **new run with a new
spec version**, leaving this one and its results in place. See `METHODOLOGY.md`, "Negative
results".

## Phrase under test

> May the Force be with you.

Appended at the end of the prompt.

## Hypotheses

**H1.** Appending the phrase changes observable output behaviour relative to appending
nothing.

**H2.** Appending the phrase improves measured task performance relative to appending
nothing.

**H3 (the question that matters).** Any improvement under H2 is specific to this phrase,
rather than a response to *any* appended text. This is tested against two active controls:
generic encouragement, and an explicit instruction to be thorough.

The null hypothesis for every contrast is that the appended text does nothing: the sign of
each task-level paired difference is exchangeable.

### What these hypotheses are not

They are not claims that the model is motivated, encouraged, or trying harder. "Effort",
"motivation" and "seriousness" name **hypotheses about observable output behaviour** —
more complete reasoning, more checking, better constraint adherence, fewer errors, higher
task success. A confirmed effect would be a fact about prompting, not about inner life.

## Conditions

One independent variable — text appended to an otherwise identical base prompt — at four
levels. See `conditions.json`.

| ID | Role | Appended text |
|---|---|---|
| A | control | *(nothing)* |
| B | active control | Good luck. Do your best. |
| C | treatment | May the Force be with you. |
| D | active control | Be especially thorough and check your work carefully. |

## Design

20 tasks (5 reasoning, 5 critique and error detection, 5 planning, 5 writing) x 4
conditions x 3 repetitions = 240 generations. Every generation starts in a fresh model
context. Pilot: 5 tasks x 4 x 2 = 40 generations, which validates the workflow and is
explicitly **not** powered to test anything.

## Primary outcome

**Blind judge `task_success`**, 1–5, one judgment per generation, judge blind to condition
and shown the base task only.

## Pre-registered primary contrasts

| ID | Question |
|---|---|
| `C_vs_A` | Does the phrase beat no added text? |
| `C_vs_B` | Does it beat generic encouragement? |
| `C_vs_D` | Does it beat an explicit effort instruction? |

`B_vs_A` and `D_vs_A` are secondary and descriptive.

## Secondary outcomes

Objective score (planted issues and machine-checkable constraints, no judge involved);
the five non-primary judge dimensions; pairwise preference with randomised A/B order.

## Behavioural indicators (descriptive only)

Response length, coverage of relevant considerations, verification markers, alternatives
considered, caveats identified, self-correction markers, constraint completion.

These are regular-expression counts over text. They are **heuristic proxies** and are never
reported as tests. A response can check its work without using any marker phrase, and use
marker phrases without checking anything.

## Analysis plan

Pairing is within (task, repetition). Paired differences are averaged to the task level and
the **task** is the unit of analysis for inference, because responses to the same task are
not independent.

- Point estimate: mean task-level paired difference.
- Interval: cluster bootstrap over tasks, 10,000 draws, seeded.
- Test: two-sided sign-flip permutation test on task-level differences, exact for n ≤ 20.
- Effect size: Cohen's dz on task-level differences.
- Multiplicity: Holm adjustment across the three primary contrasts.
- Pairwise: win rate excluding ties, Wilson interval, exact binomial test.

## Decision rule

A contrast counts as **demonstrated** only if, on the primary outcome, all three hold:

1. the treatment's point estimate is higher,
2. the 95% interval excludes zero,
3. the Holm-adjusted permutation p < 0.05.

Anything else is reported as **not demonstrated**, including a positive-looking difference
with an interval spanning zero. Direction without significance is reported as direction,
never as an effect.

## Impact classification

Per `METHODOLOGY.md`: Strong positive / Positive / Neutral / Negative / Inconclusive. A
pilot run cannot assign one, and cannot move the confidence stage off **Observed**.

## Known confounds, declared in advance

1. **Prompt length.** A is shorter than B, C and D by construction. `C_vs_B` and `C_vs_D`
   are the contrasts that isolate the phrase from the mere presence of appended text.
2. **Blinding leakage.** A response may echo its condition's text back. Outputs are never
   edited; the echo rate is measured and reported.
3. **Judge self-preference** when judge and generator are the same model.
4. **Length bias** in LLM judging. The objective score is immune to it and is the check.
5. **Harness context.** Generation runs through the `claude` CLI with its own preamble,
   identical across conditions. Results describe behaviour in that harness.
6. **Sampling settings** are not exposed by the CLI backend.
7. **Single model, single phrase position.** Nothing generalises without replication.

## What would falsify H3

C indistinguishable from B and D, while all three beat A. That would mean the effect is
about appending text, not about this phrase — a negative result for the project's premise,
and one that stays in the repository per `METHODOLOGY.md`.
