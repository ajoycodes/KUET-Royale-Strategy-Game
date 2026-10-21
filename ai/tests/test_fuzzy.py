"""Checks on the fuzzy system. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import unittest

from kuet_royale import fuzzy


class TheLabExample(unittest.TestCase):
    def test_reproduces_the_lab_tip_example(self):
        tip = fuzzy.make_system(
            "tip",
            inputs={"service": {"poor": [(0, 1), (2, 1), (4, 0)], "good": [(2, 0), (5, 1), (8, 0)],
                                "excellent": [(6, 0), (8, 1), (10, 1)]},
                    "food": {"bad": [(0, 1), (3, 1), (7, 0)], "delicious": [(3, 0), (7, 1), (10, 1)]}},
            output={"cheap": [(5, 1), (10, 1), (13, 0)], "average": [(10, 0), (15, 1), (20, 0)],
                    "generous": [(17, 0), (20, 1), (25, 1)]},
            rule_lines=["IF service is poor OR food is bad THEN tip is cheap",
                        "IF service is good THEN tip is average",
                        "IF service is excellent OR food is delicious THEN tip is generous"],
            samples=list(range(6, 25, 2)))
        outcome = fuzzy.infer(tip, {"service": 3, "food": 6})
        self.assertAlmostEqual(outcome["strengths"]["cheap"], 0.5)
        self.assertAlmostEqual(outcome["strengths"]["average"], 1 / 3)
        self.assertAlmostEqual(outcome["strengths"]["generous"], 0.75)
        self.assertAlmostEqual(outcome["output"], 16.03, places=1)

    def test_operators(self):
        self.assertEqual(fuzzy.fuzzy_or(0.2, 0.7), 0.7)
        self.assertEqual(fuzzy.fuzzy_and(0.2, 0.7), 0.2)
        self.assertAlmostEqual(fuzzy.fuzzy_not(0.2), 0.8)

    def test_membership_follows_the_straight_lines(self):
        good = [(2, 0), (5, 1), (8, 0)]
        self.assertEqual(fuzzy.membership(good, 2), 0)
        self.assertEqual(fuzzy.membership(good, 5), 1)
        self.assertAlmostEqual(fuzzy.membership(good, 3.5), 0.5)
        self.assertEqual(fuzzy.membership(good, 9), 0)


class ChoosingATarget(unittest.TestCase):
    def test_there_are_exactly_three_rules(self):
        self.assertEqual(len(fuzzy.TARGET_RULES), 3)
        self.assertEqual(sorted(rule[2] for rule in fuzzy.TARGET["rules"]), ["high", "low", "medium"])

    def test_one_case_worked_by_hand(self):
        # An enemy 1 tile away with half its health left.
        #   near = 0.5, medium distance = 0.5, far = 0      low = 0, medium health = 1, full = 0
        #   high = max(0.5, 0) = 0.5    medium = max(0.5, 1) = 1    low = max(0, 0) = 0
        outcome = fuzzy.infer(fuzzy.TARGET, {"distance": 1, "health": 50})
        self.assertAlmostEqual(outcome["degrees"]["distance"]["near"], 0.5)
        self.assertAlmostEqual(outcome["degrees"]["health"]["medium"], 1.0)
        self.assertEqual(outcome["strengths"], {"high": 0.5, "medium": 1.0, "low": 0.0})
        self.assertEqual(fuzzy.priority(1, 50), 63.5)

    def test_a_closer_enemy_is_never_less_urgent(self):
        for health in range(0, 101, 10):
            for distance in range(0, 4):
                self.assertGreaterEqual(fuzzy.priority(distance, health), fuzzy.priority(distance + 1, health))

    def test_a_weaker_enemy_is_never_less_urgent(self):
        for distance in range(0, 5):
            for health in range(0, 100, 10):
                self.assertGreaterEqual(fuzzy.priority(distance, health), fuzzy.priority(distance, health + 10))

    def test_the_two_extremes(self):
        self.assertGreater(fuzzy.priority(0, 0), 80)             # next to me and almost dead
        self.assertLess(fuzzy.priority(4, 100), 20)              # far away and untouched

    def test_equal_enemies_get_exactly_equal_priority(self):
        self.assertEqual(fuzzy.priority(2, 50), 50.0)
        self.assertEqual(fuzzy.priority(1, 75), fuzzy.priority(3, 25))


if __name__ == "__main__":
    unittest.main()
