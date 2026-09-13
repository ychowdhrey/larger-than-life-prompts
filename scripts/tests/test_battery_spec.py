"""The battery's spec files, and the runner changes that made a second experiment possible.

These guard four claims the repository makes in prose:

  * the battery is measured on the same instrument Experiment 001 was measured on;
  * conditions.json is what phrases.json generates, so the arm list cannot drift from the
    registry that documents it;
  * pairwise scoping and optional spec hashing did not change Experiment 001's lock;
  * report.py refuses a battery instead of rendering an unreadable wall of columns.
"""
import json, os, subprocess, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import config, manifest, util

REPO = config.REPO_ROOT
EXP2 = os.path.join(REPO, "experiments", "002-phrase-battery")
EXP1 = os.path.join(REPO, "experiments", "001-may-the-force-be-with-you")


class TestSharedTaskSet(unittest.TestCase):
    def test_core_task_set_is_byte_identical_to_the_one_001_ran(self):
        # Comparability across experiments is the entire point of a shared task set. If
        # these two files ever differ, every cross-experiment sentence becomes false.
        a = util.sha256_file(os.path.join(REPO, "tasks", "core-v1.json"))
        b = util.sha256_file(os.path.join(EXP1, "tasks.json"))
        self.assertEqual(a, b)
        self.assertEqual(a, "cbf894cf1017789bce66af365478ca32fb0fb9fa617097c1f181e4e5a673db52",
                         "the hash quoted in PREREGISTRATION.md must stay true")


class TestConditionsAreGenerated(unittest.TestCase):
    def test_conditions_json_is_what_phrases_json_generates(self):
        rc = subprocess.call([sys.executable,
                              os.path.join(REPO, "scripts", "build_battery_conditions.py"),
                              "--check"], stdout=subprocess.DEVNULL)
        self.assertEqual(rc, 0, "run scripts/build_battery_conditions.py and commit the result")

    def test_shared_controls_are_byte_identical_to_experiment_001(self):
        one = {c["id"]: c["suffix"] for c in
               util.read_json(os.path.join(EXP1, "conditions.json"))["conditions"]}
        two = {c["id"]: c["suffix"] for c in
               util.read_json(os.path.join(EXP2, "conditions.json"))["conditions"]}
        for cid in ("A", "B", "D"):
            self.assertEqual(one[cid], two[cid])
        self.assertEqual(two["T01"], one["C"], "T01 is the replication of 001's phrase")

    def test_every_treatment_has_a_family_hypothesis_and_mechanism(self):
        reg = util.read_json(os.path.join(EXP2, "phrases.json"))
        fams = {f["id"] for f in reg["families"]}
        for t in reg["treatments"]:
            self.assertIn(t["family"], fams, t["id"])
            self.assertTrue(t["hypothesis"].strip(), t["id"])
            self.assertTrue(t["mechanism"].strip(), t["id"])
            if t.get("secondary_family"):
                self.assertIn(t["secondary_family"], fams, t["id"])

    def test_combo_suffix_is_the_phrase_then_the_canonical_effort_instruction(self):
        doc = util.read_json(os.path.join(EXP2, "conditions.json"))
        by_id = {c["id"]: c for c in doc["conditions"]}
        effort = by_id["D"]["suffix"]
        for c in doc["conditions"]:
            if c.get("role") == "combo":
                self.assertEqual(c["suffix"],
                                 "%s %s" % (by_id[c["phrase_arm"]]["suffix"], effort))

    def test_a_placebo_built_combo_exists_because_it_is_the_combo_control(self):
        doc = util.read_json(os.path.join(EXP2, "conditions.json"))
        reg = util.read_json(os.path.join(EXP2, "phrases.json"))
        placebo_arms = {t["id"] for t in reg["treatments"] if t.get("role") == "placebo"}
        combo_parents = {c["phrase_arm"] for c in doc["conditions"]
                         if c.get("role") == "combo"}
        self.assertTrue(placebo_arms & combo_parents,
                        "without a placebo-built combo, 'does emotion amplify an "
                        "instruction' has no control and cannot be answered")

    def test_every_treatment_arm_has_all_three_core_contrasts(self):
        doc = util.read_json(os.path.join(EXP2, "conditions.json"))
        ids = {c["id"] for c in doc["primary_contrasts"]}
        for c in doc["conditions"]:
            if c["id"].startswith("T"):
                for ref in ("A", "B", "D"):
                    self.assertIn("%s_vs_%s" % (c["id"], ref), ids)

    def test_pairwise_is_scoped_to_the_empty_control_contrast(self):
        doc = util.read_json(os.path.join(EXP2, "conditions.json"))
        self.assertTrue(all(c["reference"] == "A" for c in doc["pairwise_contrasts"]))
        self.assertLess(len(doc["pairwise_contrasts"]), len(doc["primary_contrasts"]))


