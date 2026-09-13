"""The objective scorer must award full marks to a correct response and withhold them
from a violating one. A scorer that cannot tell the difference would null the experiment."""
import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ltlp import config, objective
from ltlp.objective import _words

EXP = os.path.join(config.REPO_ROOT, "experiments", "001-may-the-force-be-with-you")
TASKS = {t["id"]: t for t in json.load(open(os.path.join(EXP, "tasks.json")))["tasks"]}


def score(tid, text):
    return objective.score(TASKS[tid], text)


def failed(result):
    return sorted(c["check_id"] for c in result["checks"] if not c["passed"])


GOOD_SCHEDULE = (
    "Critical path is T1, T2, T4, T6.\n"
    "DAY 1 | E1 | T1\nDAY 2 | E1 | T1\n"
    "DAY 3 | E1 | T2\nDAY 4 | E1 | T2\nDAY 3 | E2 | T3\nDAY 4 | E2 | T3\n"
    "DAY 5 | E1 | T4\nDAY 6 | E1 | T4\nDAY 7 | E1 | T4\nDAY 5 | E2 | T5\nDAY 6 | E2 | T5\n"
    "DAY 8 | E1 | T6\nDAY 9 | E1 | T6\nDAY 10 | E1 | T6\n\nLAST DAY: 10")


class TestCorrectResponsesScoreFull(unittest.TestCase):
    def test_R01(self):
        r = score("R01", "23:40 UTC+8 is 15:40 UTC. Plus 13h25m.\n\nFINAL ANSWER: 2027-03-04 05:05")
        self.assertEqual(failed(r), [])

    def test_C01_full_recall(self):
        r = score("C01",
            "1. seen=[] is a mutable default argument and persists between calls.\n"
            "2. scores.sort() sorts in place and mutates the caller's list.\n"
            "3. range(0, limit) raises IndexError when the list is shorter than limit.\n"
            "4. sum(scores)/len(scores) is a ZeroDivisionError on an empty list.\n")
        self.assertEqual(failed(r), [])
        self.assertEqual(r["planted_issue_recall"], 1.0)
        self.assertEqual(r["distractor_avoidance"], 1.0)

    def test_P03_feasible_schedule(self):
        self.assertEqual(failed(score("P03", GOOD_SCHEDULE)), [])

    def test_P04_consistent_budget(self):
        text = ("ITEM: Conference sponsorship | 12000\nITEM: Contractor writing | 9000\n"
                "ITEM: Travel | 6000\nITEM: Tooling and software | 3000\nITEM: Swag | 2500\n"
                "ITEM: Community events | 4000\nITEM: Video | 3000\nITEM: Contingency | 2500\n\n"
                "TOTAL: 42000")
        self.assertEqual(failed(score("P04", text)), [])


class TestViolationsAreCaught(unittest.TestCase):
    def test_wrong_final_answer_loses_the_answer_check(self):
        r = score("R01", "FINAL ANSWER: 2027-03-04 13:05")
        self.assertIn("answer", failed(r))
        self.assertNotIn("format", failed(r))  # format was still obeyed

    def test_false_positive_costs_a_distractor_point(self):
        r = score("C01", "The only problem is that reverse=True is wrong, it should be reverse=False.")
        self.assertIn("distractor_reverse", failed(r))
        self.assertLess(r["distractor_avoidance"], 1.0)

    def test_dependency_violation_is_detected(self):
        bad = GOOD_SCHEDULE.replace("DAY 3 | E1 | T2", "DAY 2 | E1 | T2")
        r = score("P03", bad)
        self.assertIn("schedule_valid", failed(r))

    def test_capacity_violation_is_detected(self):
        bad = GOOD_SCHEDULE + "\nDAY 1 | E1 | T3"
        self.assertIn("schedule_valid", failed(score("P03", bad)))

    def test_over_budget_is_detected(self):
        text = "\n".join("ITEM: X%d | 6000" % i for i in range(8)) + \
               "\nITEM: Contingency | 4000\n\nTOTAL: 52000"
        self.assertIn("sum_consistency", failed(score("P04", text)))

    def test_total_not_matching_items_is_detected(self):
        text = "\n".join("ITEM: X%d | 5000" % i for i in range(8)) + \
               "\nITEM: Contingency | 2000\n\nTOTAL: 40000"
        self.assertIn("sum_consistency", failed(score("P04", text)))

    def test_banned_word_and_wrong_ending_are_caught(self):
        body = ("Saved Views is available today. It is included in all paid plans. "
                "Each user can save up to 50 views. Views can be shared with a team. "
                + " ".join(["Views help."] * 60) + " This is seamless. Try it now.")
        f = failed(score("W01", body))
        self.assertIn("banned", f)
        self.assertIn("closing", f)

    def test_word_count_band_is_enforced(self):
        short = ("Saved Views is available today. It is included in all paid plans. "
                 "Each user can save up to 50 views. Views can be shared with a team. "
                 "Open any list and select Save view to get started.")
        self.assertIn("word_count", failed(score("W01", short)))

    def test_empty_response_does_not_crash_any_task(self):
        for tid in TASKS:
            r = score(tid, "")
            self.assertIsNotNone(r["objective_score"])
            self.assertGreaterEqual(r["earned_points"], 0.0)

    def test_garbage_response_does_not_crash_any_task(self):
        junk = "\x00� | | | DAY x | TOTAL: abc ```unclosed"
        for tid in TASKS:
            self.assertIsNotNone(score(tid, junk)["objective_score"])


class TestScorerIsConditionBlind(unittest.TestCase):
    def test_appending_condition_text_does_not_change_the_score(self):
        """The scorer must not react to a response that echoes its condition."""
        base = "1. mutable default argument seen=[] persists between calls."
        a = score("C01", base)["earned_points"]
        for suffix in ("\n\nMay the Force be with you.", "\n\nGood luck. Do your best."):
            self.assertEqual(score("C01", base + suffix)["earned_points"], a)


if __name__ == "__main__":
    unittest.main()
