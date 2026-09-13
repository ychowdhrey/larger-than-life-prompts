# Experiment 002: Phrase Battery

## The question

Which kinds of human motivational, emotional, relational, dramatic, social or explicit
language measurably change AI behaviour and task performance?

[Experiment 001](../001-may-the-force-be-with-you/) answered that for exactly one phrase and
returned a null. It also produced a candidate that a single experiment cannot promote to a
pattern:

> **The active ingredient in appended text is instruction content, not tone.**

The only condition that moved any measure in 001 was `D`, the one that plainly told the
model what to do. That is the reverse of the project's premise, and it was one data point.

This battery tests it against 25 new phrases spanning nine behavioural families, on the same
task set, with the same instruments, under the same decision rule.

It is also the experiment 001's own README asked for. Its closing note said the interesting
open question was "whether condition D's consistent lead over the control is real", and that
this "is its own experiment with D as the treatment, not a reinterpretation of this one".
Family F2 here is exactly that.

## Design

One independent variable — text appended to the end of an otherwise identical base prompt —
at 37 levels. **20 tasks x 37 arms x 3 repetitions = 2,220 generations**, each starting in a
fresh model context.

The locked statement of hypotheses, contrasts, analysis plan, multiplicity and decision rule
is in [PREREGISTRATION.md](PREREGISTRATION.md), committed before any generation existed.

### Nine behavioural families

Every arm carries a primary family, an optional secondary family, a hypothesis and an
expected mechanism, all in [phrases.json](phrases.json).

| Family | Arms | What it isolates |
|---|---|---|
| F1 Cinematic motivation | T01–T04 | epic or film register, carrying no instruction |
| F2 Explicit effort instruction | D, T05, T06 | method content, carrying no emotional framing |
| F3 Appreciation / affection | T07–T09 | gratitude, making no claim about ability |
| F4 Trust / confidence | T10–T12 | stated belief in competence |
| F5 Challenge / competition | T13–T15 | contest framing, implying a failure mode |
| F6 High stakes framing | T16–T18 | stated consequences |
| F7 Identity / role priming | T19–T21 | an assigned role defined by care |
| F8 Social / team framing | T22–T24 | belonging and joint agency |
| F9 Neutral control | A, B, T25, T26 | appending text at all, carrying no meaning |

### Three arms that are not phrases under test

**`T01` is a replication.** It re-runs Experiment 001's phrase inside this battery. If the
battery cannot reproduce 001's null on the same task set, the battery's own numbers are
suspect. It is a check on the instruments, not a new finding.

**`T25` and `T26` are placebos.** Irrelevant filler of comparable length — the weather, a
form. They are the floor every other family is read against. If irrelevant text moves the
numbers, this experiment is measuring the act of appending text rather than the meaning of
any phrase. Experiment 001 had no such arm.

**`E08` is a placebo-built combination arm**, and it is what makes "does emotional framing
amplify an explicit instruction" answerable at all. See below.

### Conditions

```text
A:  {task_prompt}

B:  {task_prompt}

    Good luck. Do your best.

T??: {task_prompt}

    {phrase}

D:  {task_prompt}

    Be especially thorough and check your work carefully.

E??: {task_prompt}

    {phrase} Be especially thorough and check your work carefully.
```

`A`, `B` and `D` are byte-identical to Experiment 001's conditions `A`, `B` and `D`.

### The combination arms

Eight arms append a phrase **and then** the canonical effort instruction. `E vs D` asks
whether the phrase adds anything to a plain instruction; `E vs its own phrase arm` asks
whether the instruction adds anything to the phrase.

`E08` is built on a placebo phrase. Without it the combination comparison is
uninterpretable: if every phrase-plus-instruction arm beats the instruction alone, that
could simply be what appending one more sentence does. `E08` measures exactly that, and the
reported quantity for every other combination arm is its lift over the instruction **minus
the placebo's lift**.

### Shared control arms — a declared deviation from Experiment 001

`A`, `B` and `D` are generated **once** and serve as the reference for all 26 treatment
arms, rather than being regenerated inside each comparison.

Execution order is shuffled globally from the master seed before generation starts, so
control and treatment generations are interleaved in time and no arm sits in its own time
window. That is what removes the temporal confound a shared reference would otherwise
introduce. The remaining cost is that contrasts sharing a reference are **statistically
correlated with one another**, which affects joint claims across phrases — the leaderboard —
rather than any single within-phrase paired test. The FDR level exists for that.

