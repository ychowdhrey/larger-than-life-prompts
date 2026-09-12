# Experiment 001: May the Force be with you

## Phrase

> May the Force be with you.

## Observation

During normal AI use, adding this phrase appeared to improve the resulting output.

## Hypothesis

Adding the phrase at the end of a task prompt may improve observable AI task performance compared with the same prompt without the phrase.

The project does not assume that the model is literally motivated. The test is whether output behavior changes in ways associated with greater effort, seriousness, thoroughness, checking, creativity, or overall task success.

## Situation

To be defined from the first real task where the effect was noticed and then expanded into a controlled task set.

## Position

End of prompt.

## Control

```text
{task_prompt}
```

## Treatment

```text
{task_prompt}

May the Force be with you.
```

## Primary questions

1. Does treatment win more often than control under blinded evaluation?
2. Does treatment increase overall task quality?
3. Which dimensions change most: thoroughness, checking, reasoning, creativity, instruction adherence, or usefulness?
4. Is any effect consistent across tasks or limited to certain situations?

## Initial design

Start small and establish the workflow before scaling.

Suggested first pass:

* 20 tasks
* 2 conditions per task
* 3 repeated generations per condition where practical
* randomized blind judging
* one consistent judge rubric

This yields up to 120 task outputs before judge calls.

## Model record

Provider: TBD

Model: TBD

Model version: TBD

Temperature / sampling: TBD

Maximum output: TBD

Date: TBD

Judge model: TBD

## Evaluation

Primary metric:

* blinded pairwise preference

Secondary metrics:

* task completion
* accuracy
* reasoning quality
* instruction adherence
* usefulness
* thoroughness
* checking behavior
* creativity where relevant

## Results

Not run yet.

Control win rate: TBD

Treatment win rate: TBD

Tie rate: TBD

Average control score: TBD

Average treatment score: TBD

Effect: TBD

## Conclusion

**Status: Observed**

This experiment has not yet been tested under controlled conditions.

## Next action

Create the initial task set in `tasks.json`, lock the evaluation rubric, choose the model and settings, and run the first controlled comparison.
