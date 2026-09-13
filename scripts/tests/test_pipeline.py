"""End to end pipeline behaviour on the mock backend: resumability, immutability, blinding.

These run the real stages against a temporary run directory, so they exercise the same
code path the pilot uses, with no model calls.
"""
import copy, json, os, shutil, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import (analyze, config, generate, judge, report, score_objective, util)
from ltlp.util import ImmutableWriteError

import experiment as cli  # the CLI module, for prepare


class Args:
    workers = 1
    limit = None
    force = False
    keep_going = True


def make_cfg(tmp, **over):
    base = util.read_json(os.path.join(
        config.REPO_ROOT, "experiments", "001-may-the-force-be-with-you", "config", "pilot.json"))
    base["run_id"] = "unittest-mock"
    base["generation"] = {"backend": "mock", "model": "mock-model"}
    base["judging"] = {"backend": "mock", "model": "mock-judge"}
    base["tasks"] = ["R01", "C01"]
    base["repetitions"] = 2
    base["experiment_dir"] = tmp
    base.update(over)
    # the spec files still point at the real repository, which is what we want to lock
    path = os.path.join(tmp, "cfg.json")
    util.write_json(path, base)
    return config.load(path)


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="ltlp-test-")
        cls.cfg = make_cfg(cls.tmp)
        cli.cmd_prepare(cls.cfg, Args())
        generate.run(cls.cfg)
        score_objective.run(cls.cfg)
        judge.run_blind(cls.cfg)
        judge.run_pairwise(cls.cfg)
        cls.summary = analyze.run(cls.cfg)
        cls.report_text = report.run(cls.cfg)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---- completeness

    def test_every_sample_was_generated(self):
        self.assertEqual(len(generate.load_responses(self.cfg)), 2 * 4 * 2)
        self.assertEqual(self.summary["counts"]["generations_present"], 16)

    def test_every_sample_was_scored_and_judged(self):
        self.assertEqual(self.summary["counts"]["objective_scored"], 16)
        self.assertEqual(self.summary["counts"]["blind_judged"], 16)
        self.assertEqual(self.summary["counts"]["pairwise_judged"], 2 * 2 * 3)

    # ---- resumability

    def test_rerunning_generate_regenerates_nothing(self):
        before = {sid: r["response_sha256"]
                  for sid, r in generate.load_responses(self.cfg).items()}
        s = generate.run(self.cfg)
        self.assertEqual(s["attempted"], 0, "a resumed run tried to redo completed work")
        self.assertEqual(s["already_done"], 16)
        after = {sid: r["response_sha256"]
                 for sid, r in generate.load_responses(self.cfg).items()}
        self.assertEqual(before, after, "a resumed run changed an existing raw output")

    def test_rerunning_every_stage_is_a_no_op(self):
        for fn in (score_objective.run, judge.run_blind, judge.run_pairwise):
            self.assertEqual(fn(self.cfg)["attempted"], 0)

    def test_interrupted_generate_resumes_without_loss(self):
        tmp2 = tempfile.mkdtemp(prefix="ltlp-resume-")
        try:
            cfg = make_cfg(tmp2)
            cli.cmd_prepare(cfg, Args())
            first = generate.run(cfg, limit=5)      # simulate an interruption
            self.assertEqual(first["completed"], 5)
            partial = {sid: r["response_sha256"]
                       for sid, r in generate.load_responses(cfg).items()}
            second = generate.run(cfg)              # resume
            self.assertEqual(second["already_done"], 5)
            self.assertEqual(len(generate.load_responses(cfg)), 16)
            for sid, sha in partial.items():
                self.assertEqual(generate.load_responses(cfg)[sid]["response_sha256"], sha,
                                 "resuming rewrote a sample produced before the interruption")
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    # ---- immutability

    def test_raw_outputs_refuse_to_be_overwritten(self):
        path = self.cfg.p("raw", "R01-A-r1.json")
        self.assertTrue(os.path.exists(path))
        with self.assertRaises(ImmutableWriteError):
            util.write_json_once(path, {"tampered": True})

    def test_raw_index_hashes_match_the_files(self):
        for entry in util.read_jsonl(self.cfg.p("raw", "INDEX.jsonl")):
            path = self.cfg.p("raw", entry["file"])
            self.assertEqual(util.sha256_file(path), entry["file_sha256"])

    def test_verify_passes_on_a_clean_run(self):
        self.assertEqual(cli.cmd_verify(self.cfg, Args()), 0)

    def test_verify_detects_tampering(self):
        path = self.cfg.p("raw", "R01-A-r1.json")
        original = util.read_text(path)
        try:
            util.write_text(path, original.replace('"response":', '"response_TAMPERED":', 1))
            self.assertEqual(cli.cmd_verify(self.cfg, Args()), 1,
                             "verify did not notice an edited raw output")
        finally:
            util.write_text(path, original)
        self.assertEqual(cli.cmd_verify(self.cfg, Args()), 0)

    # ---- the spec lock

    def test_stages_refuse_to_run_if_a_spec_file_changed(self):
        lock_path = self.cfg.p("spec.lock.json")
        lock = util.read_json(lock_path)
        original = copy.deepcopy(lock)
        try:
            lock["hashes"]["tasks"] = "0" * 64   # pretend tasks.json was edited
            util.write_json(lock_path, lock)
            with self.assertRaises(config.SpecLockError):
                generate.run(self.cfg)
            with self.assertRaises(config.SpecLockError):
                judge.run_blind(self.cfg)
            with self.assertRaises(config.SpecLockError):
                analyze.run(self.cfg)
        finally:
            util.write_json(lock_path, original)
        generate.run(self.cfg)  # works again once restored

    # ---- blinding

    def test_no_judge_record_carries_condition_text(self):
        suffixes = [c["suffix"] for c in self.cfg.conditions if c["suffix"]]
        for sub in ("blind", "pairwise"):
            d = self.cfg.p("judge", sub)
            for name in os.listdir(d):
                blob = util.read_text(os.path.join(d, name))
                for suf in suffixes:
                    self.assertNotIn(suf, blob)

    def test_blind_judgments_are_filed_under_opaque_ids(self):
        names = {n[:-5] for n in os.listdir(self.cfg.p("judge", "blind"))}
        for n in names:
            for cond in ("-A-", "-B-", "-C-", "-D-"):
                self.assertNotIn(cond, n, "a condition is readable from the filename")
        mapping = util.read_json(self.cfg.p("state", "blind_map.json"))["map"]
        self.assertEqual(names, set(mapping.values()))

    def test_pairwise_slots_map_back_to_conditions_correctly(self):
        pairs = {p["pair_id"]: p for p in util.read_json(self.cfg.p("pairs.json"))["pairs"]}
        for name in os.listdir(self.cfg.p("judge", "pairwise")):
            rec = util.read_json(os.path.join(self.cfg.p("judge", "pairwise"), name))
            pair = pairs[rec["pair_id"]]
            if rec["preference_slot"] == "Tie":
                self.assertIsNone(rec["treatment_won"])
            else:
                expected = (pair["slot_a_condition"] if rec["preference_slot"] == "A"
                            else pair["slot_b_condition"])
                self.assertEqual(rec["winner_condition"], expected)
                self.assertEqual(rec["treatment_won"],
                                 expected == pair["treatment_condition"])

    # ---- outputs

    def test_analysis_outputs_exist_and_parse(self):
        for name in ("summary.json", "results.csv", "samples.csv", "analysis.md"):
            self.assertTrue(os.path.exists(self.cfg.p("analysis", name)), name)
        json.loads(util.read_text(self.cfg.p("analysis", "summary.json")))

    def test_report_keeps_the_required_sections_apart(self):
        for heading in ("Observed behavioural change",
                        "Measured task performance change",
                        "Statistical uncertainty",
                        "Possible confounds",
                        "Interpretation rule"):
            self.assertIn(heading, self.report_text)
        for question in ("beat **Control**", "beat **generic encouragement**",
                         "beat an **explicit effort instruction**"):
            self.assertIn(question, self.report_text)

    def test_report_makes_no_claim_about_internal_states(self):
        """Affirmative mental-state claims are banned. Denying them is required."""
        low = self.report_text.lower()
        for claim in ("the model is motivated", "the model wants", "the model feels",
                      "genuinely motivated", "the model tried harder",
                      "shows motivation", "is more motivated"):
            self.assertNotIn(claim, low)
        # the denial itself must be present
        self.assertIn("not claims that a model wants anything", low)
        self.assertIn("this experiment measures text", low)

    def test_report_marks_a_pilot_as_not_evidence(self):
        self.assertIn("PILOT", self.report_text)
        self.assertIn("Observed", self.report_text)

    def test_summary_records_everything_needed_to_reproduce(self):
        meta = self.summary["run_meta"]
        for field in ("seed", "prepared_at", "generation", "judging", "versions",
                      "conditions", "tasks", "system_prompt_generation"):
            self.assertIn(field, meta)
        self.assertEqual(self.summary["spec_lock"]["versions"]["tasks"], "1.0.0")
        self.assertEqual(self.summary["spec_lock"]["versions"]["rubric"], "2.0.0")


if __name__ == "__main__":
    unittest.main()
