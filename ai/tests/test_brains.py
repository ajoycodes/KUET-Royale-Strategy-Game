"""Checks on the two brains: alpha-beta and Monte Carlo Tree Search. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import math
import random
import unittest

from kuet_royale import alphabeta, mcts
from kuet_royale.cards import load_roster
from kuet_royale.game import LEFT, RIGHT, Match, State, actions, result, terminal, utility
from kuet_royale.grid import load_map

CSE = {card["name"]: card for card in load_roster("cse")}
ME = {card["name"]: card for card in load_roster("me")}


def a_match():
    return Match(load_map(), [CSE[name] for name in ("Kernel", "Logic Bomber", "Debugger", "Cloud Drone")],
                 [ME[name] for name in ("Heavy Machine", "Robotic Arm", "Gear Runner", "Mini-Bot")])


# Plain minimax, exactly as in Lab 04, to compare alpha-beta against.
def max_value(state):
    if terminal(state):
        return utility(state), None
    v, best = -math.inf, None
    for action in actions(state):
        value, _ = min_value(result(state, action))
        if value > v:
            v, best = value, action
    return v, best


def min_value(state):
    if terminal(state):
        return utility(state), None
    v, best = math.inf, None
    for action in actions(state):
        value, _ = max_value(result(state, action))
        if value < v:
            v, best = value, action
    return v, best


def minimax(state):
    return max_value(state) if state.player == LEFT else min_value(state)


class AlphaBeta(unittest.TestCase):
    def test_it_gives_exactly_the_answer_of_plain_minimax(self):
        rng = random.Random(1)
        for first in (LEFT, RIGHT):
            for _ in range(6):
                state = State(a_match(), player=first)
                for _ in range(rng.choice((2, 3, 4))):           # a few random cards, then compare from there
                    state = result(state, rng.choice(actions(state)))
                if terminal(state):
                    continue
                self.assertEqual(alphabeta.alpha_beta(state)[0], minimax(state)[0])

    def test_from_the_very_first_card_too(self):
        state = result(State(a_match()), (0, 0))                 # one card played, the other side to move
        self.assertEqual(alphabeta.alpha_beta(state)[0], minimax(state)[0])

    def test_the_move_it_returns_really_is_worth_its_value(self):
        state = State(a_match())
        value, action = alphabeta.alpha_beta(state)
        self.assertEqual(alphabeta.alpha_beta(result(state, action))[0], value)

    def test_it_looks_at_far_fewer_positions_than_plain_minimax(self):
        state = State(a_match())
        action, value, table = alphabeta.alpha_beta_decision(state)
        self.assertLess(alphabeta.searched, 270025 // 5)         # plain minimax: 270,025 positions
        self.assertGreater(alphabeta.pruned, 0)
        self.assertEqual(len(table), 8)

    def test_the_table_for_the_screen_is_honest(self):
        state = State(a_match())
        action, value, table = alphabeta.alpha_beta_decision(state)
        self.assertEqual(value, alphabeta.alpha_beta(state)[0])
        for move, score, exact, _ in table:
            true = alphabeta.alpha_beta(result(state, move))[0]
            if exact:
                self.assertEqual(score, true)
            else:
                self.assertLessEqual(true, score)                # left wants it high: "no better than score"
            if move == action:
                self.assertTrue(exact)
                self.assertEqual(score, value)

    def test_the_right_side_wants_the_score_low(self):
        state = State(a_match(), player=RIGHT)
        action, value, table = alphabeta.alpha_beta_decision(state)
        self.assertEqual(value, min(score for _, score, exact, _ in table if exact))
        for move, score, exact, _ in table:
            if not exact:
                self.assertGreaterEqual(alphabeta.alpha_beta(result(state, move))[0], score)

    def test_a_finished_leg_has_no_move(self):
        state = State(a_match(), towers=(0, 20))
        self.assertEqual(alphabeta.alpha_beta(state), (-20, None))


class MonteCarloTreeSearch(unittest.TestCase):
    def test_ucb1_is_the_formula_from_the_slides(self):
        node = mcts.Node(None)
        node.t, node.n = 20, 1
        self.assertAlmostEqual(mcts.ucb1(node, 2, 2), 20 + 2 * math.sqrt(math.log(2) / 1))
        node.t, node.n = 30, 4
        self.assertAlmostEqual(mcts.ucb1(node, 10, 2), 7.5 + 2 * math.sqrt(math.log(10) / 4))
        self.assertEqual(mcts.EXPLORATION, 2)

    def test_an_unvisited_child_is_tried_first(self):
        root = mcts.Node(None)
        visited, fresh = mcts.Node(None, parent=root), mcts.Node(None, parent=root)
        visited.n, visited.t, root.n = 5, 5, 5
        root.children = [visited, fresh]
        self.assertIs(mcts.best_ucb1_child(root, 2), fresh)

    def test_every_repeat_adds_one_visit_all_the_way_up(self):
        root = mcts.mcts(State(a_match()), LEFT, repeats=200, rng=random.Random(3))
        self.assertEqual(root.n, 200)
        self.assertEqual(sum(child.n for child in root.children), 200)
        self.assertEqual(len(root.children), 8)
        self.assertAlmostEqual(sum(child.t for child in root.children), root.t)
        self.assertTrue(0 <= root.t <= 200)

    def test_a_finished_leg_is_worth_one_half_or_nothing(self):
        match = a_match()
        self.assertEqual(mcts.value(State(match, towers=(20, 14)), LEFT), 1)
        self.assertEqual(mcts.value(State(match, towers=(20, 14)), RIGHT), 0)
        self.assertEqual(mcts.value(State(match, towers=(9, 9)), LEFT), 0.5)
        self.assertEqual(mcts.value(State(match, towers=(0, 20)), RIGHT), 1)

    def test_it_plays_the_move_with_the_best_average(self):
        root = mcts.Node(None)
        often, lucky = mcts.Node(None, "often", root), mcts.Node(None, "lucky", root)
        often.n, often.t = 100, 60
        lucky.n, lucky.t = 10, 9
        root.children = [often, lucky]
        self.assertEqual(mcts.choose_move(root).action, "lucky")

    def test_the_same_seed_gives_the_same_move(self):
        state = State(a_match())
        first = mcts.choose_move(mcts.mcts(state, LEFT, repeats=300, rng=random.Random(9))).action
        again = mcts.choose_move(mcts.mcts(state, LEFT, repeats=300, rng=random.Random(9))).action
        self.assertEqual(first, again)

    def test_it_beats_a_side_that_plays_at_random(self):
        rng = random.Random(4)
        score = 0
        for number in range(12):
            for first in (LEFT, RIGHT):
                state = State(a_match(), player=first)
                while not terminal(state):
                    if state.player == LEFT:
                        move = mcts.choose_move(mcts.mcts(state, LEFT, repeats=300, rng=rng)).action
                    else:
                        move = rng.choice(actions(state))
                    state = result(state, move)
                score += utility(state)
        self.assertGreater(score, 0)


if __name__ == "__main__":
    unittest.main()
