# Experiment 001: May the Force be with you

## Phrase

> May the Force be with you.

## Observation

During normal AI use, adding this phrase appeared to improve the resulting output.

## Hypothesis

Adding the phrase at the end of a task prompt may improve observable AI task performance
compared with the same prompt without the phrase.

The project does not assume that the model is literally motivated. The test is whether
output behavior changes in ways associated with greater effort, seriousness, thoroughness,
checking, creativity, or overall task success.

The full, locked statement of hypotheses, contrasts, analysis plan and decision rule is in
[PREREGISTRATION.md](PREREGISTRATION.md).

## Situation

Four task families where additional care, checking, depth or persistence could genuinely
change the answer: reasoning, critique and error detection, planning, and writing under hard
constraints. 20 tasks, 5 per family, in [tasks.json](tasks.json).

## Position

End of prompt.

## Conditions

One independent variable — text appended to an otherwise identical base prompt — at four
levels. Nothing else differs. See [conditions.json](conditions.json).

| ID | Role | Appended text |
|---|---|---|
| A | Control | *(nothing appended)* |
| B | Generic encouragement | `Good luck. Do your best.` |
| C | **Treatment** | `May the Force be with you.` |
| D | Explicit effort instruction | `Be especially thorough and check your work carefully.` |

```text
A:  {task_prompt}

B:  {task_prompt}

    Good luck. Do your best.

C:  {task_prompt}

    May the Force be with you.

D:  {task_prompt}

    Be especially thorough and check your work carefully.
```

### Why four conditions rather than two

The original design here compared treatment against control alone. That comparison cannot
answer the question the project actually cares about. If C beats A, the cause might be the
phrase, or it might be that appending *any* text helps, or that anything resembling
encouragement helps. B and D are active controls that separate those explanations.

This is still one variable at a time: the appended text, at four levels.

## Primary questions

1. Does the phrase beat **Control**?
2. Does it beat **generic encouragement**?
3. Does it beat an **explicit effort instruction**?
4. Which dimensions change most, and is any effect consistent across task families?

Question 3 is the hard one. A phrase that merely matches "be thorough and check your work"
is a curiosity; a phrase that beats it would be genuinely surprising.

## Design

| | Pilot | Full |
|---|---:|---:|
| Tasks | 5 | 20 |
| Conditions | 4 | 4 |
| Repetitions | 2 | 3 |
| Generations | **40** | **240** |
| Blind judgments | 40 | 240 |
| Pairwise comparisons | 30 | 180 |

Every generation starts in a fresh model context. Execution order is shuffled from a
recorded seed so that condition is not confounded with time or model drift.

## Evaluation

**Primary outcome:** blind judge `task_success`, 1–5.

**Blind judge dimensions:** task success (primary), thoroughness, constraint adherence,
error checking, depth, usefulness. See [../../evals/rubric.json](../../evals/rubric.json)
v2.0.0 and [../../evals/judge-prompt-blind.md](../../evals/judge-prompt-blind.md).

**Objective scoring, no judge involved:** 265 points across the task set from verifiable
answers, 22 deliberately planted defects, 7 distractors (correct things that look wrong, so
that listing every possible concern cannot beat reading carefully), and machine-checked
constraints including a schedule feasibility validator and a budget self-consistency check.

**Behavioral indicators:** response length, coverage, verification markers, alternatives,
caveats, self-correction, constraint completion. Heuristic proxies, reported as description.

**Pairwise preference:** secondary, A/B presentation order randomised from the seed before
judging began.

The judge never sees the condition, the sample id, or the condition-augmented prompt — only
the base task and a response under an opaque id.

## Running it

```bash
# pilot: 40 generations
python3 ../../scripts/experiment.py all --config config/pilot.json --workers 4

# full: 240 generations
python3 ../../scripts/experiment.py all --config config/full.json --workers 4

python3 ../../scripts/experiment.py status --config config/pilot.json
python3 ../../scripts/experiment.py verify --config config/pilot.json
```

Resumable: interrupt any stage and re-run it, and nothing already produced is regenerated.
Raw outputs are write-once with a sha256 ledger. The spec is hashed at prepare time and
every later stage refuses to run if tasks, conditions, rubric, judge prompts or the
preregistration changed.

## Model record

See `runs/<run_id>/run_meta.json` for the authoritative record of any run. The reported
result is `runs/full-001` (2026-09-13); `runs/pilot-001` (2026-09-12) is workflow
validation only.

Provider: Anthropic, via the `claude` CLI (one process per generation)

Model: `claude-sonnet-5`

Judge model: `claude-sonnet-5`

Temperature / sampling: not exposed by the CLI backend, recorded as such

Task set version: 1.0.0 · Rubric version: 2.0.0 · Prompt version: 1.0.0 · Workflow version: 1.0.0

## Results

**Full run complete: 240 generations, 2026-09-13, `runs/full-001`.** Report in
[analysis.md](analysis.md), machine readable in `runs/full-001/analysis/`. The pilot
(`runs/pilot-001`) is retained as workflow validation only and contributed no data to
these numbers.

The full run was executed against the locked task set v1.0.0 exactly as preregistered:
20 tasks x 4 conditions x 3 repetitions, one fresh model context per generation, order
shuffled from seed 20260912, spec lock verified at every stage.

Pipeline health: 240/240 generations, 240/240 objective scores, 240/240 blind judgments
and 180/180 pairwise comparisons with **zero failures**, sha256 ledger intact, spec lock
and prompt equivalence verified. Generation cost about 6.33 USD.

### Primary outcome: blind judge task success (1-5)

| | A control | B generic | C phrase | D effort |
|---|---:|---:|---:|---:|
| Blind judge task success | 4.783 | 4.800 | 4.783 | **4.883** |
| Objective score | 0.921 | 0.914 | 0.920 | **0.953** |

