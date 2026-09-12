"""Independently recompute every reasoning answer asserted by the task set.

A task set whose stated answer is wrong would invert the whole experiment, so the answers
are derived here from first principles rather than copied from the task file.
"""
import json, os, re, sys, unittest
from datetime import datetime, timedelta
from itertools import permutations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import config

EXP = os.path.join(config.REPO_ROOT, "experiments", "001-may-the-force-be-with-you")
TASKS = {t["id"]: t for t in json.load(open(os.path.join(EXP, "tasks.json")))["tasks"]}


def answer_pattern(task_id):
    t = TASKS[task_id]
    check = [c for c in t["checks"] if c["id"] == "answer"][0]
    return check["patterns"][0]


def asserts_answer(task_id, text):
    return re.search(answer_pattern(task_id), text, re.IGNORECASE | re.DOTALL) is not None


class TestReasoningAnswers(unittest.TestCase):
    def test_R01_flight_arrival(self):
        arrive = (datetime(2027, 3, 3, 23, 40) - timedelta(hours=8)
                  + timedelta(hours=13, minutes=25))
        self.assertTrue(asserts_answer("R01", "FINAL ANSWER: %s" % arrive.strftime("%Y-%m-%d %H:%M")))

    def test_R02_posterior(self):
        p, sens, spec = 0.002, 0.98, 0.95
        post = p * sens / (p * sens + (1 - p) * (1 - spec))
        self.assertTrue(asserts_answer("R02", "FINAL ANSWER: %.2f" % (post * 100)))

    def test_R03_seating_is_unique(self):
        names = ["Ana", "Ben", "Chi", "Dev", "Eli"]
        sols = []
        for perm in permutations(names):
            s = {n: i + 1 for i, n in enumerate(perm)}
            if not s["Ben"] < s["Chi"]: continue
            if s["Ana"] in (1, 5): continue
            if abs(s["Dev"] - s["Eli"]) != 3: continue
            if abs(s["Chi"] - s["Dev"]) == 1: continue
            if not s["Eli"] > s["Ana"]: continue
            if s["Ana"] != s["Ben"] + 1: continue
            sols.append(perm)
        self.assertEqual(len(sols), 1, "puzzle must have exactly one solution")
        self.assertTrue(asserts_answer("R03", "FINAL ANSWER: %s" % ", ".join(sols[0])))

    def test_R04_balance(self):
        bal = 10000.0
        for r in (1.12, 0.88, 1.05):
            bal = bal * r - 90
        self.assertTrue(asserts_answer("R04", "FINAL ANSWER: %.2f" % bal))

    def test_R05_count(self):
        n = sum(1 for i in range(1, 1001) if (i % 3 == 0 or i % 5 == 0) and i % 7 != 0)
        self.assertTrue(asserts_answer("R05", "FINAL ANSWER: %d" % n))


class TestTaskSetIntegrity(unittest.TestCase):
    def test_twenty_tasks_five_per_family(self):
        doc = json.load(open(os.path.join(EXP, "tasks.json")))
        self.assertEqual(len(doc["tasks"]), 20)
        fams = {}
        for t in doc["tasks"]:
            fams[t["family"]] = fams.get(t["family"], 0) + 1
        self.assertEqual(fams, {"reasoning": 5, "critique": 5, "planning": 5, "writing": 5})

    def test_ids_and_checks_unique_and_points_consistent(self):
        for t in TASKS.values():
            ids = [c["id"] for c in t["checks"]]
            self.assertEqual(len(ids), len(set(ids)), t["id"])
            self.assertAlmostEqual(t["max_points"], sum(c["points"] for c in t["checks"]))

    def test_every_check_type_is_implemented(self):
        from ltlp import objective
        for t in TASKS.values():
            for c in t["checks"]:
                self.assertIn(c["type"], objective.EVALUATORS, "%s/%s" % (t["id"], c["id"]))

    def test_no_task_prompt_mentions_the_phrase_or_the_hypothesis(self):
        for t in TASKS.values():
            low = t["base_prompt"].lower()
            for banned in ("may the force", "good luck", "do your best",
                           "especially thorough", "motivat"):
                self.assertNotIn(banned, low, "%s leaks a condition into the base prompt" % t["id"])


if __name__ == "__main__":
    unittest.main()
