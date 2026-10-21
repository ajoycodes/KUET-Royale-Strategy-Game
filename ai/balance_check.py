#!/usr/bin/env python3
"""Measure the game instead of guessing: is it fair, and how long do the brains think?

    python3 balance_check.py            the full report (about two minutes)
    python3 balance_check.py --quick    a short version

Every number in the README and in the report must come from this script.
"""
import argparse
import random
import time

from kuet_royale import alphabeta, mcts
from kuet_royale.cards import load_roster
from kuet_royale.deck_csp import build_deck
from kuet_royale.engine import list_departments, positions_without_pruning
from kuet_royale.game import LEFT, RIGHT, Match, State, actions, result, terminal, utility
from kuet_royale.grid import load_map

GRID = load_map()


def play_leg(match, first, choosers):
    state = State(match, player=first)
    while not terminal(state):
        state = result(state, choosers[state.player](state))
    return state


def play_match(match, left, right):
    """Two legs, each side starting once. Returns the left side's total score minus the right's."""
    return sum(utility(play_leg(match, first, (left, right))) for first in (LEFT, RIGHT))


def perfect(state):
    return alphabeta.alpha_beta(state)[1]


def gambler(rng, repeats=mcts.REPEATS):
    return lambda state: mcts.choose_move(mcts.mcts(state, state.player, repeats=repeats, rng=rng)).action


def at_random(rng):
    return lambda state: rng.choice(actions(state))


def matches_of(left, right, count):
    for number in range(count):
        yield Match(GRID, build_deck(load_roster(left), number * 2)[0], build_deck(load_roster(right), number * 2 + 1)[0])


def tally(scores):
    count = len(scores)
    return "left wins %3d%%, right wins %3d%%, level %3d%%   (average margin %.1f)" % (
        100 * sum(score > 0 for score in scores) // count, 100 * sum(score < 0 for score in scores) // count,
        100 * sum(score == 0 for score in scores) // count, sum(abs(score) for score in scores) / count)


def thinking_time(left, right, count):
    worst, total, positions = 0.0, 0.0, 0
    for match in matches_of(left, right, count):
        state = State(match)
        started = time.time()
        alphabeta.alpha_beta_decision(state)
        spent = time.time() - started
        worst, total, positions = max(worst, spent), total + spent, positions + alphabeta.searched
    print("  alpha-beta, first card of a leg: %.2f s on average, %.2f s at worst" % (total / count, worst))
    print("  positions looked at: %d on average, where plain minimax would need up to %d"
          % (positions // count, positions_without_pruning(State(next(matches_of(left, right, 1))))))
    rng = random.Random(1)
    started = time.time()
    for match in matches_of(left, right, count):
        mcts.mcts(State(match), LEFT, rng=rng)
    print("  MCTS, first card of a leg, %d random legs: %.2f s on average" % (mcts.REPEATS, (time.time() - started) / count))


def report(left, right, count, brains):
    names = (left.upper(), right.upper())
    print("\n%s (left) against %s (right), %d matches of two legs, decks from the CSP solver" % (names[0], names[1], count))

    scores, first_edge, level_legs = [], [], 0
    for match in matches_of(left, right, count):
        legs = [utility(play_leg(match, first, (perfect, perfect))) for first in (LEFT, RIGHT)]
        scores.append(sum(legs))
        first_edge += [legs[0], -legs[1]]
        level_legs += legs.count(0)
    print("  both sides perfect (alpha-beta):   " + tally(scores))
    print("    in one leg the side that plays first scores %+.1f on average, and %d%% of legs end level"
          % (sum(first_edge) / len(first_edge), 100 * level_legs // (2 * count)))

    if not brains:
        return
    rng = random.Random(7)
    fewer = max(10, count // 3)
    print("  alpha-beta (left) v MCTS (right):  " + tally([play_match(m, perfect, gambler(rng)) for m in matches_of(left, right, fewer)]))
    print("  MCTS (left) v alpha-beta (right):  " + tally([play_match(m, gambler(rng), perfect) for m in matches_of(left, right, fewer)]))
    print("  MCTS (left) v random (right):      " + tally([play_match(m, gambler(rng), at_random(rng)) for m in matches_of(left, right, fewer)]))
    print("  random (left) v MCTS (right):      " + tally([play_match(m, at_random(rng), gambler(rng)) for m in matches_of(left, right, fewer)]))
    print("  random v random:                   " + tally([play_match(m, at_random(rng), at_random(rng)) for m in matches_of(left, right, count * 5)]))


def main():
    parser = argparse.ArgumentParser(description="KUET Royale: fairness and thinking time")
    parser.add_argument("--quick", action="store_true")
    arguments = parser.parse_args()
    count = 20 if arguments.quick else 80
    departments = [entry["id"] for entry in list_departments()]

    print("THINKING TIME (%s against %s)" % (departments[0].upper(), departments[2].upper()))
    thinking_time(departments[0], departments[2], 5 if arguments.quick else 20)

    print("\nFAIRNESS")
    first_pair = True
    for place, left in enumerate(departments):
        for right in departments[place + 1:]:
            report(left, right, count, first_pair)       # the brains are compared on the first pairing only
            first_pair = False
    print()


if __name__ == "__main__":
    main()