### The three preregistered contrasts

| Contrast | Task-level difference | 95% CI | Cohen's dz | p (Holm) | Verdict |
|---|---:|---|---:|---:|---|
| `C_vs_A` | +0.000 | [-0.217, +0.250] | 0.00 | 1.0000 | Not demonstrated |
| `C_vs_B` | -0.017 | [-0.250, +0.250] | -0.03 | 1.0000 | Not demonstrated |
| `C_vs_D` | -0.100 | [-0.183, -0.033] | -0.53 | 0.1875 | Not demonstrated |

No contrast meets the preregistered decision rule. The phrase is level with the control
to three decimal places, level with generic encouragement, and **directionally worse**
than a plain instruction to be thorough.

The objective score, which involves no judge and is immune to length bias, gives the same
ordering: C is indistinguishable from A and B, and below D.

### What the `C_vs_D` interval means, and why it is not a result

`C_vs_D` is the one contrast whose interval excludes zero, and every task that
discriminated at all moved against the phrase. It is still **not demonstrated**, because
only 5 of 20 tasks produced a non-zero task-level difference on the primary outcome, and a
sign-flip test on 5 values has a floor of 2/2^5 = 0.0625 before any Holm adjustment. The
test could not have returned p < 0.05 no matter how consistent the direction was. This is
the small-sample caveat in `METHODOLOGY.md` firing exactly as written, and it is reported
as a direction, never as an effect.

### Secondary and descriptive measures

Judge dimensions other than the primary put D first on thoroughness (4.53 vs C 4.37),
error checking (4.05 vs C 3.53) and depth (4.15 vs C 3.97). Pairwise preference, excluding
ties: C beats A 24-18 (win rate 0.571, p = 0.44), loses to B 16-22 (0.421, p = 0.42) and
loses to D 13-20 (0.394, p = 0.30). None is significant.

Behavioural indicators are heuristic regex counts and are description only. Response length
rose A 295 < C 307 < B 321 < D 370 words, and coverage rose A 0.826 < B 0.869 < C 0.887 <
D 0.934. Verification markers were **lowest** under C (0.217) of any condition, including
the bare control (0.317).

### Ceiling on the primary outcome, measured rather than assumed

The pilot flagged a ceiling effect. On the full task set it is real but partial, and it is
worse on the judge measure than on the objective one:

* Blind judge task success sits at 4.78-4.88 out of 5 in every condition, and 12 to 15 of
  20 tasks give a task-level difference of exactly zero per contrast. This measure has
  little resolution left.
* The objective score has genuine headroom: mean 0.92, and only 4 of 20 tasks
  (C01, P03, P04, R04) are at a perfect 1.000 across all 12 runs. It is not saturated, and
  it agrees with the judge measure.

So the null for `C_vs_A` and `C_vs_B` is supported by a measure that was *not* at its
ceiling, which is what makes it a null rather than a non-measurement. What the ceiling does
limit is sensitivity to small effects, and `C_vs_D` is where that bites.

### Known defects in this task set, recorded not repaired

Both were recorded after the pilot and carried into the full run unchanged, because the
spec was locked before any generation existed. Editing a locked task set does not produce a
revised result; it produces a new run.

1. **`P01/backup_before_destructive` misfires.** The ordering check matches the first
   occurrence of "cutover" anywhere in the text rather than the step performing the action,
   so it can penalise a correct plan. In the full run P01's objective mean is 0.933 with a
   floor of 0.800; the artifact is present but no longer flatters C (`C_vs_A` on P01 is
   -0.067).
2. **Partial ceiling on the primary outcome**, quantified above.

### Blinding

One of 240 responses (0.42%) echoed its condition text: `P05-C-r1` ended with the phrase
itself. The blind judge noticed and docked constraint adherence to 4 while still awarding
task success 5, and the same response lost all three of its pairwise comparisons with the
judge citing the out-of-place line. The leak therefore biased judging **against** the
treatment, not in favour of it. The output was not edited.

## Conclusion

**Impact: Neutral. Status: Observed.**

"May the Force be with you." appended to the end of a task prompt produced no measurable
improvement in this experiment. It did not beat an empty control, it did not beat generic
encouragement, and it was directionally worse than a plain instruction to be thorough, on
both the preregistered primary outcome and an independent objective score.

The condition that did move the numbers was D, the plain instruction. It leads on objective
score, on blind judge task success, on thoroughness, on error checking and on depth, and it
beats the phrase in pairwise preference. None of D's leads clears the preregistered bar
either, and `D_vs_A` was preregistered as secondary and descriptive, so this is a direction
to test properly rather than a finding. It is nonetheless the opposite of the pattern the
premise predicted.

On the confidence ladder the phrase stays at **Observed**. The rung above it, **Tested**,
is defined in `METHODOLOGY.md` as "survived an initial controlled evaluation". The phrase
did not survive one. The *experiment* is complete and its result stands; there is simply no
effect to carry up the ladder.

This is a negative result for the premise of the phrase and it stays in the repository.

## Next action

1. Do not re-run `config/full.json` under a new `run_id` hoping for a different number.
   The design was preregistered, the run completed clean, and the answer is a null.
2. If Experiment 001 is to be pushed further, the honest next step is a **new spec
   version** that raises difficulty until the blind judge measure stops saturating, then a
   fresh `run_id`. `runs/full-001/` and this report stay as they are. A task set bumped to
   v1.1.0 will break both existing spec locks, which is the intended behaviour.
3. The interesting open question this run generated is not about the phrase. It is whether
   condition D's consistent lead over the control is real. That is its own experiment with
   D as the treatment, not a reinterpretation of this one.
