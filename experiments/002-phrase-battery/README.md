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

**Full run complete: 2,220 generations, 2026-09-13, `runs/full-002`.** Generated report in
[analysis.md](analysis.md), machine readable in `runs/full-002/analysis/`.

Pipeline health: 2,220/2,220 generations, 2,220/2,220 objective scores, 2,220/2,220 blind
judgments and 1,560/1,560 pairwise comparisons. **Zero blinding leaks** in 2,220 responses.
Spec lock, prompt equivalence across all 37 arms, and the sha256 ledger verified in both
directions. Generation cost 60.61 USD.

The container running the judging stages was interrupted part-way through and 729 judge
units failed with the CLI killed mid-call. They were re-run under the same configuration
per `METHODOLOGY.md`; the retry completed 456 blind and 415 pairwise units with 0 failures.
No raw output was touched, because failures are recorded under `state/failures/` and raw
outputs are write-once. The failure records are kept.

### The headline: 26 of 26 arms are Neutral

No phrase met the preregistered decision rule on the primary outcome. Not one, in either
direction.

### The primary outcome ran out of room, and this run proves it

The empty control scored **4.950 of 5** on blind judge task success, against 4.783 in
Experiment 001. At that level a phrase has almost nowhere to go but down, and the numbers
show exactly that shape:

| Measure | Arms above the empty control | Arms below | Median effect |
|---|---:|---:|---:|
| Blind judge task success (A = 4.950 / 5) | **1** of 26 | 25 | -0.100 |
| Objective score (A = 0.927) | **11** of 26 | 15 | -0.006 |

The same 26 arms, the same generations, two instruments. On the saturated one almost
everything looks harmful; on the one with headroom the arms sit symmetrically around the
control. **"Appended text makes things worse" is an artefact of the ceiling, not a finding.**
Effective n says the same thing: the `vs_A` contrast discriminated on a median of 5 of 20
tasks on the judge measure and 9 of 20 on the objective score.

This was declared in advance — see PREREGISTRATION.md section 4.1, written before the run
from Experiment 001's measurements — which is the only reason it can be read as a property
of the instrument rather than argued about after the fact.

### The replication arm worked, and it cost Experiment 001 its candidate pattern

`T01` re-ran Experiment 001's phrase inside this battery. It reproduced the null: **-0.033**
on the primary outcome against the empty control, **+0.016** on the objective score, both
intervals spanning zero. The instruments agree with 001 about the phrase.

They do not agree with 001 about anything else. The three shared control arms carry
byte-identical text in both experiments, so the difference between runs is pure run-to-run
variation:

| Same appended text | Exp 001 | Exp 002 | Drift |
|---|---:|---:|---:|
| A control, judge task success | 4.783 | 4.950 | **+0.167** |
| B generic encouragement, judge task success | 4.800 | 4.883 | +0.083 |
| D explicit effort, judge task success | 4.883 | 4.800 | **-0.083** |
| B generic encouragement, objective | 0.914 | 0.948 | **+0.034** |
| D explicit effort, objective | 0.953 | 0.935 | -0.018 |

`D_vs_A` on the primary outcome was **+0.100 in Experiment 001 and -0.150 here** — the same
sentence, the same task set, the same model, opposite signs. On the objective score D's lead
shrank from +0.031 to +0.008, and B overtook it.

Experiment 001 offered one candidate pattern: *the active ingredient in appended text is
instruction content, not tone.* **It does not replicate.** It was one run's noise, and the
only reason that is visible is that this battery re-ran the same controls.

The drift on identical text (up to 0.167 on the primary outcome, 0.034 on the objective
score) is **larger than almost every treatment effect in the battery**. That number is the
noise floor, and nothing smaller than it should be called a result.

### No behavioural family separates from irrelevant text

PREREGISTRATION.md section 9 names the falsification criterion for the emotional families:
*indistinguishable from the placebo arms*. Pooling each family's member arms and comparing
them against the two placebo arms — exploratory, since only the family-versus-reference
contrasts were preregistered as tests:

