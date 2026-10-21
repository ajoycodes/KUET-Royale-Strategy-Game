"""Lab 08: Monte Carlo Tree Search, written from the lab's flowchart and pseudocode.

The four steps, repeated x times:

    1. Selection        walk down from the root, always to the child with the highest UCB1
    2. Expansion        at a visited leaf, add a child for every available action
    3. Simulation       play random cards from there until the match ends (the rollout)
    4. Backpropagation  add the result to every node on the way back up

    UCB1(S_i) = t_i / n_i  +  C * sqrt( ln N / n_i )

    t_i = total value of node S_i        n_i = number of visits to node S_i
    N   = number of simulations from the parent node        C = exploration constant

The slides stop before saying a few things. Those choices are ours, and they are
marked "OUR CHOICE" below so nobody mistakes them for course material:
  * which move to finally play
  * how many times to repeat
  * what to do when the walk reaches a finished match
  * what a finished match is worth (1 for a win, 0.5 for a draw, 0 for a loss, to the side searching)

Nothing was added for the opponent, because the lab taught nothing about one.
The same value is added at every level of the tree, so this search imagines
that the other side will be helpful. It gambles, and that is why it can lose
to alpha-beta.
"""
import math
import random

from .game import LEFT, actions, result, terminal, utility

EXPLORATION = 2    # C. The lab's worked example uses C = 2.
REPEATS = 1500     # x. OUR CHOICE: the slides only say "repeated x times".


class Node:
    def __init__(self, state, action=None, parent=None):
        self.state = state
        self.action = action     # the move that led to this state
        self.parent = parent
        self.children = []
        self.n = 0               # number of visits
        self.t = 0               # total value


def value(state, seat):
    """OUR CHOICE: what a finished match is worth to the side doing the search."""
    score = utility(state) if seat == LEFT else -utility(state)
    if score > 0:
        return 1
    if score < 0:
        return 0
    return 0.5


def ucb1(node, N, C):
    return node.t / node.n + C * math.sqrt(math.log(N) / node.n)


def best_ucb1_child(node, C):
    for child in node.children:
        if child.n == 0:
            return child           # an unvisited child is tried before any UCB1 is compared (slides 7-8)
    best, best_score = None, -math.inf
    for child in node.children:
        score = ucb1(child, node.n, C)
        if score > best_score:
            best, best_score = child, score
    return best


def add_children(node):
    """For each available action from this node, add a new state to the tree."""
    for action in actions(node.state):
        node.children.append(Node(result(node.state, action), action, node))


def rollout(state, seat, rng):
    while True:
        if terminal(state):
            return value(state, seat)
        action = rng.choice(actions(state))
        state = result(state, action)


def backpropagate(node, v):
    while node is not None:
        node.n += 1
        node.t += v
        node = node.parent


def mcts(state, seat, repeats=REPEATS, C=EXPLORATION, rng=random):
    """Build the search tree for the side in `seat` and return its root."""
    root = Node(state)
    add_children(root)             # as on slide 7, where the root already has its actions drawn at N = 0

    for _ in range(repeats):
        # 1. Selection: is current a leaf node? If not, move to the child that maximizes UCB1.
        current = root
        while current.children:
            current = best_ucb1_child(current, C)

        # 2. Expansion: a leaf that was visited before gets a child for every action.
        if current.n > 0 and not terminal(current.state):
            add_children(current)
            current = current.children[0]      # current = first new child node
        # OUR CHOICE: a visited leaf that is already a finished match cannot be
        # expanded, so its final value is simply read again.

        # 3. Simulation
        v = rollout(current.state, seat, rng)

        # 4. Backpropagation
        backpropagate(current, v)

    return root


def choose_move(root):
    """OUR CHOICE: play the move with the best average result, t / n.

    That is the "exploitation" half of UCB1. Ties keep the first move.
    """
    best, best_average = None, -math.inf
    for child in root.children:
        if child.n > 0 and child.t / child.n > best_average:
            best, best_average = child, child.t / child.n
    return best
