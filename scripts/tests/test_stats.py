"""Statistics checked against values computed independently."""
import math, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import stats


class TestKnownValues(unittest.TestCase):
    def test_binomial_matches_exact_enumeration(self):
        self.assertAlmostEqual(stats.binom_test_two_sided(8, 10), 0.109375, places=9)
        self.assertAlmostEqual(stats.binom_test_two_sided(10, 10), 2 / 1024, places=9)
        self.assertAlmostEqual(stats.binom_test_two_sided(5, 10), 1.0, places=9)

    def test_wilson_matches_closed_form(self):
        def ref(k, n, z=1.959963985):
            p, d = k / n, 1 + 1.959963985 ** 2 / n
            c = (p + z * z / (2 * n)) / d
            h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
            return (max(0.0, c - h), min(1.0, c + h))
        for k, n in ((8, 10), (0, 10), (10, 10), (45, 60)):
            a, b = stats.wilson_ci(k, n), ref(k, n)
            self.assertAlmostEqual(a[0], b[0], places=12)
            self.assertAlmostEqual(a[1], b[1], places=12)

    def test_permutation_all_same_sign_is_the_exact_minimum(self):
        # every flip except the identity and the full flip gives a smaller |mean|
        for n in (5, 6, 8):
            p = stats.paired_permutation_test([1.0] * n, seed=1)
            self.assertAlmostEqual(p, 2 / (2 ** n), places=12)

    def test_permutation_symmetric_data_is_not_significant(self):
        self.assertGreater(stats.paired_permutation_test([1, -1, 1, -1, 1, -1], seed=1), 0.5)

    def test_cohens_dz(self):
        # mean 1.5, sd 0.5773502692 for [1,2,1,2]
        self.assertAlmostEqual(stats.cohens_dz([1, 2, 1, 2]), 1.5 / math.sqrt(1 / 3.0), places=9)
        self.assertIsNone(stats.cohens_dz([1]), "needs at least two observations")
        self.assertIsNone(stats.cohens_dz([2, 2, 2, 2]), "zero variance has no dz")

    def test_holm_is_monotone_and_bounded(self):
        adj = stats.holm({"a": 0.01, "b": 0.04, "c": 0.5})
        self.assertAlmostEqual(adj["a"], 0.03)
        self.assertAlmostEqual(adj["b"], 0.08)
        self.assertAlmostEqual(adj["c"], 0.5)
        self.assertTrue(all(v <= 1.0 for v in adj.values()))

    def test_holm_never_reduces_a_p_value(self):
        raw = {"a": 0.2, "b": 0.3, "c": 0.9}
        adj = stats.holm(raw)
        for k in raw:
            self.assertGreaterEqual(adj[k], raw[k])


class TestSeedDeterminism(unittest.TestCase):
    def test_bootstrap_is_reproducible_from_the_seed(self):
        clusters = [[0.13 * i, 0.31 * i + 0.7] for i in range(1, 13)]
        a = stats.cluster_bootstrap_ci(clusters, seed=99)
        b = stats.cluster_bootstrap_ci(clusters, seed=99)
        self.assertEqual(a, b, "same seed must give the same interval")
        # The seed is genuinely used: with few draws two seeds disagree. At the default
        # 10,000 draws the percentile endpoints have converged and agree, which is the
        # property we actually want from a reported interval.
        few_a = stats.cluster_bootstrap_ci(clusters, seed=99, draws=50)
        few_b = stats.cluster_bootstrap_ci(clusters, seed=100, draws=50)
        self.assertNotEqual(few_a, few_b, "seed is not reaching the resampler")
        converged = stats.cluster_bootstrap_ci(clusters, seed=100)
        for x, y in zip(a, converged):
            self.assertAlmostEqual(x, y, places=6, msg="bootstrap has not converged")

    def test_bootstrap_interval_brackets_the_mean(self):
        clusters = [[1, 2], [2, 3], [3, 4], [2, 2], [1, 3], [4, 4]]
        flat = [v for c in clusters for v in c]
        lo, hi = stats.cluster_bootstrap_ci(clusters, seed=5)
        self.assertLessEqual(lo, sum(flat) / len(flat))
        self.assertGreaterEqual(hi, sum(flat) / len(flat))

    def test_degenerate_inputs_return_none_rather_than_crashing(self):
        self.assertIsNone(stats.cluster_bootstrap_ci([], seed=1))
        self.assertIsNone(stats.cluster_bootstrap_ci([[1]], seed=1))
        self.assertIsNone(stats.paired_permutation_test([], seed=1))
        self.assertIsNone(stats.wilson_ci(0, 0))
        self.assertIsNone(stats.mean([]))


if __name__ == "__main__":
    unittest.main()