class TestRunnerChangesDidNotMove001(unittest.TestCase):
    def test_001_spec_lock_still_verifies(self):
        cfg = config.load(os.path.join(EXP1, "config", "full.json"))
        cfg.verify_spec_lock()  # raises on drift

    def test_001_locks_exactly_the_six_required_files(self):
        cfg = config.load(os.path.join(EXP1, "config", "full.json"))
        self.assertEqual(sorted(cfg.locked_spec_files), sorted(config.SPEC_FILES),
                         "adding an optional spec file must not change an experiment "
                         "that does not declare one")

    def test_the_battery_additionally_locks_its_phrase_registry(self):
        cfg = config.load(os.path.join(EXP2, "config", "full.json"))
        self.assertIn("phrases", cfg.locked_spec_files)
        self.assertIn("phrases", cfg.spec_hashes())

    def test_dropping_a_spec_entry_after_prepare_is_caught_as_drift(self):
        # Comparing only the names still in the config would let you unlock a file by
        # deleting its entry. The union is what makes that impossible.
        cfg = config.load(os.path.join(EXP1, "config", "full.json"))
        locked = util.read_json(cfg.p("spec.lock.json"))["hashes"]
        self.assertEqual(set(locked), set(cfg.spec_hashes()))

    def test_an_unknown_spec_entry_is_rejected_rather_than_silently_unhashed(self):
        raw = util.read_json(os.path.join(EXP1, "config", "full.json"))
        raw["spec"]["something_new"] = "README.md"
        with self.assertRaises(ValueError):
            config.Config(raw, "synthetic")

    def test_pairwise_contrasts_default_to_primary_when_not_declared(self):
        cfg = config.load(os.path.join(EXP1, "config", "full.json"))
        self.assertEqual(cfg.pairwise_contrasts, cfg.primary_contrasts)
        self.assertEqual(len(manifest.build_pairs(cfg)),
                         len(cfg.primary_contrasts) * len(cfg.tasks) * cfg.repetitions)

    def test_declared_pairwise_contrasts_bound_the_pair_count(self):
        cfg = config.load(os.path.join(EXP2, "config", "full.json"))
        self.assertEqual(len(manifest.build_pairs(cfg)),
                         len(cfg.pairwise_contrasts) * len(cfg.tasks) * cfg.repetitions)
        self.assertLess(len(manifest.build_pairs(cfg)),
                        len(cfg.primary_contrasts) * len(cfg.tasks) * cfg.repetitions)

    def test_prepare_takes_identity_from_the_spec_not_a_literal(self):
        import experiment as cli  # noqa: F401  (imported for the module under test)
        meta = util.read_json(os.path.join(EXP1, "runs", "full-001", "run_meta.json"))
        cfg = config.load(os.path.join(EXP1, "config", "full.json"))
        derived_id = cfg.raw.get("experiment_id") or cfg.conditions_doc.get("experiment_id")
        derived_phrase = cfg.raw.get("phrase") or cfg.condition(
            cfg.conditions_doc["primary_treatment"])["suffix"]
        self.assertEqual(derived_id, meta["experiment_id"])
        self.assertEqual(derived_phrase, meta["phrase"],
                         "the fallback must reproduce the committed run_meta exactly")


class TestReportRefusesABattery(unittest.TestCase):
    def test_ladder_renderer_refuses_an_experiment_with_too_many_arms(self):
        from ltlp import report
        cfg = config.load(os.path.join(EXP2, "config", "full.json"))
        with self.assertRaises(RuntimeError) as ctx:
            report.run(cfg)
        self.assertIn("battery", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()


class TestVerifyLedgerIsTamperEvident(unittest.TestCase):
    """The README calls raw/INDEX.jsonl tamper-evident. These are the probes for that.

    Before this check compared both directions, a raw file ADDED after the ledger was
    built was never looked at, and an empty ledger printed OK having verified nothing.
    A check that reports nothing is indistinguishable from a check that passes.
    """

    def _run(self, tmp, *, finished=True):
        import shutil
        import experiment as cli
        raw = os.path.join(tmp, "runs", "probe", "raw")
        os.makedirs(raw)
        os.makedirs(os.path.join(tmp, "runs", "probe", "state"))
        raw_cfg = util.read_json(os.path.join(EXP1, "config", "full.json"))
        raw_cfg["experiment_dir"] = tmp
        raw_cfg["run_id"] = "probe"
        cfg = config.Config(raw_cfg, "synthetic")
        util.write_json(cfg.p("spec.lock.json"), cfg.spec_lock_document())
        util.write_json(cfg.p("state", "stages.json"),
                        {"generate": {"finished_at": "2026-09-13T00:00:00+00:00"}}
                        if finished else {})
        for sid in ("R01-A-r1", "R01-C-r1"):
            util.write_json_once(os.path.join(raw, "%s.json" % sid),
                                 {"sample_id": sid, "response": "x",
                                  "response_sha256": "deadbeef"})
        from ltlp import generate
        generate.rebuild_index(cfg)
        return cfg

    def _verify_rc(self, cfg):
        import io, contextlib
        import experiment as cli

        class A:
            pass
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.cmd_verify(cfg, A())
        return rc, buf.getvalue()

    def test_clean_run_passes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._run(tmp)
            rc, out = self._verify_rc(cfg)
            self.assertEqual(rc, 0)
            self.assertIn("2 files in ledger, 2 on disk", out)

    def test_a_raw_file_added_outside_the_ledger_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._run(tmp)
            util.write_json_once(cfg.p("raw", "R01-A-r9.json"),
                                 {"sample_id": "R01-A-r9", "response": "fabricated"})
            rc, out = self._verify_rc(cfg)
            self.assertEqual(rc, 1, "a fabricated raw output must not pass verification")
            self.assertIn("not in the ledger", out)

    def test_an_edited_raw_file_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._run(tmp)
            path = cfg.p("raw", "R01-A-r1.json")
            os.unlink(path)
            util.write_json_once(path, {"sample_id": "R01-A-r1", "response": "tampered"})
            rc, out = self._verify_rc(cfg)
            self.assertEqual(rc, 1)
            self.assertIn("changed", out)

    def test_an_empty_ledger_is_reported_as_unverified_not_as_a_pass(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._run(tmp, finished=False)
            os.unlink(cfg.p("raw", "INDEX.jsonl"))
            rc, out = self._verify_rc(cfg)
            self.assertIn("NOT YET BUILT", out)
            self.assertIn("unverified", out)
            self.assertNotIn("raw immutability: OK", out)
