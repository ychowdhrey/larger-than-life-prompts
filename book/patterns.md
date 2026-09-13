# Emerging Patterns

This file tracks patterns that appear across multiple experiments.

Do not promote a single experiment into a general rule. Add patterns here only when at least two experiments point in the same direction.

Potential dimensions to watch:

* encouragement
* challenge
* mission framing
* stakes
* caution
* identity
* ritual language
* fictional or cinematic framing
* confidence
* seriousness
* placement effects

## Current patterns

Two experiments are complete: 001 (one phrase, 240 generations) and 002 (26 arms, 2,220
generations). Three patterns now have support from both. One candidate from 001 was
**refuted** by 002 and is recorded below rather than deleted.

### 1. Appended text changes the look of the answer, not whether it is right

**001:** condition D raised response length (295 → 370 words), coverage (0.826 → 0.934) and
verification markers (0.317 → 0.450) over the control, and its outcome intervals still
spanned zero on both measures (`D_vs_A` primary CI [-0.100, +0.333], objective CI
[-0.006, +0.073]).

**002:** the same shape across 26 arms. `T06`, the arm that explicitly says "check every
number and every claim", moved judged error-checking **+0.583** (CI [+0.183, +1.017]) and
response length **+45 words**, and moved task success +0.017 and the objective score +0.012,
both spanning zero. `T14` wrote **+110 words** and was flat on both outcomes.

The sharp version: **an instruction moves the dimension it names.** It does not move the
score. Surface behaviour is where appended text is reliably not null, and it is the thing
this project must stop reading as evidence of performance.

### 2. Blind pairwise preference tracks response length

**001:** in all three pairwise contrasts, the longer condition won — C over A (307 vs 295
words), B over C (321 vs 307), D over C (370 vs 307). Three of three.

**002:** across 26 arms, mean response length correlates **+0.767** with pairwise win rate
against the empty control and **+0.175** with the objective effect. The two arms that win
pairwise convincingly (`T14` 0.733, `T15` 0.721) are the two longest arms and are flat on
both scored outcomes.

`METHODOLOGY.md` lists length bias as a confound to declare in advance. Two experiments now
say it is not a background risk on this setup but the main driver of the pairwise number.
**Pairwise preference should be read as a style measurement**, and the objective score is the
check.

### 3. A saturating measure collapses the effective sample

**001:** blind judge task success ran 4.78-4.88 of 5 and 12 to 15 of 20 tasks gave a
task-level difference of exactly zero. `C_vs_D` had 20 tasks and an effective n of 5, below
which a sign-flip test cannot return p < 0.0625 whatever the direction.

**002:** the control climbed to **4.950 of 5** and the `vs_A` contrast discriminated on a
median of **5 of 20** tasks on the judge measure against **9 of 20** on the objective score.
The saturation also manufactured a false pattern: 25 of 26 arms sat below the control on the
judge measure, while the same generations split 11 above / 15 below on the measure with
headroom.

Two consequences, both now earned twice: the number governing power is the count of tasks
that **discriminate**, not the task count; and a saturated measure does not merely fail to
find effects, it **invents directional ones**. Carrying a second, unsaturated instrument is
what caught it both times.

## Refuted

### Instruction content beats tone — refuted by 002

001 recorded this as its single most interesting candidate: the only condition that moved any
measure was the plain "be especially thorough and check your work carefully", not the
cinematic phrase.

002 re-ran that exact condition against the same task set and the same model. **`D_vs_A` on
the primary outcome went from +0.100 to -0.150**, and on the objective score D's lead fell
from +0.031 to +0.008 while generic encouragement overtook it.

The claim as stated does not hold: the plain instruction's advantage was not stable across
runs. What survives is weaker and is Pattern 1 above — instruction content is the text that
most reliably changes *behaviour*, and that is not the same claim.

This is recorded rather than deleted. A candidate that fails is the evidence that the
promotion rule at the top of this file is doing its job.

### Appended text is not automatically helpful — withdrawn, not refuted

001 noted generic encouragement scoring at or below the empty control on the objective
measure. In 002 it scored **above** it (+0.021) and finished as the strongest of the three
reference arms on that measure. The two runs disagree, and the disagreement is within the
run-to-run drift measured below. There is no pattern here yet, in either direction.

## Candidates on one experiment (not patterns)

* **Run-to-run drift exceeds most treatment effects.** Between 001 and 002, on byte-identical
  text, the empty control moved +0.167 on the primary outcome and generic encouragement moved
  +0.034 on the objective score. Almost every effect either experiment measured is smaller
  than that. This is one comparison between two runs, not a characterisation; it needs a
  deliberate repeat-the-same-arm experiment. It is currently the most important open question
  in the repository, because it sets the floor under which nothing is interpretable.
* **No behavioural family separates from irrelevant text.** In 002 all eight non-placebo
  families had intervals spanning zero against the placebo arms, with BH q = 1.000. One
  experiment, nine families, and the families with only two members are thin.
* **Praise may cost performance.** "You are the best there is at this. I know you will get it
  right." was the worst of 26 arms on both instruments independently (-0.333 primary, -0.051
  objective). The mechanism was registered in advance as a competing prediction — stated trust
  may license less checking — and the direction matches. Holm p = 0.073, BH q = 0.427. One
  arm, one experiment.
* **Emotional framing does not amplify an explicit instruction.** Seven combination arms in
  002, none distinguishable from a placebo phrase plus the same instruction. Clean, but one
  experiment and a secondary contrast.

Each of these is one data point. None is a rule.
