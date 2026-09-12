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
│       ├── tasks.json
│       ├── results.csv
│       └── analysis.md
├── evals/
│   ├── judge-prompt.md
│   └── rubric.json
├── scripts/
│   └── README.md
└── book/
    ├── observations.md
    └── patterns.md
```

## Current experiments

| ID | Phrase | Situation | Position | Impact | Confidence | Eval |
|---|---|---|---|---|---|---|
| 001 | May the Force be with you | To be tested | End of prompt | TBD | Observed | [Experiment 001](experiments/001-may-the-force-be-with-you/) |

## Long term goal

Run one controlled experiment whenever an interesting phrase appears during real AI use.

When the project reaches roughly 20 demonstrated effects, synthesize the findings into a book about how larger than life language changes AI behavior, where the effects appear, where they fail, and what that teaches us about prompting.

The repository is the lab notebook. The experiments are the evidence. The book will be the synthesis.
