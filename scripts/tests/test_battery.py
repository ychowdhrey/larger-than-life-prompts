"""Battery analysis: the decision rule, the classification table, pooling and multiplicity.

Every assertion here is about a claim the battery report makes in prose. The point is that
a deliberately broken input produces a different label, not that the code runs.
"""
import math, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import battery, stats


def contrast(diff, ci, n_pairs=60):
    return {"task_level_mean_difference": diff, "ci95_task_level": ci, "n_pairs": n_pairs}


class TestDecisionRule(unittest.TestCase):
    """All three conditions must hold. Any one missing is 'not demonstrated'."""

    def test_all_three_hold_counts_for_the_treatment(self):
        c = contrast(0.30, [0.10, 0.50])
        self.assertEqual(battery._demonstrated(c, 0.01), "treatment")

    def test_interval_spanning_zero_is_a_direction_not_an_effect(self):
        c = contrast(0.30, [-0.05, 0.65])
        self.assertEqual(battery._demonstrated(c, 0.01), "not_demonstrated")

    def test_significance_without_an_excluding_interval_is_not_enough(self):
        self.assertEqual(battery._demonstrated(contrast(0.3, None), 0.001), "not_demonstrated")

    def test_an_excluding_interval_without_significance_is_not_enough(self):
        c = contrast(0.30, [0.10, 0.50])
        self.assertEqual(battery._demonstrated(c, 0.20), "not_demonstrated")
        self.assertEqual(battery._demonstrated(c, None), "not_demonstrated")

    def test_alpha_is_strict(self):
        c = contrast(0.30, [0.10, 0.50])
        self.assertEqual(battery._demonstrated(c, battery.ALPHA), "not_demonstrated")
        self.assertEqual(battery._demonstrated(c, battery.ALPHA - 1e-9), "treatment")

    def test_a_demonstrated_difference_the_other_way_favours_the_reference(self):
        c = contrast(-0.30, [-0.50, -0.10])
        self.assertEqual(battery._demonstrated(c, 0.01), "reference")

    def test_no_data_is_never_demonstrated(self):
        self.assertEqual(battery._demonstrated(contrast(0.3, [0.1, 0.5], n_pairs=0), 0.001),
                         "not_demonstrated")
        self.assertEqual(battery._demonstrated(contrast(None, [0.1, 0.5]), 0.001),
                         "not_demonstrated")


def rec(verdicts, fdr=True, arm="T09"):
    """A phrase record carrying only what _classify reads."""
    out = {"arm_id": arm, "contrasts": {battery.PRIMARY: {}}}
    for ref, v in verdicts.items():
        out["contrasts"][battery.PRIMARY]["%s_vs_%s" % (arm, ref)] = {
            "verdict": v, "n_pairs": 60,
            "survives_battery_fdr": fdr if ref == "A" else False}
    return out


class TestClassification(unittest.TestCase):
    """The labels are the pre-registered table, applied mechanically."""

    def test_beats_control_and_an_active_control_and_survives_fdr_is_positive(self):
        label, why, _ = battery._classify(rec({"A": "treatment", "B": "treatment",
                                               "D": "not_demonstrated"}))
        self.assertEqual(label, "Positive")
        self.assertIn("condition B", why)

    def test_beating_only_the_empty_control_is_weak_positive(self):
        label, why, _ = battery._classify(rec({"A": "treatment", "B": "not_demonstrated",
                                               "D": "not_demonstrated"}))
        self.assertEqual(label, "Weak positive")
        self.assertIn("appended text", why,
                      "the reason must name why an active control matters")

    def test_failing_the_battery_fdr_demotes_a_positive_to_weak(self):
        label, why, _ = battery._classify(rec({"A": "treatment", "B": "treatment",
                                               "D": "treatment"}, fdr=False))
        self.assertEqual(label, "Weak positive")
        self.assertIn("FDR", why)

    def test_nothing_demonstrated_is_neutral(self):
        label, _, _ = battery._classify(rec({"A": "not_demonstrated", "B": "not_demonstrated",
                                             "D": "not_demonstrated"}))
        self.assertEqual(label, "Neutral")

    def test_losing_to_a_reference_without_beating_control_is_negative(self):
        label, why, caveats = battery._classify(rec({"A": "not_demonstrated",
                                                     "B": "not_demonstrated",
                                                     "D": "reference"}))
        self.assertEqual(label, "Negative")
        self.assertIn("T09_vs_D", why)
        self.assertEqual(len(caveats), 1)

    def test_a_mixed_result_keeps_the_adverse_effect_visible(self):
        # Beats nothing-appended but loses to the effort instruction: a real pattern, and
        # the adverse half must not disappear into the label.
        label, _, caveats = battery._classify(rec({"A": "treatment", "B": "not_demonstrated",
                                                   "D": "reference"}))
        self.assertEqual(label, "Weak positive")
        self.assertEqual(len(caveats), 1)
        self.assertIn("T09_vs_D", caveats[0])

    def test_missing_data_is_inconclusive(self):
        r = rec({"A": "not_demonstrated"})
        r["contrasts"][battery.PRIMARY]["T09_vs_A"]["n_pairs"] = 0
        self.assertEqual(battery._classify(r)[0], "Inconclusive")


