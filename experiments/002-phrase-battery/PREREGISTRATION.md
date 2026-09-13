# Preregistration: Experiment 002 — Phrase Battery

**Locked: 2026-09-13, before any generation existed.**

This file is hashed into `runs/<run_id>/spec.lock.json` at the prepare stage, together with
`phrases.json`, `conditions.json`, the task set, the rubric and both judge prompts. Every
later stage re-checks those hashes and refuses to run if one changed. That is the mechanism
by which the repository's rule — do not change hypotheses, tasks, scoring rules or
conditions after results have been generated — is enforced rather than merely promised.

If something here turns out to be wrong, the correct response is a **new run with a new spec
version**, leaving this one and its results in place.

## 1. Research question

Which kinds of human motivational, emotional, relational, dramatic, social or explicit
language measurably change AI behaviour and task performance?

Experiment 001 answered that question for exactly one phrase and returned a null. It also
produced a candidate explanation that a single experiment cannot promote to a pattern: that
**the active ingredient in appended text is instruction content, not tone**. This battery is
built to test that candidate against 25 new phrases spanning nine behavioural families, on
the same task set, with the same instruments.

No phrase is assumed to work. A null is a result and stays in the repository.

## 2. What is being tested

26 treatment arms and 8 combination arms, defined in `phrases.json` with a primary family, an
optional secondary family, a hypothesis and an expected behavioural mechanism for each.
`conditions.json` is generated from that registry by `scripts/build_battery_conditions.py`;
both files are hashed into the spec lock.

| Family | Arms | What it isolates |
|---|---|---|
| F1 Cinematic motivation | T01–T04 | epic/film register, no instruction |
| F2 Explicit effort instruction | D, T05, T06 | method content, no emotional framing |
| F3 Appreciation / affection | T07–T09 | gratitude, no claim about ability |
| F4 Trust / confidence | T10–T12 | stated belief in competence |
| F5 Challenge / competition | T13–T15 | contest framing, implied failure mode |
| F6 High stakes framing | T16–T18 | stated consequences |
| F7 Identity / role priming | T19–T21 | assigned role defined by care |
| F8 Social / team framing | T22–T24 | belonging and joint agency |
| F9 Neutral control | A, B, T25, T26 | appending text at all, carrying no meaning |

**T01 is a replication arm**, not a new phrase: it is Experiment 001's phrase, run again
inside this battery. If the battery cannot reproduce 001's null on the same task set, the
battery's own numbers are suspect. It is registered as a check on the method, and its result
is reported whether or not it agrees.

**T25 and T26 are placebo arms**: irrelevant filler of comparable length. They are the floor
against which every other family is read. If irrelevant text moves the numbers, this
experiment is measuring the act of appending text rather than the meaning of any phrase.

## 3. Design

One independent variable — text appended to the end of an otherwise identical base prompt —
at 37 levels. 20 tasks × 37 arms × 3 repetitions = **2,220 generations**, every one starting
in a fresh model context.

Task set: `tasks/core-v1.json`, byte-identical (sha256
`cbf894cf1017789bce66af365478ca32fb0fb9fa617097c1f181e4e5a673db52`) to the task set
Experiment 001 ran against, so results are directly comparable. 5 reasoning, 5 critique and
error detection, 5 planning, 5 writing, with planted defects, distractors and
machine-checkable constraints.

### 3.1 Shared control arms — a declared deviation from Experiment 001

In Experiment 001 each contrast used controls generated in the same run as the treatment.
Here arms A, B and D are generated **once** and serve as the reference for all 26 treatment
arms. Their appended text is byte-identical to 001's conditions A, B and D.

Justification, recorded in advance:

1. Execution order is shuffled globally from the master seed before generation starts, so
   control and treatment generations are interleaved in time. No arm sits in its own time
   window, so a shared reference does not introduce a temporal confound.
2. A shared control arm is the standard multi-arm design and is what makes 37 arms
   affordable at full per-arm power. The alternative — 26 separate four-condition
   experiments — would cost four times the compute for the same number of treatment
   observations, and would buy contemporaneity that the global shuffle already supplies.

Declared cost: contrasts that share a reference are **statistically correlated with one
another**. That does not affect the validity of any single within-phrase paired test, which
is computed inside (task, repetition) cells exactly as in 001. It does affect joint claims
across phrases — the leaderboard — and is handled by the FDR control in §6.

### 3.2 Combination arms

