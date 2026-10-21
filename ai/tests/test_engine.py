"""Checks on a whole match and on the bridge the screen uses. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from kuet_royale import engine
from kuet_royale.cards import COST_LEAST, COST_LIMIT
from kuet_royale.game import RIGHT, TOWER_HEALTH, State

AI_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def play_leg(session):
    reply = None
    while not engine.view(session)["leg_over"]:
        reply = engine.step(session)
    return reply


class AMatch(unittest.TestCase):
    def test_departments_are_found_from_their_card_files(self):
        found = {entry["id"]: entry for entry in engine.list_departments()}
        self.assertEqual(list(found), ["cse", "eee", "me", "ce"])
        self.assertEqual(found["cse"]["short"], "CSE")
        self.assertEqual(len(found["me"]["cards"]), 8)

    def test_a_new_match_has_two_legal_decks_and_two_legs(self):
        session = engine.new_match("cse", "me", seed=3)
        view = engine.view(session)
        for side in ("left", "right"):
            deck = view["sides"][side]["deck"]
            self.assertEqual(len(deck), 4)
            self.assertTrue(COST_LEAST <= view["sides"][side]["deck_cost"] <= COST_LIMIT)
            self.assertFalse(any(card["used"] for card in deck))
            self.assertEqual(view["sides"][side]["tower"], TOWER_HEALTH)
        self.assertEqual([leg["first"] for leg in view["legs"]], ["left", "right"])
        self.assertEqual((view["leg"], view["to_move"], view["play"], view["plays"]), (1, "left", 0, 8))
        json.dumps(session)                                      # the session must be storable as JSON

    def test_the_same_seed_gives_the_same_match(self):
        first, again = engine.new_match("cse", "me", seed=11), engine.new_match("cse", "me", seed=11)
        play_leg(first)
        play_leg(again)
        self.assertEqual(first["legs"][0]["moves"], again["legs"][0]["moves"])

    def test_a_whole_match_of_two_legs(self):
        session = engine.new_match("cse", "me", "alphabeta", "mcts", seed=5)
        reply = play_leg(session)
        view = reply["view"]
        self.assertTrue(view["leg_over"])
        self.assertFalse(view["match_over"])
        self.assertIsNone(view["winner"])
        with self.assertRaises(ValueError):
            engine.step(session)                                 # the leg is over
        view = engine.next_leg(session)["view"]
        self.assertEqual((view["leg"], view["to_move"], view["play"]), (2, "right", 0))
        self.assertEqual(view["units"], [])
        view = play_leg(session)["view"]
        self.assertTrue(view["match_over"])
        left = sum(leg["damage"]["left"] for leg in view["legs"])
        right = sum(leg["damage"]["right"] for leg in view["legs"])
        self.assertEqual(view["damage"], {"left": left, "right": right})
        self.assertEqual(view["winner"], "left" if left > right else "right" if right > left else "draw")
        with self.assertRaises(ValueError):
            engine.next_leg(session)

    def test_each_reply_tells_the_screen_what_happened(self):
        session = engine.new_match("cse", "me", "alphabeta", "mcts", seed=5)
        reply = engine.step(session)
        self.assertEqual(reply["thinking"]["algorithm"], "alphabeta")
        self.assertEqual(reply["thinking"]["plain_minimax"], 270025)
        self.assertLess(reply["thinking"]["searched"], 270025)
        self.assertTrue(reply["thinking"]["choices"][0]["chosen"])
        self.assertEqual(reply["deployed"]["tile"], reply["view"]["sides"]["left"]["starts"][reply["move"]["lane"]])
        self.assertEqual(len(reply["steps"]), 3)
        self.assertTrue(reply["comments"][0]["text"].startswith("CSE plays "))
        reply = engine.step(session)
        self.assertEqual(reply["thinking"]["algorithm"], "mcts")
        self.assertEqual(sum(row["visits"] for row in reply["thinking"]["choices"]), reply["thinking"]["repeats"])
        self.assertEqual(sum(card["used"] for card in reply["view"]["sides"]["right"]["deck"]), 1)

    def test_alpha_beta_never_slips_so_it_never_causes_a_turning_point(self):
        session = engine.new_match("cse", "me", "alphabeta", "alphabeta", seed=8)
        view = play_leg(session)["view"]
        self.assertIsNone(view["legs"][0]["turning_point"])
        self.assertTrue(all(entry["lost"] == 0 for entry in session["legs"][0]["analysis"]))

    def test_a_person_can_play_and_ask_for_a_hint(self):
        session = engine.new_match("cse", "me", "human", "alphabeta", seed=2)
        with self.assertRaises(ValueError):
            engine.step(session)                                 # it is the person's turn
        hint = engine.hint(session)["hint"]
        reply = engine.step(session, hint["index"], hint["lane"])
        self.assertEqual(reply["move"]["card"], hint["card"])
        self.assertEqual(reply["view"]["to_move"], "right")
        engine.step(session)
        with self.assertRaises(ValueError):
            engine.step(session, hint["index"], "top")           # that card has been played already

    def test_a_careless_move_is_named_as_the_turning_point(self):
        session = engine.new_match("cse", "me", "human", "alphabeta", seed=2)
        while not engine.view(session)["leg_over"]:
            view = engine.view(session)
            if view["to_move"] == "left":
                card = [entry for entry in view["sides"]["left"]["deck"] if not entry["used"]][-1]
                engine.step(session, card["index"], "bottom")
            else:
                engine.step(session)
        losses = [entry["lost"] for entry in session["legs"][0]["analysis"]]
        self.assertTrue(all(loss >= 0 for loss in losses))
        point = engine.view(session)["legs"][0]["turning_point"]
        if max(losses) > 0:
            self.assertEqual(point["lost"], max(losses))
            self.assertEqual(point["side"], "left")
        else:
            self.assertIsNone(point)

    def test_plain_minimax_position_counts(self):
        match = engine.match_of(engine.new_match("cse", "me", seed=1))
        self.assertEqual(engine.positions_without_pruning(State(match)), 270025)
        last_card = State(match, used=(15, 7), player=RIGHT, plays=7)        # the right side holds the only card left
        self.assertEqual(engine.positions_without_pruning(last_card), 3)     # this position and its two lanes


class TheBridge(unittest.TestCase):
    def ask(self, *arguments):
        out = subprocess.run([sys.executable, "bridge.py"] + list(arguments), cwd=AI_FOLDER, capture_output=True, text=True)
        return json.loads(out.stdout)

    def test_a_match_through_the_bridge(self):
        with tempfile.TemporaryDirectory() as folder:
            session = os.path.join(folder, "match.json")
            self.assertEqual([entry["short"] for entry in self.ask("departments")["departments"]][:1], ["CSE"])
            reply = self.ask("new", "--left", "me", "--right", "cse", "--seed", "4", "--session", session)
            self.assertTrue(reply["ok"])
            self.assertEqual(reply["view"]["sides"]["left"]["short"], "ME")
            reply = self.ask("step", "--session", session)
            self.assertEqual(reply["view"]["play"], 1)
            self.assertEqual(self.ask("view", "--session", session)["view"]["play"], 1)
            self.assertTrue(self.ask("hint", "--session", session)["ok"])

    def test_a_mistake_comes_back_as_a_message_not_a_crash(self):
        with tempfile.TemporaryDirectory() as folder:
            session = os.path.join(folder, "match.json")
            self.ask("new", "--session", session)
            reply = self.ask("next", "--session", session)
            self.assertFalse(reply["ok"])
            self.assertIn("still being played", reply["error"])

    def test_the_answer_can_go_to_a_file(self):
        with tempfile.TemporaryDirectory() as folder:
            out = os.path.join(folder, "reply.json")
            subprocess.run([sys.executable, "bridge.py", "departments", "--out", out], cwd=AI_FOLDER, check=True)
            with open(out, encoding="utf-8") as handle:
                self.assertTrue(json.load(handle)["ok"])


if __name__ == "__main__":
    unittest.main()
