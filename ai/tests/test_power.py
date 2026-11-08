"""Checks on the one-minute power mode. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from kuet_royale import alphabeta, power
from kuet_royale.game import LEFT, RIGHT, TOWER_HEALTH

AI_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def person_against_nobody(seed=1):
    """A session with people on both seats, so that only what the test asks for is dropped."""
    return power.new_match("cse", "me", "human", "human", seed=seed)


def cheapest_in_hand(session, side):
    match = power._match_of(session)
    return min(session["queues"][side][:power.HAND], key=lambda card: match.decks[side][card]["cost"])


class TheClockAndTheCoins(unittest.TestCase):
    def test_a_new_match_is_one_minute_long(self):
        view = power.view(person_against_nobody())
        self.assertEqual(view["seconds_left"], 60)
        self.assertEqual(view["sides"]["left"]["coins"], power.COINS_START)
        self.assertEqual(view["sides"]["left"]["tower"], TOWER_HEALTH)
        self.assertEqual(len(view["sides"]["left"]["hand"]), power.HAND)
        json.dumps(person_against_nobody())

    def test_coins_grow_with_time_up_to_the_most(self):
        session = person_against_nobody()
        for _ in range(power.COIN_EVERY):
            power.beat(session)
        self.assertEqual(session["coins"], [power.COINS_START + 1] * 2)
        for _ in range(power.COIN_EVERY * (power.COINS_MOST + 2)):
            power.beat(session)
        self.assertEqual(session["coins"], [power.COINS_MOST] * 2)

    def test_a_drop_costs_coins_and_the_card_goes_to_the_back_of_the_queue(self):
        session = person_against_nobody()
        match = power._match_of(session)
        card = cheapest_in_hand(session, LEFT)
        upcoming = session["queues"][LEFT][power.HAND]
        reply = power.beat(session, ["left:%d:5" % card])
        self.assertEqual(session["coins"][LEFT], power.COINS_START - match.decks[LEFT][card]["cost"])
        self.assertEqual(session["queues"][LEFT][-1], card)
        self.assertIn(upcoming, session["queues"][LEFT][:power.HAND])
        self.assertEqual(reply["deployed"][0]["move"]["spot"], 5)

    def test_all_eight_cards_come_round(self):
        session = person_against_nobody()
        seen = set()
        while len(seen) < 8 and not power.is_over(session):
            session["towers"] = [TOWER_HEALTH, TOWER_HEALTH]        # so that the clock runs out before a tower falls
            card = session["queues"][LEFT][0]
            if power._match_of(session).decks[LEFT][card]["cost"] <= session["coins"][LEFT]:
                seen.add(card)
                power.beat(session, ["left:%d:0" % card])
            else:
                power.beat(session)
        self.assertEqual(len(seen), 8)
        self.assertEqual(sorted(session["queues"][LEFT]), list(range(8)))

    def test_a_drop_that_cannot_be_paid_for_is_refused(self):
        session = person_against_nobody()
        session["coins"][LEFT] = 0
        reply = power.beat(session, ["left:%d:0" % session["queues"][LEFT][0]])
        self.assertEqual(reply["refused"], ["left"])
        self.assertEqual(reply["deployed"], [])

    def test_a_card_not_in_hand_or_a_bad_tile_is_refused(self):
        session = person_against_nobody()
        session["coins"][LEFT] = 10
        out_of_hand = session["queues"][LEFT][-1]
        self.assertEqual(power.beat(session, ["left:%d:0" % out_of_hand])["refused"], ["left"])
        self.assertEqual(power.beat(session, ["left:%d:999" % session["queues"][LEFT][0]])["refused"], ["left"])

    def test_both_sides_can_drop_in_the_same_beat(self):
        session = person_against_nobody()
        reply = power.beat(session, ["left:%d:0" % cheapest_in_hand(session, LEFT), "right:%d:0" % cheapest_in_hand(session, RIGHT)])
        self.assertEqual(sorted(entry["side"] for entry in reply["deployed"]), ["left", "right"])
        self.assertEqual(session["plays"], 2)


class TheBrainsClock(unittest.TestCase):
    def test_two_brains_can_drop_in_the_same_beat(self):
        session = power.new_match("cse", "me", "mcts", "mcts", seed=3)
        both = 0
        while not power.is_over(session):
            both += len(power.beat(session)["deployed"]) == 2
        self.assertGreater(both, 0)

    def test_a_brain_waits_until_it_can_pay_for_any_card_in_its_hand(self):
        session = power.new_match("cse", "me", "mcts", "mcts", seed=3)
        dearest = max(power._match_of(session).decks[LEFT][card]["cost"] for card in session["queues"][LEFT][:power.HAND])
        session["coins"][LEFT] = dearest - 1
        self.assertNotIn("left", power.beat(session)["thinking"])


class TheEnd(unittest.TestCase):
    def test_it_ends_when_the_clock_runs_out(self):
        session = person_against_nobody()
        for _ in range(power.BEATS):
            self.assertFalse(power.is_over(session))
            power.beat(session)
        self.assertTrue(power.is_over(session))
        self.assertEqual(power.view(session)["winner"], "draw")
        with self.assertRaises(ValueError):
            power.beat(session)

    def test_a_fallen_tower_ends_it_at_once(self):
        session = person_against_nobody()
        session["towers"] = [0, 12]
        self.assertTrue(power.is_over(session))
        self.assertEqual(power.view(session)["winner"], "right")

    def test_the_tower_with_more_health_wins_when_time_is_up(self):
        session = person_against_nobody()
        session["beat"] = power.BEATS
        session["towers"] = [11, 9]
        self.assertEqual(power.view(session)["winner"], "left")


class TheBrains(unittest.TestCase):
    def test_a_whole_match_of_the_two_brains(self):
        session = power.new_match("cse", "me", "alphabeta", "mcts", seed=2)
        winner = power.play_out(session)
        self.assertIn(winner, ("left", "right", "draw"))
        self.assertGreater(session["plays"], 10)
        self.assertEqual(sorted(session["queues"][LEFT]), list(range(8)))
        self.assertTrue(all(0 <= coins <= power.COINS_MOST for coins in session["coins"]))

    def test_the_same_seed_gives_the_same_match(self):
        first, again = (power.new_match("ce", "eee", "mcts", "alphabeta", seed=9) for _ in range(2))
        power.play_out(first)
        power.play_out(again)
        self.assertEqual((first["towers"], first["units"]), (again["towers"], again["units"]))

    def test_with_no_coins_a_brain_does_not_think_at_all(self):
        session = power.new_match("cse", "me", "alphabeta", "human", seed=1)
        session["coins"][LEFT] = 0
        self.assertEqual(power.beat(session)["thinking"], {})

    def test_alpha_beta_gives_the_same_answer_as_plain_minimax_on_the_window(self):
        def minimax(state):
            if power.terminal(state):
                return power.utility(state)
            values = [minimax(power.result(state, action)) for action in power.actions(state)]
            return max(values) if state.player == LEFT else min(values)

        session = person_against_nobody(3)
        session["coins"] = [2, 2]
        match = power._match_of(session)
        for side in (LEFT, RIGHT):
            state = power._window(match, session, side, 2)
            state.end = min(power.BEATS, session["beat"] + 8)
            self.assertEqual(alphabeta.alpha_beta_decision(state, power)[1], minimax(state))

    def test_waiting_is_chosen_when_no_drop_changes_the_score(self):
        session = power.new_match("cse", "me", "alphabeta", "human", seed=1)
        session["beat"] = power.BEATS - 1                        # no time left for a drop to reach anything
        action, thinking = power.think(power._match_of(session), session, LEFT, "alphabeta", None)
        self.assertEqual(action, power.WAIT)
        self.assertEqual(thinking["choices"][0]["card"], "Hold on")


class TheBridge(unittest.TestCase):
    def ask(self, *arguments):
        out = subprocess.run([sys.executable, "bridge.py"] + list(arguments), cwd=AI_FOLDER, capture_output=True, text=True)
        return json.loads(out.stdout)

    def test_a_power_match_through_the_bridge(self):
        with tempfile.TemporaryDirectory() as folder:
            session = os.path.join(folder, "match.json")
            reply = self.ask("power_new", "--left", "cse", "--left-brain", "human", "--right", "me", "--seed", "4", "--session", session)
            self.assertTrue(reply["ok"])
            card = reply["view"]["sides"]["left"]["hand"][0]["index"]
            reply = self.ask("power_beat", "--drop", "left:%d:0" % card, "--session", session)
            self.assertTrue(reply["ok"])
            self.assertEqual(reply["view"]["beat"], 1)

    def test_the_troop_picker_gets_a_legal_deck_from_the_solver(self):
        deck = self.ask("deck", "--left", "ce", "--seed", "5")["deck"]
        self.assertEqual(len(deck), 4)


if __name__ == "__main__":
    unittest.main()