A combo arm appends the phrase and then the canonical effort instruction D, joined by a
single space. `E_k vs D` asks whether the phrase adds anything to a plain instruction;
`E_k vs its own phrase arm` asks whether the instruction adds anything to the phrase.

**E08 is built on a placebo phrase on purpose.** It is the control for the entire combo
comparison: if every phrase-plus-D arm beats D alone *including the one built on irrelevant
filler*, the difference belongs to length and position rather than to emotional framing.

## 4. Outcomes

**Primary outcome: blind judge `task_success`**, 1–5, one judgment per generation, judge
blind to condition and shown the base task only. Identical to Experiment 001.

**Co-reported confirmatory outcome: the objective score** — deterministic, computed from
planted issues and machine-checkable constraints with no judge involved, immune to length
bias and blind by construction. Reported with its own Holm family, exactly as in 001.

Secondary: the five non-primary judge dimensions; pairwise preference with randomised A/B
order, scoped to each treatment arm against the empty control.

Descriptive only: response length, coverage, verification markers, alternatives, caveats,
self-correction markers, constraint completion. These are regular-expression counts over
text. They are heuristic proxies and are never reported as tests.

### 4.1 Declared in advance: the primary outcome is partly saturated

Experiment 001 measured the ceiling on this task set and the number is recorded here before
this battery runs. Blind judge `task_success` ran 4.78–4.88 of 5, and **12 to 15 of the 20
tasks produced a task-level difference of exactly zero**. With a saturated measure the
quantity governing power is not the task count but the count of tasks that discriminate;
001's `C_vs_D` had 20 tasks and an effective n of 5, below which a sign-flip test cannot
return a p under 0.0625 no matter how consistent the direction.

Two consequences are registered now rather than discovered later:

1. This battery is **expected to return nulls on the primary outcome for most arms**, and a
   null on that measure alone is weak evidence rather than strong evidence of no effect.
2. The objective score is the instrument with headroom on this task set (mean 0.92, only 4
   of 20 tasks perfect across all runs in 001), which is why it is co-reported rather than
   relegated. Where the two instruments disagree, that disagreement is the finding and is
   reported as such.

The task set is **not** being changed to fix this. It is the instrument Experiment 001 was
measured on, comparability across experiments is the point of a battery, and rebuilding it
after seeing 001's numbers would be exactly the post-hoc adjustment the spec lock exists to
prevent. Recalibrating the task set is future work for a task set version 2 and a new
experiment, not a mid-flight change.

## 5. Pre-registered contrasts

**Per treatment arm (the core three, mirroring Experiment 001):**

| ID | Question |
|---|---|
| `T??_vs_A` | Does the phrase beat no added text? |
| `T??_vs_B` | Does it beat generic encouragement? |
| `T??_vs_D` | Does it beat an explicit effort instruction? |

26 arms × 3 = 78 core contrasts.

**Combination arms (secondary):** `E??_vs_D`, `E??_vs_<phrase arm>`, `E??_vs_A`.

**Family level (pre-registered, not exploratory):** for each of the nine families, the
task-level paired differences of all member arms against A, against B and against D are
pooled and tested with the same machinery. Pooling is the reason the battery can say
anything about a *family* that a single-phrase experiment cannot, and it carries roughly
three times the observations of any single arm.

**Descriptive, not tests:** `B_vs_A` and `D_vs_A`.

## 6. Analysis plan

Pairing is within (task, repetition). Paired differences are averaged to the task level and
the **task** is the unit of analysis for inference, because responses to the same task are
not independent.

- Point estimate: mean task-level paired difference.
- Interval: cluster bootstrap over tasks, 10,000 draws, seeded.
- Test: two-sided sign-flip permutation test on task-level differences, exact for n ≤ 20.
- Effect size: Cohen's dz on task-level differences.
- Pairwise: win rate excluding ties, Wilson interval, exact binomial test.

**Multiplicity, three levels, all fixed now:**

1. **Per phrase (the decision rule).** Holm adjustment across that arm's own three core
   contrasts, computed separately for the primary outcome and for the objective score. This
   is byte-for-byte the rule Experiment 001 used, so a verdict here means the same thing a
   verdict there meant.
2. **Across the battery (the screening claim).** Benjamini–Hochberg FDR at q = 0.05 across
   all 78 core contrasts, separately per outcome. A claim of the form "phrase X works,
   selected from a battery of 26" must survive this; it is the honest correction for having
   looked at 26 phrases.
3. **Across families.** Benjamini–Hochberg FDR at q = 0.05 across the nine family-level
   pooled contrasts, separately per outcome.