| Family | Primary vs placebo | 95% CI | Objective vs placebo | 95% CI |
|---|---:|---|---:|---|
| F1 Cinematic motivation | +0.108 | [-0.021, +0.279] | +0.024 | [-0.000, +0.051] |
| F2 Explicit effort instruction | +0.083 | [-0.050, +0.242] | +0.020 | [-0.002, +0.043] |
| F3 Appreciation / affection | +0.003 | [-0.122, +0.142] | +0.010 | [-0.015, +0.042] |
| F4 Trust / confidence | -0.086 | [-0.278, +0.114] | +0.002 | [-0.030, +0.036] |
| F5 Challenge / competition | +0.069 | [-0.108, +0.269] | +0.023 | [-0.009, +0.062] |
| F6 High stakes framing | +0.025 | [-0.097, +0.156] | +0.015 | [-0.011, +0.041] |
| F7 Identity / role priming | -0.014 | [-0.164, +0.158] | +0.005 | [-0.021, +0.031] |
| F8 Social / team framing | +0.064 | [-0.064, +0.242] | +0.012 | [-0.013, +0.041] |

**Every interval spans zero. Every BH q is 1.000.** Eight behavioural families, 24 phrases,
1,440 generations, and none of them is distinguishable from telling the model about the
weather.

Read against the empty control instead, three families are *demonstrably worse* on the
primary outcome after FDR — identity/role priming (q = 0.009), appreciation (q = 0.035) and
trust/confidence (q = 0.035). That comparison is the ceiling artefact above: the placebo
family is negative too (-0.142), and the objective score shows none of it.

### Emotional framing does not amplify an explicit instruction

Eight combination arms appended a phrase and then the canonical effort instruction. `E08` is
built on a placebo phrase, so it measures what appending *any* extra sentence plus the
instruction does. Every other combination arm's lift over the instruction, minus the
placebo's lift:

| Arm | Family | Lift over placebo combo (objective) | 95% CI |
|---|---|---:|---|
| E01 | Cinematic | +0.0115 | [-0.018, +0.046] |
| E02 | Appreciation | +0.0104 | [-0.020, +0.048] |
| E03 | Trust | +0.0173 | [-0.008, +0.044] |
| E04 | Challenge | +0.0079 | [-0.016, +0.033] |
| E05 | High stakes | +0.0101 | [-0.016, +0.038] |
| E06 | Identity | -0.0098 | [-0.035, +0.012] |
| E07 | Social | -0.0184 | [-0.049, +0.007] |

All seven intervals span zero. Adding emotional framing on top of "be especially thorough"
buys what adding a sentence about the weather buys.

### What appended text *does* change: the look of the answer

This is where the battery is not null at all, and it is the most useful thing in it. These
are secondary and descriptive measures — multiplicity applies and none is a preregistered
test — but the pattern is consistent across arms.

`T06`, **"Check every number and every claim before you finish."** — the one arm that names
error checking:

| Measure | Effect vs empty control | 95% CI |
|---|---:|---|
| Judge **error_checking** | **+0.583** | [+0.183, +1.017] |
| Judge thoroughness | +0.300 | [+0.083, +0.550] |
| Response length (words) | **+44.98** | [+22.7, +68.5] |
| **Task success (primary)** | +0.017 | [-0.083, +0.117] |
| **Objective score** | +0.012 | [-0.017, +0.043] |

`T14`, **"This one is harder than it looks. Prove me wrong."** — writes **+109.6 words**
(CI [+71.3, +147.6]), scores +0.317 on judged thoroughness, and moves the primary outcome by
-0.017 and the objective score by +0.018.

**A targeted instruction reliably moves the dimension it names, and reliably fails to move
whether the answer is right.** Telling the model to check produces more checking *language*
and more *judged* checking. It does not produce a better answer on a task set with planted
defects to find.

