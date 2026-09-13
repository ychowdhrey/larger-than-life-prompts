"""Randomisation must be reproducible from the seed and must balance the design."""
import collections, json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import config, manifest

CFG = os.path.join("experiments", "001-may-the-force-be-with-you", "config", "pilot.json")


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load(CFG)

    def test_expected_counts(self):
        s = manifest.build_samples(self.cfg)
        self.assertEqual(len(s), self.cfg.expected_generations)
        self.assertEqual(len(s), 5 * 4 * 2)
        self.assertEqual(len({x["sample_id"] for x in s}), len(s))

    def test_design_is_balanced(self):
        s = manifest.build_samples(self.cfg)
        per_cond = collections.Counter(x["condition_id"] for x in s)
        self.assertEqual(len(set(per_cond.values())), 1, "conditions are not balanced")
        per_task = collections.Counter(x["task_id"] for x in s)
        self.assertEqual(len(set(per_task.values())), 1, "tasks are not balanced")

    def test_execution_order_is_shuffled_not_blocked_by_condition(self):
        s = manifest.build_samples(self.cfg)
        ordered = [x["condition_id"] for x in sorted(s, key=lambda x: x["execution_index"])]
        blocked = sorted(ordered)
        self.assertNotEqual(ordered, blocked,
                            "execution order is grouped by condition; time would confound")

    def test_manifest_is_reproducible_from_the_seed(self):
        a = manifest.build_samples(self.cfg)
        b = manifest.build_samples(self.cfg)
        self.assertEqual([x["sample_id"] for x in a], [x["sample_id"] for x in b])
        self.assertEqual([x["execution_index"] for x in a], [x["execution_index"] for x in b])

    def test_changing_the_seed_changes_the_order(self):
        a = [x["sample_id"] for x in manifest.build_samples(self.cfg)]
        self.cfg.seed += 1
        b = [x["sample_id"] for x in manifest.build_samples(self.cfg)]
        self.assertNotEqual(a, b)

    def test_pairs_cover_every_primary_contrast(self):
        p = manifest.build_pairs(self.cfg)
        self.assertEqual(len(p), 5 * 2 * 3)
        by = collections.Counter(x["contrast_id"] for x in p)
        self.assertEqual(set(by), {"C_vs_A", "C_vs_B", "C_vs_D"})
        self.assertEqual(len(set(by.values())), 1)

    def test_pair_slots_are_randomised_both_ways(self):
        p = manifest.build_pairs(self.cfg)
        slots = collections.Counter(x["treatment_in_slot"] for x in p)
        self.assertEqual(set(slots), {"A", "B"},
                         "treatment always lands in the same slot; order bias would confound")

    def test_pair_slots_hold_the_right_conditions(self):
        for x in manifest.build_pairs(self.cfg):
            self.assertEqual({x["slot_a_condition"], x["slot_b_condition"]},
                             {x["treatment_condition"], x["reference_condition"]})
            expected = x["slot_a_condition"] if x["treatment_in_slot"] == "A" else x["slot_b_condition"]
            self.assertEqual(expected, x["treatment_condition"])

    def test_pairs_are_reproducible_from_the_seed(self):
        a = manifest.build_pairs(self.cfg)
        b = manifest.build_pairs(self.cfg)
        self.assertEqual([(x["pair_id"], x["treatment_in_slot"]) for x in a],
                         [(x["pair_id"], x["treatment_in_slot"]) for x in b])

    def test_full_config_is_240_generations(self):
        full = config.load(os.path.join("experiments", "001-may-the-force-be-with-you",
                                        "config", "full.json"))
        self.assertEqual(full.expected_generations, 240)
        self.assertEqual(len(manifest.build_pairs(full)), 20 * 3 * 3)


if __name__ == "__main__":
    unittest.main()
