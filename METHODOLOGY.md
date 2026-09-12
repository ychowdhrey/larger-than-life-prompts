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

## Independent variable

The experimental phrase.

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

The primary outcome is blinded preference between control and treatment outputs.

Secondary dimensions may include:

* task completion
* accuracy
* reasoning quality
* instruction adherence
* usefulness
* thoroughness
* checking behavior
* creativity where relevant

Each dimension is scored from 1 to 5 unless an experiment defines a more objective metric.

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

For an initial low cost experiment, 20 tasks with multiple repeated runs is acceptable. Stronger claims require larger samples and replication.

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

Each experiment should record:

* date
* model
* model version if exposed
* provider
* prompt condition
* phrase position
* settings
* task set
* number of runs
* judge model
* judge prompt version
* raw outputs or references to them
* aggregate results
* interpretation

## Book threshold

The working publication milestone is approximately 20 demonstrated effects, not merely 20 collected phrases.

Null and negative experiments still count as part of the evidence base and should inform the eventual synthesis.
