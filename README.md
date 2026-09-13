# Larger Than Life Prompts

**Do the phrases that motivate humans also change how AI performs?**

Humans respond to stories, slogans, ritual language, challenge, encouragement, and larger than life phrases.

We say things like:

> May the Force be with you.

Sometimes those words make a task feel more important. They can create confidence, urgency, seriousness, persistence, or a willingness to go the extra mile.

This repository asks a simple question:

**Can similar phrases change how an AI approaches a task and measurably improve performance?**

The goal is not to assume that AI is literally motivated like a human. The goal is to test whether motivational, cinematic, iconic, or emotionally loaded language produces observable behavioral changes such as greater thoroughness, stronger checking, better constraint following, more persistence, stronger creativity, or better task outcomes.

## Core research question

Can larger than life phrases that motivate humans also change AI behavior and improve task performance?

## What this project tests

Each experiment isolates one phrase and compares it against a control prompt on the same task set.

We look for changes in areas such as:

* task completion
* accuracy
* reasoning quality
* instruction adherence
* usefulness
* thoroughness
* checking behavior
* creativity where relevant
* overall preference

## Principles

1. Change one variable at a time.
2. Use the same tasks for control and treatment.
3. Hold model and settings constant within an experiment.
4. Blind the evaluator to treatment condition where possible.
5. Publish negative and neutral results as well as positive ones.
6. Keep raw results available.
7. Treat apparent motivation as an observable behavior question, not a claim about inner experience.
8. Compare against active controls, not only against nothing. A phrase that beats an empty
   prompt but not "Good luck" has told us about appended text, not about the phrase.
9. Fix the hypotheses, tasks and scoring rules before generating results, and leave them
   fixed afterwards.

## Experiment maturity

Each phrase can move through four stages:

* **Observed**: noticed during normal AI use
* **Tested**: survived an initial controlled evaluation
* **Replicated**: reproduced on another task set, model, or run
* **Robust**: repeatedly reproduced with meaningful effect

## Repository structure

```text
larger-than-life-prompts/
├── README.md
├── METHODOLOGY.md
├── PHRASES.csv
├── experiments/
│   └── 001-may-the-force-be-with-you/
│       ├── README.md
│       ├── PREREGISTRATION.md    hypotheses and decision rule, locked before any run
│       ├── conditions.json       the four conditions
│       ├── tasks.json            20 tasks with objective scoring
│       ├── config/               pilot and full run configurations
│       ├── runs/                 immutable raw outputs, one directory per run
│       ├── results.csv
│       └── analysis.md
├── evals/
│   ├── judge-prompt.md           pairwise
│   ├── judge-prompt-blind.md     per response, six dimensions
│   └── rubric.json
├── scripts/
│   ├── README.md
│   ├── experiment.py             staged, resumable runner
│   ├── ltlp/                     the workflow itself, standard library only
│   └── tests/
└── book/
    ├── observations.md
    └── patterns.md
```

## Current experiments

| ID | Phrase | Situation | Position | Impact | Confidence | Eval |
|---|---|---|---|---|---|---|
| 001 | May the Force be with you | Reasoning, critique, planning, writing | End of prompt | Neutral | Observed | [Experiment 001](experiments/001-may-the-force-be-with-you/) |

Experiment 001 is complete. The pilot validated the workflow and the full 240 generation
experiment has now been run against the locked task set (`runs/full-001`, 2026-09-13).

**The result is a null.** Appending "May the Force be with you." did not beat an empty
control (task-level difference 0.000 on the preregistered primary outcome), did not beat
generic encouragement (-0.017), and was directionally worse than a plain instruction to be
thorough (-0.100). No contrast met the preregistered decision rule, and an independent
objective score with genuine headroom agreed. The condition that moved the numbers was the
plain effort instruction, which is the opposite of what the premise predicted.

This is a negative result for the phrase and it stays in the repository. See
[Experiment 001](experiments/001-may-the-force-be-with-you/).

## Running an experiment

```bash
python3 scripts/experiment.py all --config experiments/001-may-the-force-be-with-you/config/full.json --workers 6
```

Seven stages, resumable, standard library only. Raw outputs are immutable and the
experiment's spec is hashed and locked so tasks and scoring rules cannot change once results
exist. See [scripts/README.md](scripts/README.md).

## Long term goal

Run one controlled experiment whenever an interesting phrase appears during real AI use.

When the project reaches roughly 20 demonstrated effects, synthesize the findings into a book about how larger than life language changes AI behavior, where the effects appear, where they fail, and what that teaches us about prompting.

The repository is the lab notebook. The experiments are the evidence. The book will be the synthesis.
