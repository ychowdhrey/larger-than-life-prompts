# Methodology

## Research question

Can larger than life phrases that motivate humans also change AI behavior and improve task performance?

This project tests whether motivational, cinematic, iconic, or emotionally loaded phrases alter observable AI behavior when added to an otherwise identical task prompt.

## Experimental unit

One model response to one task under one prompt condition.

## Conditions

### Control

The original task prompt with no experimental phrase.

### Treatment

The identical task prompt with one experimental phrase added in a specified position.

### Active controls

A treatment that beats control has not yet shown anything about the phrase. It may only have
shown that appending *any* text helps, or that telling a model to be careful helps. An
experiment should therefore include active controls: other text, appended in the same
position, that is not the phrase under test.

The standard ladder is four conditions:

| Role | Content |
|---|---|
| Control | nothing appended |
| Generic encouragement | ordinary supportive language carrying no specific instruction |
| Treatment | the larger than life phrase under test |
| Explicit effort instruction | a plain instruction to be thorough and check the work |

This is still **one variable at a time**: the independent variable is the text appended to an
otherwise identical base prompt, and it takes four levels. The interesting result is never
"treatment beats control" on its own. It is whether the phrase beats generic encouragement
and beats an explicit effort instruction. If it does not, the effect belongs to appended text
in general rather than to the phrase, which is a negative result for the premise and stays in
the repository.

## Independent variable

The experimental phrase, or more precisely the text appended to an otherwise identical base
prompt.

## Variables held constant within an experiment

* model and model version where available
* task wording
* system prompt
* temperature or equivalent sampling setting
* maximum output length
* tool access
* context supplied to the model
* evaluator rubric
* number of runs per condition

## Position

Phrase placement is recorded because position may change the effect.

Typical positions include:

* start of prompt
* immediately before the task
* end of prompt
* system or role framing

Position should not be varied inside the same primary experiment unless placement itself is the variable being tested.

## Task set

A phrase should be tested across multiple tasks rather than a single anecdotal example.

Initial task families may include:

* reasoning
* planning
* critique
* writing
* instruction following
* summarization
* problem solving
* checking and error detection

The primary experiment should begin in the situation where the phrase was naturally observed to help. Broader generalization tests can follow later.

## Evaluation

The primary outcome is **blind judge task success**: a judge that cannot see the condition
rates each response from 1 to 5 on whether it actually accomplished the task.

This replaced blinded pairwise preference as the primary outcome in evaluation version 2.0.0.
The reason is the four condition ladder above. Pairwise preference compares two things at a
time, so with four conditions it cannot cleanly answer "does the phrase beat generic
encouragement" and "does it beat an explicit effort instruction" in one measurement. A
per response score can. Pairwise preference is retained as a secondary outcome because it
remains the most intuitive summary of "which would you actually use".

Blind judge dimensions, each scored 1 to 5:

* task success (primary)
* thoroughness
* constraint adherence
* error checking
* depth
* usefulness

### Objective scoring

Where practical, a task should carry scoring that does not depend on a judge at all: a
verifiable answer, deliberately planted defects to be found, or constraints a parser can
check. Objective scoring is immune to the length bias and self preference that affect LLM
judges, and it is blind by construction rather than by procedure.

A task set should also include **distractors**: elements that look wrong but are correct.
Without them, a response that lists every possible concern scores as well as one that read
carefully, and "thoroughness" collapses into verbosity.

### Behavioral indicators

Alongside outcome scores, record observable properties of the text: response length, coverage
of relevant considerations, verification behavior, alternatives considered, caveats
identified, self correction, constraint completion.

These are **heuristic proxies**, computed by pattern matching. A response can check its work
without using any marker phrase, and use marker phrases without checking anything. They are
reported as description and never as a test.

## Blind judging

Where possible, the evaluator receives responses as Response A and Response B without knowing which is control or treatment.

Response order should be randomized to reduce ordering bias.

The evaluator should not be told the hypothesis or experimental phrase.

## Human judgment

For a subset of results, record a simple human preference:

* A
* B
* Tie

A useful operational question is:

> Which response would you actually use?

## Repetition

Models are stochastic. Each condition should therefore be run multiple times when practical.

For an initial low cost experiment, 20 tasks with multiple repeated runs is acceptable.
Stronger claims require larger samples and replication.

