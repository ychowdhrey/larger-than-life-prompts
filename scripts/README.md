# Scripts

A dependency-free, resumable evaluation workflow for the experiments in this repository.

## Why this exists now

Version 1 of this file said:

> Do not overbuild before Experiment 001 is run end to end manually or with a minimal script.

That caution was right and is worth keeping in mind. It was superseded deliberately, because
Experiment 001 as specified needs 240 independent generations across four conditions, each in
a fresh context, with blinding, randomisation and resumability. That cannot be done by hand
without the record-keeping errors the caution was meant to prevent.

The caution is honoured in the shape of the tooling rather than its absence:

* **Standard library only.** No dependencies, no framework, no build step. A result should be
  reproducible on any machine with Python 3.9+ and nothing installed.
* **Plain files.** JSON and CSV on disk. No database, no cache, no server.
* **Readable.** Each stage is one module, and the module that carries the validity claim
  (`ltlp/prompts.py`) is under 100 lines.

## Usage

```bash
# one stage at a time
python3 scripts/experiment.py prepare --config experiments/001-may-the-force-be-with-you/config/pilot.json
python3 scripts/experiment.py generate --config .../pilot.json --workers 4
python3 scripts/experiment.py score-objective --config .../pilot.json
python3 scripts/experiment.py judge-blind --config .../pilot.json --workers 4
python3 scripts/experiment.py judge-pairwise --config .../pilot.json --workers 4
python3 scripts/experiment.py analyze --config .../pilot.json
python3 scripts/experiment.py report --config .../pilot.json

# or all seven in order
python3 scripts/experiment.py all --config .../pilot.json --workers 4

# how far along is a run, and is its data intact
python3 scripts/experiment.py status --config .../pilot.json
python3 scripts/experiment.py verify --config .../pilot.json
```

`--limit N` stops after N new units, which is the cautious way to make a first pass.

## Stages

| Stage | Does | Model calls |
|---|---|---|
| `prepare` | builds the randomised manifest, the pairwise slots and the spec lock | none |
| `generate` | one fresh model context per sample | 1 per generation |
| `score-objective` | deterministic checks and behavioural indicators | none |
| `judge-blind` | six dimensions per response, condition never shown | 1 per generation |
| `judge-pairwise` | head to head, A/B order fixed at prepare time | 1 per comparison |
| `analyze` | joins everything, computes contrasts and uncertainty | none |
| `report` | renders `analysis.md` from `summary.json` | none |

## Guarantees

**Resumable.** Every unit of work has a deterministic id and one output file. A unit whose
output exists is skipped. Interrupt any stage and re-run it: nothing already produced is
regenerated, and a partially judged run costs only its remainder.

**Raw outputs are immutable.** Generations and judgments are written through a write-once
function that refuses to touch an existing file. Failures are recorded under
`state/failures/`, never in `raw/`, so a retry cannot overwrite a completed sample.
`raw/INDEX.jsonl` holds a sha256 per file and `verify` re-checks it.

**The spec is locked.** `prepare` hashes tasks, conditions, rubric, both judge prompts and
the preregistration into `spec.lock.json`. Every later stage re-checks those hashes and
**refuses to run** if one moved. This is how the rule "do not change hypotheses, tasks,
scoring rules or conditions after results have been generated" is enforced rather than
merely promised. To change the design, start a new `run_id` with a new spec version.

**The judge is blind.** It receives the base task and a response under an opaque HMAC item
id. It never receives the condition, the sample id, or the condition-augmented prompt —
passing the rendered prompt would print the treatment phrase straight into the judge's
context, so `build_blind_judge_prompt` takes the base prompt and no code path passes
anything else. Responses that echo their condition's text back are flagged, counted and
reported as a confound; they are never edited.

**Randomisation is seeded and pre-registered.** Execution order and the A/B presentation
slots are drawn from one recorded master seed before generation starts, so anyone can
recompute them.

## Backends

| Backend | Use | Notes |
|---|---|---|
| `claude_cli` | default | one OS process per generation, so the context is genuinely fresh. No API key needed. Exposes no temperature or seed flag, which is recorded honestly rather than papered over. |
| `anthropic_api` | exact sampling control | needs `ANTHROPIC_API_KEY` |
| `mock` | testing the pipeline | deterministic, offline, tagged `backend: "mock"` so it can never be mistaken for data |

## Tests

```bash
cd scripts && python3 -m unittest discover -s tests -t . -q
```

71 tests, no network, a few seconds. They cover the claims that matter: prompts differ only
by the suffix, no condition text can reach a judge, every objective scorer awards full marks
to a correct response and withholds them from a violating one, all reasoning answers
recomputed from first principles, statistics checked against closed forms, and an end-to-end
mock run proving resumability, write-once immutability and spec-lock enforcement.

## Layout

```text
scripts/
├── experiment.py        CLI entry point
├── ltlp/
│   ├── config.py        config loading and the spec lock
│   ├── manifest.py      seeded randomisation: samples, pairs, blind ids
│   ├── prompts.py       prompt assembly and judge payloads (the validity claim)
│   ├── backends.py      claude_cli / anthropic_api / mock
│   ├── runner.py        the shared resumable work loop
│   ├── generate.py      stage: generate
│   ├── objective.py     deterministic check evaluators
│   ├── score_objective.py  stage: objective scoring
│   ├── indicators.py    behavioural proxies (heuristic, labelled as such)
│   ├── judge.py         stages: blind and pairwise judging
│   ├── stats.py         bootstrap, permutation, binomial, Wilson, Holm
│   ├── analyze.py       stage: analyse
│   ├── report.py        stage: report
│   └── util.py          hashing, atomic and write-once IO
└── tests/
```
