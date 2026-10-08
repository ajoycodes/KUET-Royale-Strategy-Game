"""Checks on the card files. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import unittest

from kuet_royale.cards import COST_LIMIT, ROLES, WALKS, check_roster, load_roster

DEPARTMENTS = ("cse", "me")


class TheRosters(unittest.TestCase):
    def test_both_rosters_are_well_formed(self):
        for department in DEPARTMENTS:
            self.assertEqual(check_roster(load_roster(department)), [], department)

    def test_every_role_offers_a_choice(self):
        for department in DEPARTMENTS:
            cards = load_roster(department)
            for role in ROLES:
                self.assertGreaterEqual(sum(card["role"] == role for card in cards), 2, (department, role))

    def test_every_walking_style_is_used(self):
        # Each style is one path search, so each department needs all three.
        for department in DEPARTMENTS:
            used = {card["walks"] for card in load_roster(department)}
            self.assertEqual(used, set(WALKS), department)

    def test_each_department_has_one_splash_card(self):
        for department in DEPARTMENTS:
            self.assertEqual(sum(card["splash"] for card in load_roster(department)), 1, department)

    def test_a_legal_deck_exists(self):
        # Cheapest Tank + cheapest Ranged + cheapest Fast + cheapest card left over.
        for department in DEPARTMENTS:
            cards = load_roster(department)
            deck = []
            for role in ROLES:
                deck.append(min((card for card in cards if card["role"] == role), key=lambda card: card["cost"]))
            rest = [card for card in cards if card not in deck]
            deck.append(min(rest, key=lambda card: card["cost"]))
            self.assertLessEqual(sum(card["cost"] for card in deck), COST_LIMIT, department)

    def test_the_dearest_deck_breaks_the_limit(self):
        # Otherwise the cost limit would never force a choice.
        for department in DEPARTMENTS:
            costs = sorted((card["cost"] for card in load_roster(department)), reverse=True)
            self.assertGreater(sum(costs[:4]), COST_LIMIT, department)


class ABrokenRoster(unittest.TestCase):
    def test_problems_are_reported_in_words(self):
        cards = load_roster("cse")
        cards[0] = dict(cards[0], cost=0, role="Wizard", walks="swims")
        problems = check_roster(cards)
        self.assertEqual(len(problems), 3)
        self.assertTrue(all(problem.startswith("Compiler") for problem in problems))

    def test_a_short_roster_is_reported(self):
        self.assertIn("a roster has 8 cards, found 7", check_roster(load_roster("me")[:7]))


if __name__ == "__main__":
    unittest.main()
