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

See `runs/<run_id>/run_meta.json` for the authoritative record of any run.

Provider: Anthropic, via the `claude` CLI (one process per generation)

Model: `claude-sonnet-5`

Judge model: `claude-sonnet-5`

Temperature / sampling: not exposed by the CLI backend, recorded as such

Task set version: 1.0.0 · Rubric version: 2.0.0 · Prompt version: 1.0.0 · Workflow version: 1.0.0

## Results

Pilot: see [analysis.md](analysis.md) and `runs/pilot-001/`.

The full 240 generation experiment has **not** been run.

## Conclusion

**Status: Observed**

A pilot validates the workflow and cannot move the confidence stage. Promotion to **Tested**
requires the full run.

## Next action

Run `config/full.json`, then update `PHRASES.csv`, this section, and
`book/observations.md` from the generated analysis.