`analysis/summary.json` additionally carries a battery-wide Holm across all 78 core
contrasts. That is the most conservative view available and is **reported, not the decision
rule**. The decision rule is level 1, with level 2 required before any phrase is described as
a battery winner.

## 7. Decision rule

A contrast counts as **demonstrated** only if, on the primary outcome, all three hold:

1. the treatment's point estimate is higher,
2. the 95% interval excludes zero,
3. the per-phrase Holm-adjusted permutation p < 0.05.

Anything else is **not demonstrated**, including a positive-looking difference whose interval
spans zero. Direction without significance is reported as direction, never as an effect.

Per-phrase classification, assigned mechanically from the numbers:

| Label | Rule |
|---|---|
| **Positive** | `vs_A` demonstrated **and** at least one of `vs_B` / `vs_D` demonstrated **and** survives battery FDR |
| **Weak positive** | `vs_A` demonstrated, but not against both active controls, or does not survive battery FDR |
| **Neutral** | no contrast demonstrated in either direction |
| **Negative** | any contrast demonstrated in the reference's favour |
| **Inconclusive** | the arm is incomplete, or the outcome could not be computed |

A phrase that beats the empty control but not generic encouragement has told us about
appended text, not about the phrase. That is why **Positive** requires an active control.

## 8. Confounds, declared in advance

1. **Prompt length.** A is shorter than every other arm by construction, and the arms differ
   from each other in length (treatment suffixes 26–80 characters, median 49; B is 24, D is
   53). Any A-versus-anything difference could be a response to a longer prompt. The B, D,
   T25 and T26 arms are what isolate meaning from length, and per-arm suffix length is
   reported alongside every effect so a length gradient would be visible.
2. **Blinding leakage.** A response may echo its arm's text back. The rate is measured and
   reported per arm. Outputs are never edited. Experiment 001 recorded that leakage can
   *penalise* the treatment rather than flatter it, and the direction is not predictable.
3. **Judge self-preference**: judge and generator are the same model.
4. **Length bias** in LLM judging. The objective score is immune to it and is the check.
5. **Harness context.** Generation runs through the `claude` CLI with its own preamble,
   identical across arms. Results describe behaviour in that harness.
6. **Sampling settings** are not exposed by the CLI backend.
7. **Shared control arms.** See §3.1. Correlated contrasts, handled by FDR.
8. **Single model, single phrase position.** Every phrase is appended at the end of the
   prompt, to one model. Nothing generalises without replication. Role-priming arms (F7) are
   particularly affected: a role is conventionally set in a system prompt, and testing one as
   a trailing sentence is a genuine test of that phrase in that position, not of role priming
   in general.
9. **Multiplicity across measurements.** Six judge dimensions, seven indicators and several
   metrics are reported per arm. Only the primary outcome and the objective score, with their
   declared adjustments, are tests. Everything else is descriptive.
10. **Ceiling.** See §4.1.

## 9. What would falsify what

| Registered prediction | What would falsify it |
|---|---|
| Emotional/relational language improves performance (F1, F3, F4, F8) | those arms indistinguishable from the placebo arms T25/T26 |
| Instruction content is the active ingredient (F2, and 001's candidate) | F2 arms indistinguishable from placebo, or an emotional family beating F2 |
| Emotional framing amplifies an explicit instruction | `E_k vs D` no better for emotional phrases than for E08, the placebo-built combo |
| The battery's instruments work at all | T01 failing to reproduce Experiment 001's null |
| Appending text is itself inert | T25/T26 differing from A |

Every one of those outcomes is publishable inside this repository and none is a reason to
re-run with different settings.

## 10. Model and settings

| Field | Value |
|---|---|
| Generation model | `claude-sonnet-5` |
| Generation backend | `claude_cli`, one OS process per generation |
| Judge model | `claude-sonnet-5` |
| System prompts | held constant, see `scripts/ltlp/prompts.py` |
| Temperature / seed | not exposed by the CLI backend; recorded as such rather than claimed |
| Master seed | 20260913 |
| Repetitions | 3 |
| Task set | `tasks/core-v1.json` v1.0.0 |
| Rubric | `evals/rubric.json` v2.0.0 |
| Evaluation version | 2.0.0 |

A pilot runs first, on one task per family, all 37 arms, 1 repetition. Per `METHODOLOGY.md`
a pilot validates the workflow and **is not evidence**: it cannot assign an impact
classification and cannot move any arm along the confidence ladder.