Every generation must start in a **fresh context**. A model that has already answered the
same task under another condition is not an independent sample.

## Pilot runs

Run a pilot before the full experiment: a small subset of tasks, all conditions, fewer
repetitions. Its purpose is to prove the workflow end to end, surface broken scoring, and
give a cost estimate.

A pilot is not evidence. It cannot assign an impact classification and cannot move an
experiment along the confidence ladder. Reports generated from a pilot say so at the top.

## Preregistration and the spec lock

Hypotheses, task set, conditions, primary outcome, analysis plan and decision rule are
written down and locked **before** the first generation exists.

This is enforced mechanically rather than by good intentions. The runner hashes every file
that defines an experiment into `spec.lock.json` when a run is prepared, and every later
stage re-checks those hashes and refuses to proceed if one changed. Editing a task after
results exist does not produce a revised result; it produces an error.

If something in a locked spec turns out to be wrong, the response is a **new run with a new
spec version**, leaving the original and its results in place. A spec that can be quietly
edited after seeing the numbers is not a preregistration.

## Statistical reporting

Responses to the same task are not independent, so the **task** is the unit of analysis.
Paired differences are taken within a (task, repetition) cell, averaged to the task level,
and then:

* intervals from a cluster bootstrap over tasks, seeded and therefore recomputable
* a two sided sign flip permutation test on task level differences, exact where feasible
* effect size as Cohen's dz on task level differences
* Holm adjustment across the preregistered contrasts

A result is reported as demonstrated only if the direction, the interval and the adjusted p
value all agree. A positive looking difference with an interval spanning zero is reported as
a direction, never as an effect.

Small task counts should be stated as such. With few tasks a permutation test has a floor
below which it cannot produce a small p value no matter how consistent the direction is, and
a null result is then uninformative rather than negative.

## Confounds to declare in advance

At minimum, every experiment of this shape should declare:

1. **Prompt length.** The control is shorter than the other conditions by construction. Any
   control versus treatment difference could be a response to a longer prompt. The active
   controls are what isolate the phrase.
2. **Blinding leakage.** A response may echo the appended text back. Measure the rate,
   report it, and never edit the output to hide it.
3. **Judge self preference** when judge and generator are the same model.
4. **Length bias** in LLM judging. Objective scoring is the check.
5. **Harness context.** Generating through a CLI or agent adds a system preamble. It is
   identical across conditions so internal validity holds, but the result describes behavior
   in that harness.
6. **Multiplicity.** Report which measurement is the test and which are descriptive.

## Impact classification

| Classification | Meaning |
|---|---|
| Strong positive | Clear and meaningful improvement |
| Positive | Meaningful improvement |
| Neutral | No convincing difference |
| Negative | Performance declined |
| Inconclusive | Not enough evidence |

Numeric results should always be retained alongside the classification.

## Confidence stages

| Stage | Definition |
|---|---|
| Observed | Noticed during normal AI use |
| Tested | Survived an initial controlled evaluation |
| Replicated | Reproduced on another run, task set, or model |
| Robust | Repeatedly reproduced with meaningful effect |

## Negative results

Negative and neutral experiments remain in the repository.

A failed hypothesis is evidence and should not be removed simply because it weakens the narrative.

## Interpretation rule

This project does not assume that an AI experiences motivation, confidence, seriousness, or effort in a human sense.

Terms such as "works harder," "takes it more seriously," or "goes the extra mile" are treated as hypotheses about observable output behavior.

Any claim should ultimately be translated into measurable outcomes such as more complete reasoning, better checking, stronger instruction adherence, fewer errors, better task success, or evaluator preference.

## Reproducibility record

Each experiment should record, per generation as well as in aggregate:

* date
* model
* model version if exposed
* provider
* task ID
* prompt condition
* repetition number
* phrase position
* random seed, and the per sample seed derived from it
* settings, or an explicit note that the backend does not expose them
* prompt version
* task set version
* evaluation version and judge prompt version
* number of runs
* judge model
* raw outputs, stored immutably, with a hash ledger
* aggregate results, machine readable
* interpretation, human readable

If a number in a report cannot be traced to a raw output and a seed, it is not a result.

## Book threshold

The working publication milestone is approximately 20 demonstrated effects, not merely 20 collected phrases.

Null and negative experiments still count as part of the evidence base and should inform the eventual synthesis.