The alternative, 26 separate four-condition experiments, costs four times the compute for
the same number of treatment observations and buys contemporaneity the global shuffle
already supplies.

## Evaluation

**Primary outcome:** blind judge `task_success`, 1–5. Identical to Experiment 001.

**Co-reported confirmatory outcome:** the objective score — planted defects, distractors and
machine-checked constraints, no judge involved, immune to length bias, blind by
construction.

Both are necessary here, and the preregistration says why in advance: Experiment 001
measured the primary outcome's ceiling on this task set at 4.78–4.88 of 5, with 12 to 15 of
20 tasks producing a task-level difference of exactly zero. On a saturated measure the
quantity governing power is not the task count but the count of tasks that discriminate. The
objective score is the instrument with headroom (mean 0.92, only 4 of 20 tasks perfect).

**The task set is not rebuilt to fix that.** It is the instrument 001 was measured on,
comparability is the point of a battery, and changing it after seeing 001's numbers is
exactly the post-hoc adjustment the spec lock exists to prevent.

**Secondary:** the five non-primary judge dimensions; pairwise preference, scoped before the
run to each treatment arm against the empty control.

The judge never sees the arm, the sample id, or the condition-augmented prompt — only the
base task and a response under an opaque id.

## Decision rule

A contrast is **demonstrated** only if the point estimate favours the treatment, the 95%
interval excludes zero, and the Holm-adjusted permutation p is below 0.05 — with Holm
computed across that phrase's own three contrasts, byte-for-byte the rule Experiment 001
used.

| Label | Rule |
|---|---|
| **Positive** | beats control, beats an active control, and survives the battery-wide FDR |
| **Weak positive** | beats control, but not both of those |
| **Neutral** | no contrast demonstrated in either direction |
| **Negative** | a contrast demonstrated in the reference's favour, without beating control |
| **Inconclusive** | the arm is incomplete |

A phrase that beats an empty control but not generic encouragement has told us about
appended text, not about the phrase. That is why **Positive** requires an active control.

### Three levels of multiplicity, all fixed before the run

1. **Per phrase** — Holm across that arm's three contrasts. This is the decision rule.
2. **Across the battery** — Benjamini-Hochberg at q = 0.05 across all 78 core contrasts.
   Required before any phrase is called a battery winner; it is the correction for having
   looked at 26 phrases.
3. **Across families** — Benjamini-Hochberg at q = 0.05 across the nine families.

A battery-wide Holm is also recorded in `summary.json`. It is the most conservative view
available and is reported, **not** the decision rule.

## Running it

```bash
# offline, full scale, zero cost: validates the plumbing
python3 ../../scripts/experiment.py all --config config/mock.json --workers 8

# pilot: 74 generations, workflow validation only, not evidence
python3 ../../scripts/experiment.py all --config config/pilot.json --workers 8

# full: 2,220 generations
python3 ../../scripts/experiment.py all --config config/full.json --workers 16

python3 ../../scripts/experiment.py status --config config/full.json
python3 ../../scripts/experiment.py verify --config config/full.json
```

Resumable: interrupt any stage and re-run it, and nothing already produced is regenerated.
Raw outputs are write-once with a sha256 ledger that is checked in both directions. The spec
— tasks, conditions, **phrases**, rubric, both judge prompts and the preregistration — is
hashed at prepare time and every later stage refuses to run if any of it moved.

`conditions.json` is generated from `phrases.json` by
[`scripts/build_battery_conditions.py`](../../scripts/build_battery_conditions.py) and is
never hand-edited; `--check` fails if the committed file is not what the registry produces.

## Model record

See `runs/<run_id>/run_meta.json` for the authoritative record of any run.

Provider: Anthropic, via the `claude` CLI (one OS process per generation)

Model: `claude-sonnet-5` · Judge model: `claude-sonnet-5`

Temperature / sampling: not exposed by the CLI backend, recorded as such

Task set: `tasks/core-v1.json` v1.0.0, sha256
`cbf894cf1017789bce66af365478ca32fb0fb9fa617097c1f181e4e5a673db52`, byte-identical to the
set Experiment 001 ran against · Rubric 2.0.0 · Prompt 1.0.0 · Workflow 1.1.0

## Results

Full run in progress. This section is written from `runs/full-002/analysis/` once the run
completes; the generated report is [analysis.md](analysis.md).
