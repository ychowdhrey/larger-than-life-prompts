# Book Observations

Capture one concise observation after every completed experiment.

The purpose of this file is not to draft polished chapters. It is to preserve what each experiment taught while the result is still fresh.

## Experiment 001

**Full run, 2026-09-13. 240 generations. The phrase did nothing.**

Appending "May the Force be with you." to the end of a task prompt produced no measurable
improvement. On the preregistered primary outcome, blind judge task success, the task-level
paired difference against an empty control was **0.000**. Not small: zero to three decimal
places, from eight tasks whose differences cancelled. Against generic encouragement it was
-0.017. Against a plain instruction to be thorough it was -0.100, and every one of the five
tasks that discriminated at all moved against the phrase.

The objective score, computed with no judge involved, gave the same ordering: A 0.921,
B 0.914, C 0.920, D 0.953. Two independent instruments, one of them immune to length bias
and blind by construction, agree that the phrase is indistinguishable from appending
nothing.

The lesson is not "cinematic language is inert." It is narrower and more useful: **the
active ingredient in appended text is instruction content, not tone.** The only condition
that moved anything was D, the one that actually told the model what to do. D leads on
objective score, on task success, on thoroughness, on error checking, on depth, and it beats
the phrase in pairwise preference. It does not clear the preregistered bar either, and
`D_vs_A` was declared secondary in advance, so it is a direction to test rather than a
finding. But the ordering is the reverse of the premise: the plain instruction outperformed
the evocative one.

One number deserves recording because it is the opposite of the hypothesis. Verification
markers were **lowest** under the phrase (0.217 distinct markers per response) — lower than
the bare control (0.317) and lower than every other condition. These are crude regex counts
and mean little on their own, but nothing in the data points towards the phrase inducing
more checking, and this points mildly the other way.

The pilot's warning about a ceiling was half right, and the half it got wrong matters.
Measured on all 20 tasks: the judge measure *is* saturated (4.78-4.88 of 5; 12 to 15 of 20
tasks give a difference of exactly zero), but the objective score is *not* (mean 0.92, only
4 of 20 tasks perfect across all 12 runs). The null therefore rests on an instrument that
had room to move. Had the pilot's recommendation been followed — rebuild the task set before
running — the null would have been deferred on the strength of five tasks, and the finding
that the unsaturated measure agrees would never have been produced. A pilot is allowed to
flag a defect. It is not powered to cancel the experiment.

Where the ceiling does bite is `C_vs_D`. Its bootstrap interval excludes zero and its
direction is perfectly consistent, but only 5 of 20 tasks produced a non-zero difference,
and a sign-flip test on 5 values cannot return below 2/2^5 = 0.0625. The test was
arithmetically incapable of significance before the data arrived. That is worth remembering
as a design lesson: with a saturated measure, the effective n is not the number of tasks,
it is the number of tasks that discriminate.

Two method notes earned in this run:

1. **The preregistration paid for itself in the direction nobody plans for.** The lock is
   usually described as protection against talking yourself into an effect. Here it was
   protection against talking yourself out of running the experiment at all. The spec was
   fixed, the pilot's advice to redesign first was advice rather than authority, and the
   run produced a clean null on 240 generations instead of an indefinite postponement.

2. **A blinding leak can hurt the treatment.** Exactly one of 240 responses echoed its
   condition text: `P05-C-r1` ended with the phrase. The blind judge noticed and docked
   constraint adherence, and that response lost all three of its pairwise comparisons with
   the judge citing the out-of-place line. Leakage is normally modelled as a risk of
   flattering the treatment. It can equally penalise it, and the direction is not
   predictable in advance.

### Pilot, 2026-09-12 (retained: workflow validation only)

**Workflow validated; the phrase was not tested.**

The pilot's lesson is about instruments, not about the phrase.

Both outcome measures hit their ceiling. The objective score ran A 0.973 / B 0.960 /
C 1.000 / D 0.980, and the blind judge's task success ran A 4.60 / B 4.90 / C 5.00 /
D 5.00 out of 5. Three of five tasks scored a perfect 1.000 under every condition. A
measure that everything saturates cannot detect an effect of any size, so the honest
description of this pilot is that it had almost no room to show a difference, not that
it found none.

The direction was consistent even so: on every measure the ordering was A lowest, then
B, then C and D at or near the top. Consistent direction across a ceiling is weak
evidence and should not be quoted as a finding. It is worth one line in a notebook and
nothing more.

The most interesting number is the tie rate. In blind pairwise comparison the judge
could not separate the two responses in 14 of 30 comparisons. Against control the
phrase went 5-0 with 5 ties; against the explicit effort instruction it went 1-4. If
that survives a properly powered run it points somewhere specific: telling a model to
check its work may do what the phrase does, and do it more reliably.

Two lessons for the method, both about task design rather than about phrasing:

1. **Tasks calibrated to be answerable are useless here.** The interesting question is
   whether appended text helps at the margin, and there is no margin when a capable
   model solves everything. Task difficulty has to be tuned until the control condition
   fails a meaningful fraction of the time. A task set is an instrument and needs
   calibrating like one.

2. **An ordering check that matches the first occurrence anywhere in the text is not
   an ordering check.** The migration task penalised three correct plans because the
   word "cutover" appeared in a passing mention before the backup step. The artifact
   happened to flatter the treatment condition, which is the direction that would have
   been easiest to miss and most tempting to keep.

Neither defect was repaired in place. The spec was locked before the run and the
results exist, so both are recorded for a future task set version. That constraint cost
nothing here and is the only reason the two defects are legible as defects rather than
as results.
