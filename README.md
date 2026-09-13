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
├── SUMMARY.md                    state of the evidence across every experiment
├── results.csv                   cross-phrase leaderboard, generated
├── tasks/
│   └── core-v1.json              the shared task set every phrase is measured on
├── experiments/
│   ├── 001-may-the-force-be-with-you/
│   │   ├── README.md
│   │   ├── PREREGISTRATION.md    hypotheses and decision rule, locked before any run
│   │   ├── conditions.json       the four conditions
│   │   ├── tasks.json            20 tasks with objective scoring
│   │   ├── config/               pilot and full run configurations
│   │   ├── runs/                 immutable raw outputs, one directory per run
│   │   ├── results.csv
│   │   └── analysis.md
│   └── 002-phrase-battery/
│       ├── README.md
│       ├── PREREGISTRATION.md    locked before any generation existed
│       ├── phrases.json          26 treatment arms, each with family and hypothesis
│       ├── conditions.json       generated from phrases.json, never hand-edited
│       ├── config/               mock, pilot and full run configurations
│       ├── runs/
│       ├── results.csv, phrase_results.csv, family_results.csv
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

| ID | Phrase(s) | Families | Generations | Impact | Confidence | Eval |
|---|---|---:|---:|---|---|---|
| 001 | May the Force be with you | 1 | 240 | Neutral | Observed | [Experiment 001](experiments/001-may-the-force-be-with-you/) |
| 002 | 25 phrases, 26 arms | 9 | 2,220 | Neutral on all 26 | Observed | [Experiment 002](experiments/002-phrase-battery/) |

**Both experiments are complete and both are nulls.** 26 phrases, 2,460 generations, nine
behavioural families, zero demonstrated effects on task performance in either direction.

Experiment 001 tested one phrase and found nothing. It closed with a candidate it could not
promote on one run: *the active ingredient in appended text is instruction content, not
tone.* Experiment 002 re-ran that condition verbatim alongside 25 new phrases and **the
candidate reversed** — the plain instruction beat the empty control by +0.100 in 001 and lost
to it by -0.150 in 002, on identical text.

What the battery did find is not about any phrase:

* **Appended text changes the look of the answer, not whether it is right.** The one arm that
  says "check every number and every claim" moved judged error-checking by **+0.583** and the
  objective score by **+0.012**.
* **Blind pairwise preference tracks length.** Across 26 arms, response length correlates
  **+0.767** with pairwise win rate and **+0.175** with the objective effect.
* **No behavioural family separates from irrelevant filler.** All eight non-placebo families
  have intervals spanning zero against a placebo arm that talks about the weather.
* **The noise floor is larger than the effects.** On byte-identical text the empty control
  moved +0.167 between runs — bigger than almost every treatment effect measured.

Full synthesis in [SUMMARY.md](SUMMARY.md). Per-phrase index in [PHRASES.csv](PHRASES.csv),
cross-phrase leaderboard in [results.csv](results.csv).

## Running an experiment

```bash
# a single phrase, four conditions
python3 scripts/experiment.py all --config experiments/001-may-the-force-be-with-you/config/full.json --workers 6

# a battery: many phrases against shared controls
python3 scripts/experiment.py all --config experiments/002-phrase-battery/config/full.json --workers 16
```

Resumable, standard library only. Raw outputs are immutable with a sha256 ledger checked in
both directions, and the experiment's spec — tasks, conditions, phrase registry, rubric, both
judge prompts and the preregistration — is hashed and locked so none of it can change once
results exist. See [scripts/README.md](scripts/README.md).

## Long term goal

Run one controlled experiment whenever an interesting phrase appears during real AI use.

When the project reaches roughly 20 demonstrated effects, synthesize the findings into a book about how larger than life language changes AI behavior, where the effects appear, where they fail, and what that teaches us about prompting.

After two experiments the count of demonstrated effects is **zero**, and the useful findings
so far are about measurement rather than about phrases. That is a real result and it stays.
The binding constraint is now the task set: the control condition scores 4.95 of 5 on the
primary outcome and the measure discriminates on a median of 5 of 20 tasks, so the next step
is a harder task set rather than more phrases.

The repository is the lab notebook. The experiments are the evidence. The book will be the synthesis.
