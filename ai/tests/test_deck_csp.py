"""Checks on the deck builder. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import unittest

from kuet_royale import deck_csp
from kuet_royale.cards import COST_LEAST, COST_LIMIT, load_roster
from kuet_royale.deck_csp import SLOTS, build_deck, deck_from_picks, get_domain, is_valid, order_cards, select_slot


def card(name, role, cost):
    return {"name": name, "role": role, "cost": cost}


class RealRosters(unittest.TestCase):
    def test_every_deck_obeys_every_constraint(self):
        for department in ("cse", "me"):
            cards = load_roster(department)
            for seed in range(60):
                deck, _ = build_deck(cards, seed)
                self.assertEqual(len(deck), 4)
                self.assertEqual(len({chosen["name"] for chosen in deck}), 4)
                self.assertEqual([chosen["role"] for chosen in deck[:3]], ["Tank", "Ranged", "Fast"])
                self.assertTrue(COST_LEAST <= sum(chosen["cost"] for chosen in deck) <= COST_LIMIT)

    def test_the_same_seed_builds_the_same_deck(self):
        cards = load_roster("cse")
        self.assertEqual(build_deck(cards, 5)[0], build_deck(cards, 5)[0])

    def test_different_seeds_give_a_variety_of_decks(self):
        for department in ("cse", "me"):
            cards = load_roster(department)
            decks = {tuple(sorted(chosen["name"] for chosen in build_deck(cards, seed)[0])) for seed in range(100)}
            self.assertGreaterEqual(len(decks), 10, department)

    def test_the_trace_lists_each_choice(self):
        deck, trace = build_deck(load_roster("me"), 1)
        tried = [entry for entry in trace if entry["step"] == "try"]
        self.assertEqual(len(tried) - sum(entry["step"] == "undo" for entry in trace), 4)
        self.assertEqual(tried[-1]["cost"], sum(chosen["cost"] for chosen in deck))


class TheMethod(unittest.TestCase):
    def test_is_valid(self):
        tank, bow = card("T", "Tank", 5), card("R", "Ranged", 4)
        self.assertTrue(is_valid({"Tank": tank, "Ranged": bow}))
        self.assertFalse(is_valid({"Tank": tank, "Free": tank}))                             # the same card twice
        self.assertFalse(is_valid({"Tank": tank, "Ranged": card("R2", "Ranged", 5), "Fast": card("F", "Fast", 5)}))    # 15: too dear
        cheap = {"Tank": card("a", "Tank", 2), "Ranged": card("b", "Ranged", 2), "Fast": card("c", "Fast", 2),
                 "Free": card("d", "Fast", 2)}
        self.assertFalse(is_valid(cheap))                                                    # finished at 8: too cheap

    def test_mrv_picks_the_slot_with_the_fewest_cards(self):
        cards = [card("T1", "Tank", 5), card("T2", "Tank", 4), card("R1", "Ranged", 4),
                 card("F1", "Fast", 2), card("F2", "Fast", 3), card("F3", "Fast", 2)]
        self.assertEqual(select_slot(cards, {}), "Ranged")               # one Ranged card, two Tanks, three Fast

    def test_lcv_tries_the_least_constraining_card_first(self):
        # After an 11-cost Tank no Ranged card fits any more. After the 4-cost Tank everything still fits.
        cards = [card("T-dear", "Tank", 11), card("T-cheap", "Tank", 4), card("R1", "Ranged", 4), card("R2", "Ranged", 5),
                 card("F1", "Fast", 2), card("F2", "Fast", 3)]
        order = [chosen["name"] for chosen in order_cards(cards, {}, "Tank")]
        self.assertEqual(order, ["T-cheap", "T-dear"])

    def test_domain_shrinks_as_the_deck_fills(self):
        cards = load_roster("cse")
        names = {chosen["name"]: chosen for chosen in cards}
        deck = {"Tank": names["Compiler"], "Ranged": names["Optimizer"], "Fast": names["Cloud Drone"]}   # 12 so far
        free = [chosen["name"] for chosen in get_domain(cards, deck, "Free")]
        self.assertEqual(sorted(free), ["Debugger", "Stack Runner"])     # only a 2-cost card fits, and it must be new

    def test_backtracking_undoes_a_choice_that_leads_nowhere(self):
        # The cheap Tank is tried first. With it every finished deck costs 9 (too cheap) or 15 (too dear),
        # so the solver has to take it back and use the dear Tank: 7 + 4 + 2 + 1 = 14.
        cards = [card("T-cheap", "Tank", 2), card("T-dear", "Tank", 7), card("R", "Ranged", 4),
                 card("F", "Fast", 2), card("X", "Ranged", 1)]
        deck, trace = build_deck(cards)
        self.assertEqual([chosen["name"] for chosen in deck], ["T-dear", "R", "F", "X"])
        self.assertIn({"step": "undo", "slot": "Tank", "card": "T-cheap"}, trace)

    def test_no_deck_at_all_is_an_error(self):
        with self.assertRaises(ValueError):
            build_deck([card("T", "Tank", 2), card("R", "Ranged", 2), card("F", "Fast", 2), card("X", "Fast", 2)])

    def test_slots(self):
        self.assertEqual(SLOTS, ("Tank", "Ranged", "Fast", "Free"))
        self.assertTrue(deck_csp.fits_slot(card("x", "Tank", 1), "Free"))
        self.assertFalse(deck_csp.fits_slot(card("x", "Tank", 1), "Fast"))


class ThePickersDeck(unittest.TestCase):
    def setUp(self):
        self.cards = load_roster("cse")

    def test_a_legal_pick_comes_back_in_slot_order(self):
        deck = deck_from_picks(self.cards, ["Stack Runner", "Compiler", "Debugger", "Optimizer"])
        self.assertEqual([card["name"] for card in deck[:2]], ["Compiler", "Optimizer"])
        self.assertEqual(deck[2]["role"], "Fast")
        self.assertEqual(sum(card["cost"] for card in deck), 13)

    def test_a_pick_that_breaks_a_rule_is_refused_with_a_reason(self):
        for names, reason in ((["Compiler", "Compiler", "Debugger", "Algorithmist"], "different"),
                              (["Algorithmist", "Optimizer", "Debugger", "Stack Runner"], "Tank"),
                              (["Compiler", "Kernel", "Algorithmist", "Debugger"], "13 or 14")):
            with self.assertRaises(ValueError) as caught:
                deck_from_picks(self.cards, names)
            self.assertIn(reason, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