### Pairwise preference measures length

Blind pairwise preference against the empty control, over 1,560 comparisons: treatment win
rate 0.472 excluding ties. Two arms win convincingly — `T14` at 0.733 (p = 0.0025) and `T15`
at 0.721 (p = 0.0054) — though neither survives BH correction across the 26 arms
(q = 0.064 and 0.070), and both are flat on both scored outcomes.

Across the 26 arms:

| Correlation with mean response length | r |
|---|---:|
| Pairwise win rate against the empty control | **+0.767** |
| Objective-score effect against the empty control | **+0.175** |

How much longer a phrase makes the answer explains most of the variance in which answer a
blind judge says it would use, and almost none of the variance in whether the answer is
better. This is the length bias `METHODOLOGY.md` names as a confound, measured directly
rather than assumed.

### Adverse effects

Four contrasts meet the full decision rule **in the reference's favour**, all on the
objective score and all against generic encouragement: `T07_vs_B` (-0.038, Holm p = 0.023),
`T11_vs_B` (-0.071, Holm p = 0.019), `T20_vs_B` (-0.039, Holm p = 0.029) and `T25_vs_B`
(-0.045, Holm p = 0.006). None survives the battery-wide FDR (q = 0.15 to 0.19), and the
last of them is a **placebo** arm, which is the reason to read the whole set as B running
high in this run rather than as four phrases being harmful.

The largest single negative effect in the battery is `T11`, **"You are the best there is at
this. I know you will get it right."**: -0.333 on the primary outcome and **-0.051** on the
objective score against the empty control, the worst arm on both instruments independently.
The preregistration recorded the competing prediction for family F4 in advance — that stated
trust may *license less checking*, because the work is pre-approved. The direction is
consistent with it. The evidence is not sufficient to claim it: `T11_vs_A` on the objective
score has Holm p = 0.073 and BH q = 0.427.

## Conclusion

**Impact: Neutral for all 26 arms. Status: Observed.**

Twenty-five new phrases across nine behavioural families, measured at 60 generations each
against three shared controls on the same task set as Experiment 001, produced **no
demonstrated improvement on any contrast**. No family separates from irrelevant filler. No
emotional framing amplifies an explicit instruction. The one phrase that plainly instructs
the model to check its work moves judged checking by +0.58 and the objective score by +0.012.

Two results here are worth more than the nulls:

1. **Experiment 001's candidate pattern did not replicate, and reversed.** `D_vs_A` went from
   +0.100 to -0.150 on identical text. A battery with shared controls and a replication arm
   is what made that visible, and it is an argument for running phrases in batteries rather
   than one at a time.
2. **Appended text changes style, not correctness.** Length explains pairwise preference
   (r = +0.767) and not objective performance (r = +0.175). A phrase can make an answer that
   a blind judge prefers, reads as more thorough, and contains more checking language, while
   leaving what the answer actually gets right exactly where it was.

On the confidence ladder every arm stays at **Observed**. None survived a controlled
evaluation, because there was nothing to survive.

## Next action

1. **Do not re-run `config/full.json` under a new `run_id` hoping for a different number.**
   The design was preregistered, the run completed clean, and the answer is a null on 26
   arms.
2. **The task set is now the binding constraint, and this run quantified it.** The judge
   measure discriminates on a median of 5 of 20 tasks; the objective score on 9 of 20; the
   control sits at 4.95 of 5. The honest next step is a **task set v2** hard enough that the
   control fails a meaningful fraction of the time, then a fresh experiment. That will break
   both existing spec locks, which is the intended behaviour. `runs/full-002/` and this
   report stay as they are.
3. **The open question this run generated is about measurement, not about phrases.** Between-
   run drift on identical text reached 0.167 on the primary outcome — larger than nearly
   every treatment effect measured here. Before another phrase is tested, it is worth running
   the same control arm several times under different `run_id`s to characterise that floor
   directly. Any future effect smaller than it is not interpretable.
