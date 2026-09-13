# Summary

*State of the evidence as of 2026-09-13. Regenerate the numbers from
`experiments/*/runs/*/analysis/` and the indexes with `python3 scripts/build_indexes.py`.*

---

## Where the project stands

| | |
|---|---:|
| **Phrases tested** | **26** (25 distinct, one run twice as a replication) |
| Behavioural families covered | 9 |
| **Total generations** | **2,460** |
| Blind judgments | 2,460 |
| Pairwise comparisons | 1,740 |
| Experiments complete | 2 |
| **Phrases with a demonstrated positive effect** | **0** |
| Phrases with a demonstrated negative effect | 0 |
| Phrases classified Neutral | 26 |

Every phrase was measured on the same 20-task set, at the end of the prompt, on
`claude-sonnet-5`, against an empty control, generic encouragement, and a plain instruction
to be thorough. Every hypothesis, contrast, threshold and decision rule was locked before any
result existed.

---

## Answers to the questions this project asks

**Overall strongest phrase.** None. No phrase met the preregistered decision rule on the
primary outcome in either experiment. The nominal top of the leaderboard is
`T06` — *"Check every number and every claim before you finish."* — at **+0.017** on blind
judge task success and **+0.012** on the objective score against an empty control, both
intervals spanning zero. It is the strongest arm in the battery and it is not an effect.

**Strongest category.** None separates from irrelevant text. Ranked on the objective score
against the empty control, **Cinematic motivation** is nominally first (+0.008,
CI [-0.008, +0.026]) and **Challenge / competition** second (+0.007, CI [-0.020, +0.036]).
Compared against the placebo arms rather than against nothing — which is the comparison the
preregistration named as the falsification criterion — **all eight non-placebo families have
intervals spanning zero and BH q = 1.000**.

**Weakest category.** **Trust / confidence** (F4): -0.014 on the objective score and -0.228 on
the primary outcome against the empty control, last of nine on both. It also contains the
single worst arm in the battery.

**Largest negative effect.** `T11` — *"You are the best there is at this. I know you will get
it right."* — **-0.333** on blind judge task success and **-0.051** on the objective score
against an empty control: worst of 26 arms on two independent instruments. The
preregistration recorded the mechanism in advance as a competing prediction for this family:
stated trust may license *less* checking, because the work is pre-approved. The direction
matches. The evidence does not clear the bar (Holm p = 0.073, BH q = 0.427), so it is a
direction to test, not a finding.

**Most surprising result.** Not a phrase. **Experiment 001's own candidate pattern did not
replicate, and reversed.** The plain instruction "Be especially thorough and check your work
carefully" beat the empty control by **+0.100** on the primary outcome in Experiment 001 and
**lost to it by -0.150** in Experiment 002. Identical text, identical task set, identical
model, opposite signs. The battery only caught it because it re-ran the same control arms
alongside 26 new phrases.

The runner-up is quieter and more useful: across the 26 arms, mean response length correlates
**+0.767** with blind pairwise preference and **+0.175** with the objective effect. A phrase
buys preference by making the answer longer, not better.

**Current evidence for the overall hypothesis.** Against it, on 2,460 generations. The
premise is that larger-than-life language changes AI behaviour and improves task performance.
Behaviour: yes, measurably. Performance: no, not once, in nine families, across two
instruments, one of which never sees a judge.

---

## Do larger than life phrases make AI work harder or perform better?

**On this evidence: they change how the work looks, and not whether it is right.**

Appending a phrase reliably produces a longer answer, more checking language, and a higher
rating on judged thoroughness. It does not produce more correct answers, better constraint
adherence, or higher scores on a task set that contains planted defects to find. Telling the
model to check its work moved judged error-checking by **+0.583** (CI [+0.183, +1.017]) and
moved the objective score by **+0.012** (CI [-0.017, +0.043]).

Nothing here says the phrases are inert. They are not. They are inert *on the outcome*.

### The five effects, separated

| Effect | Verdict on this evidence |
|---|---|
| **Emotional effect** | **Not demonstrated.** Appreciation, trust and social framing are indistinguishable from a sentence about the weather on both outcomes. Trust/confidence is the weakest family of the nine, and the worst single arm in the battery is superlative praise. |
| **Instruction effect** | **Real on behaviour, absent on outcome.** A plain instruction is the only text that consistently moves the descriptive measures: longest responses (+45 to +110 words), highest coverage, most verification markers, highest judged error-checking. None of it reaches task success or the objective score, and the instruction arm's lead over the control reversed between experiments. |
| **Role priming effect** | **Not demonstrated, and worst-in-class on the judge measure.** Identity/role priming is the family furthest below the empty control on the primary outcome (-0.156, BH q = 0.009), though it is level with the placebo arms (-0.014, CI [-0.164, +0.158]). Position is a real limitation: a role is conventionally set in a system prompt, and this tested it as a trailing sentence. |
| **Task specific effect** | **No family is task-specific in a way that survives.** 19 of 26 arms score best on **critique**, and 19 of 26 score worst on **reasoning** or **planning**, but that is the shape of the task set — critique tasks carry planted defects and have the most room to move — not a property of any phrase. No family × task-family interaction clears the bar. |
| **Overall performance effect** | **Zero.** 26 of 26 arms Neutral. 0 of 78 core contrasts demonstrated in the treatment's favour. Pairwise preference against an empty control across 1,560 comparisons: 0.472 excluding ties. |

### Two caveats that belong next to that answer

**The primary outcome ran out of room.** The empty control scored **4.950 of 5** on blind
judge task success. On that measure 25 of 26 arms sit below the control; on the objective
score, which has headroom, 11 of 26 sit above it. The judge measure discriminated on a median
of 5 of 20 tasks. An effect smaller than the ceiling can hide is not something this task set
can see, and the next experiment needs a harder one.

**The noise floor is larger than most of the effects.** Between Experiments 001 and 002, on
byte-identical text, the empty control moved **+0.167** on the primary outcome and generic
encouragement moved **+0.034** on the objective score. Almost every treatment effect measured
here is smaller than that drift. Before another phrase is tested, that floor should be
characterised directly by running one control arm several times.

---

## What would change this answer

* A task set hard enough that the control fails a meaningful fraction of the time. This one
  is saturated and the saturation is measured, not suspected.
* A phrase position other than the end of the prompt — particularly for role priming, which
  is conventionally a system-prompt device and was tested here as a trailing sentence.
* Another model. Everything here is one model in one harness.
* Longer or multi-turn tasks, where persistence has somewhere to show up. Every task in this
  set is answerable in one turn.

None of those is a reason to discount the current answer. They are the experiments that would
extend it.

---

## Index

| Experiment | Phrases | Generations | Result |
|---|---:|---:|---|
| [001 May the Force be with you](experiments/001-may-the-force-be-with-you/) | 1 | 240 | Neutral. No contrast demonstrated. |
| [002 Phrase Battery](experiments/002-phrase-battery/) | 26 arms across 9 families | 2,220 | Neutral on all 26. No family separates from placebo. |

Per-phrase index: [PHRASES.csv](PHRASES.csv) · Cross-phrase leaderboard:
[results.csv](results.csv) · Method: [METHODOLOGY.md](METHODOLOGY.md) ·
Notebook: [book/observations.md](book/observations.md),
[book/patterns.md](book/patterns.md)

**Every null and negative result in this repository stays in it.** That is the point of the
repository, and after two experiments the nulls are the evidence.
