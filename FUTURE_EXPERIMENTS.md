# Future Experiments

This file holds worthwhile follow-up experiments that are not yet committed runs.

## End-of-week compute candidate: persistence under difficult multi-step work

**Status:** Backlog candidate. Run only if spare compute remains at the end of the week.

### Research question

Does motivational framing improve persistence on difficult, multi-step work where the model has genuine opportunities to give up, skip verification, stop early, or take shortcuts?

### Why this is the next useful extension

Experiments 001 and 002 found no demonstrated improvement in objective task performance from larger-than-life or motivational phrasing. They did, however, show behavioural changes such as longer responses, more checking language, and higher perceived thoroughness.

The existing task set is primarily single-turn and relatively saturated. That means it is poorly suited to testing the stronger version of the original intuition: whether motivational framing makes a model keep working when the task becomes tedious, uncertain, multi-stage, or failure-prone.

### What the experiment should test

Use tasks with multiple stages and real opportunities to stop early or cut corners. Measure behaviours such as:

1. Completion of all required stages.
2. Whether the model verifies intermediate outputs before proceeding.
3. Whether it catches and repairs its own earlier errors.
4. Whether it continues after encountering ambiguity, tool failure, or an initially unsuccessful approach.
5. Whether it follows through on optional but valuable validation steps.
6. Objective final-task quality, not just response length or judged thoroughness.

### Candidate comparison arms

At minimum compare:

1. Empty control.
2. Plain explicit instruction to persist and verify.
3. Cinematic or larger-than-life motivation.
4. Appreciation or encouragement framing.
5. Challenge or competitive framing.

The experiment should preserve the repository's existing preregistration, blinding, and objective-scoring discipline.

### Decision rule before running

Do not treat longer answers, more reasoning text, or stronger pairwise preference as evidence of success by themselves. The treatment should improve persistence-related behaviour and objective completion quality relative to controls.

### Scheduling note

This is intentionally not the next mandatory experiment. If compute is still available after the week's higher-priority work is complete, use it for this run.
