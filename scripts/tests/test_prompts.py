"""The experiment's central validity claim: conditions differ ONLY by the suffix."""
import json, os, re, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import config, prompts

REPO = config.REPO_ROOT
EXP = os.path.join(REPO, "experiments", "001-may-the-force-be-with-you")


def load():
    tasks = json.load(open(os.path.join(EXP, "tasks.json")))["tasks"]
    conds = json.load(open(os.path.join(EXP, "conditions.json")))
    return tasks, conds


class TestPromptEquivalence(unittest.TestCase):
    def test_only_difference_is_the_suffix(self):
        tasks, conds = load()
        join = conds["join"]
        for task in tasks:
            rendered = {c["id"]: prompts.render_prompt(task["base_prompt"], c["suffix"], join)
                        for c in conds["conditions"]}
            for c in conds["conditions"]:
                stripped = prompts.strip_suffix(rendered[c["id"]], c["suffix"], join)
                self.assertEqual(stripped, task["base_prompt"],
                                 "%s/%s differs by more than its suffix" % (task["id"], c["id"]))

    def test_control_is_byte_identical_to_the_base_prompt(self):
        tasks, conds = load()
        control = [c for c in conds["conditions"] if c["id"] == "A"][0]
        self.assertEqual(control["suffix"], "")
        for task in tasks:
            self.assertEqual(prompts.render_prompt(task["base_prompt"], control["suffix"]),
                             task["base_prompt"])

    def test_each_condition_produces_a_distinct_prompt(self):
        tasks, conds = load()
        for task in tasks:
            rendered = {c["id"]: prompts.render_prompt(task["base_prompt"], c["suffix"])
                        for c in conds["conditions"]}
            self.assertEqual(len(set(rendered.values())), len(conds["conditions"]),
                             "two conditions produced the same prompt for %s" % task["id"])

    def test_suffix_is_appended_at_the_end(self):
        tasks, conds = load()
        for task in tasks:
            for c in conds["conditions"]:
                if not c["suffix"]:
                    continue
                self.assertTrue(
                    prompts.render_prompt(task["base_prompt"], c["suffix"]).endswith(c["suffix"]))


class TestBlinding(unittest.TestCase):
    def test_blind_judge_prompt_contains_no_condition_text(self):
        tasks, conds = load()
        suffixes = [c["suffix"] for c in conds["conditions"] if c["suffix"]]
        template = open(os.path.join(REPO, "evals", "judge-prompt-blind.md")).read()
        for task in tasks:
            # even if a response somehow contained the phrase, the TASK half must not
            payload = prompts.build_blind_judge_prompt(template, task["base_prompt"],
                                                       "a response")
            for suf in suffixes:
                self.assertNotIn(suf, payload,
                                 "condition text leaked into the judge prompt for %s" % task["id"])

    def test_pairwise_judge_prompt_contains_no_condition_text(self):
        tasks, conds = load()
        suffixes = [c["suffix"] for c in conds["conditions"] if c["suffix"]]
        template = open(os.path.join(REPO, "evals", "judge-prompt.md")).read()
        for task in tasks:
            payload = prompts.build_pairwise_judge_prompt(template, task["base_prompt"], "a", "b")
            for suf in suffixes:
                self.assertNotIn(suf, payload)

    def test_judge_templates_never_reveal_the_hypothesis(self):
        """The templates may *forbid* mentioning treatments; they must never reveal one."""
        _, conds = load()
        for name in ("judge-prompt-blind.md", "judge-prompt.md"):
            text = open(os.path.join(REPO, "evals", name)).read()
            low = text.lower()
            for c in conds["conditions"]:
                if c["suffix"]:
                    self.assertNotIn(c["suffix"].lower(), low,
                                     "%s contains condition text" % name)
                # bare words like "control" legitimately appear in the instruction
                # telling the judge not to mention controls; distinctive names must not
                name = c["name"].replace("_", " ")
                if " " in name:
                    self.assertNotIn(name, low, "%s names a condition" % name)
            self.assertNotIn("star wars", low)
            # no substitution slot could carry a condition into the judge's context
            slots = set(re.findall(r"\{\{(\w+)\}\}", text))
            self.assertTrue(slots <= {"TASK", "RESPONSE", "RESPONSE_A", "RESPONSE_B"},
                            "unexpected template slots: %s" % slots)

    def test_blind_item_ids_are_stable_and_opaque(self):
        a = prompts.blind_item_id("key", "R01-C-r1")
        self.assertEqual(a, prompts.blind_item_id("key", "R01-C-r1"))
        self.assertNotEqual(a, prompts.blind_item_id("key", "R01-A-r1"))
        self.assertEqual(len(a), 16)
        # the id must not be invertible without the key
        self.assertNotEqual(a, prompts.blind_item_id("other-key", "R01-C-r1"))
        # ids for the four conditions of one task/rep must look unrelated
        ids = [prompts.blind_item_id("key", "R01-%s-r1" % c) for c in "ABCD"]
        self.assertEqual(len(set(ids)), 4)
        for i in ids:
            self.assertNotIn("R01", i)

    def test_condition_echo_detection(self):
        self.assertIsNotNone(prompts.condition_echo(
            "Good luck! May the Force be with you.", ["May the Force be with you."]))
        self.assertIsNone(prompts.condition_echo(
            "The answer is 42.", ["May the Force be with you."]))


if __name__ == "__main__":
    unittest.main()