class TestPooling(unittest.TestCase):
    def test_task_level_diffs_pair_inside_task_and_repetition(self):
        cells = {("R01", 1): {"T": 5.0, "A": 3.0},
                 ("R01", 2): {"T": 4.0, "A": 4.0},
                 ("R02", 1): {"T": 1.0, "A": 3.0}}
        d = battery._task_level_diffs(cells, "T", "A")
        self.assertAlmostEqual(d["R01"], 1.0, msg="mean of +2 and 0 within the task")
        self.assertAlmostEqual(d["R02"], -2.0)

    def test_a_cell_missing_one_side_is_dropped_not_imputed(self):
        cells = {("R01", 1): {"T": 5.0}, ("R02", 1): {"T": 2.0, "A": 1.0}}
        self.assertEqual(set(battery._task_level_diffs(cells, "T", "A")), {"R02"})

    def test_pooling_averages_within_task_so_the_task_stays_the_unit(self):
        # Two member arms, one task. Concatenating would give n=2 observations for one
        # task and an interval that is too narrow; averaging gives n=1 task.
        cells = {("R01", 1): {"X": 4.0, "Y": 2.0, "A": 3.0}}
        per_task = {}
        for arm in ("X", "Y"):
            for t, v in battery._task_level_diffs(cells, arm, "A").items():
                per_task.setdefault(t, []).append(v)
        pooled = {t: stats.mean(v) for t, v in per_task.items()}
        self.assertEqual(len(pooled), 1)
        self.assertAlmostEqual(pooled["R01"], 0.0, msg="+1 and -1 average to zero")


class TestConsistency(unittest.TestCase):
    def test_tied_tasks_are_excluded_from_the_denominator(self):
        # A perfectly consistent effect on 2 of 10 tasks is 100% consistent, not 20%.
        d = {"t%d" % i: 0.0 for i in range(8)}
        d.update({"t8": 0.5, "t9": 0.5})
        self.assertAlmostEqual(battery._consistency(d), 1.0)

    def test_disagreement_is_measured_against_the_overall_direction(self):
        self.assertAlmostEqual(battery._consistency({"a": 1.0, "b": 1.0, "c": -1.0, "d": 3.0}),
                               0.75)

    def test_all_ties_has_no_consistency_rather_than_zero(self):
        self.assertIsNone(battery._consistency({"a": 0.0, "b": 0.0}))


class TestBenjaminiHochberg(unittest.TestCase):
    def test_matches_a_hand_computed_example(self):
        # m=4; q_i = min over j>=i of m*p_j/j, enforced monotone
        adj = stats.benjamini_hochberg({"a": 0.005, "b": 0.02, "c": 0.06, "d": 0.5})
        self.assertAlmostEqual(adj["a"], 0.02)    # min(4*.005/1, .04, .08, .5)
        self.assertAlmostEqual(adj["b"], 0.04)
        self.assertAlmostEqual(adj["c"], 0.08)
        self.assertAlmostEqual(adj["d"], 0.5)

    def test_is_never_more_conservative_than_holm(self):
        p = {"a": 0.001, "b": 0.01, "c": 0.02, "d": 0.3, "e": 0.9}
        bh, hm = stats.benjamini_hochberg(p), stats.holm(p)
        for k in p:
            self.assertLessEqual(bh[k], hm[k] + 1e-12,
                                 "FDR must not exceed FWER for the same family")

    def test_is_monotone_in_rank(self):
        p = {"k%d" % i: v for i, v in enumerate([0.001, 0.004, 0.02, 0.04, 0.2])}
        adj = stats.benjamini_hochberg(p)
        vals = [adj["k%d" % i] for i in range(5)]
        self.assertEqual(vals, sorted(vals))

    def test_missing_p_values_stay_missing(self):
        adj = stats.benjamini_hochberg({"a": 0.01, "b": None})
        self.assertIsNone(adj["b"])
        self.assertIsNotNone(adj["a"])

    def test_empty_family_is_all_none(self):
        self.assertEqual(stats.benjamini_hochberg({"a": None}), {"a": None})


class TestPerPhraseHolmIsScopedToOnePhrase(unittest.TestCase):
    def test_holm_over_three_contrasts_not_over_the_whole_battery(self):
        # The decision rule is Holm across ONE arm's three contrasts. Holm over all 78
        # would multiply the smallest p by 78 instead of by 3, which is the battery-wide
        # view reported separately and deliberately not used as the rule.
        three = stats.holm({"T_vs_A": 0.01, "T_vs_B": 0.4, "T_vs_D": 0.6})
        self.assertAlmostEqual(three["T_vs_A"], 0.03)
        seventy_eight = stats.holm({"c%d" % i: (0.01 if i == 0 else 0.9) for i in range(78)})
        self.assertAlmostEqual(seventy_eight["c0"], 0.78)


if __name__ == "__main__":
    unittest.main()
