"""Alpha-beta search: the Lab 04 minimax program with the two bounds from the theory class.

    alpha = the best score the left side (MAX) is already sure of
    beta  = the best score the right side (MIN) is already sure of

When a branch cannot change the final choice any more, the rest of it is
skipped. The answer is exactly the one plain minimax would give.

In the classic game the search runs to the end of the leg, with no depth limit
and no evaluation function: utility() reads the score off a finished leg. Power
mode passes its own rules, which stop at the end of a short window.
"""
import math

from . import game
from .game import LEFT

searched = 0        # positions looked at, counted for the screen
pruned = 0          # moves skipped because they could not matter


def max_value(state, alpha, beta, rules=game):
    global searched, pruned
    searched += 1
    if rules.terminal(state):
        return rules.utility(state), None
    v = -math.inf
    best_action = None
    moves = rules.actions(state)
    for place, action in enumerate(moves):
        value, _ = min_value(rules.result(state, action), alpha, beta, rules)
        if value > v:
            v = value
            best_action = action
        if v >= beta:
            pruned += len(moves) - place - 1
            return v, best_action           # MIN would never let the match come here
        alpha = max(alpha, v)
    return v, best_action


def min_value(state, alpha, beta, rules=game):
    global searched, pruned
    searched += 1
    if rules.terminal(state):
        return rules.utility(state), None
    v = math.inf
    best_action = None
    moves = rules.actions(state)
    for place, action in enumerate(moves):
        value, _ = max_value(rules.result(state, action), alpha, beta, rules)
        if value < v:
            v = value
            best_action = action
        if v <= alpha:
            pruned += len(moves) - place - 1
            return v, best_action           # MAX would never let the match come here
        beta = min(beta, v)
    return v, best_action


def alpha_beta(state):
    """Returns (value, best_action) for the side to play."""
    if state.player == LEFT:
        return max_value(state, -math.inf, math.inf)
    return min_value(state, -math.inf, math.inf)


def alpha_beta_decision(state, rules=game):
    """The same search, keeping what it learned about every first move, for the screen.

    Returns (best_action, value, table). Each table row is
    (action, score, exact, positions). exact is False when the search stopped
    looking at that move early: the score is then only a limit ("no better
    than this"), which was enough to know the move is not the best.
    positions is how many positions the search looked at below that move.
    """
    global searched, pruned
    searched = 1
    pruned = 0
    left = state.player == LEFT
    alpha, beta = -math.inf, math.inf
    best_action, best = None, None
    table = []
    for action in rules.first_moves(state):
        child = rules.result(state, action)
        before = searched
        if left:
            value, _ = min_value(child, alpha, beta, rules)
            exact = value > alpha
            if best is None or value > best:
                best, best_action = value, action
            alpha = max(alpha, value)
        else:
            value, _ = max_value(child, alpha, beta, rules)
            exact = value < beta
            if best is None or value < best:
                best, best_action = value, action
            beta = min(beta, value)
        table.append((action, value, exact, searched - before))
    return best_action, best, table
