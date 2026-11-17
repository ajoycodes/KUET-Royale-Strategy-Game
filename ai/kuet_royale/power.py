"""Power mode: one minute of dropping warriors, with no turns.

    Each side holds four of its department's eight cards. A played card goes to
    the back of the queue and the next one comes into the hand, so all eight are
    in rotation.
    A card costs coins. A side starts with some, earns more with time, and can
    never hold more than COINS_MOST.
    The clock is counted in beats, and one beat is one battle step. In a beat each
    side may drop one card, whoever it is, and neither waits for the other.
    The match ends when the clock runs out or a tower falls. The side that did
    more damage to the enemy tower wins.

The two brains are the same alpha-beta and MCTS code as the classic game: only
the rules they are given change. Searching a whole minute is far too big, so a
brain looks at a short window of the fight and cuts its search off there. The
end of the window is scored with a very simple evaluation function: how much
the towers changed, plus a large bonus if one fell. Alpha-beta looks at two drops
by each side, one beat apart, and then lets the fight run to the end of the
window. MCTS plays random games to the end of the window, with drops on both sides.
"""
import random
import sys

from . import alphabeta, mcts
from .cards import load_roster, special_of
from .engine import BRAINS, department, describe_action
from .game import (FIRST_MOVE_SPOTS, LEFT, RIGHT, SIDE_NAMES, TOWER_DAMAGE, TOWER_HEALTH, TOWER_RANGE, Match,
                   battle_step, describe_unit)
from .grid import load_map

BEATS = 100                 # one minute, at a beat of BEAT_SECONDS on the screen
BEAT_SECONDS = 0.6
HAND = 4
COINS_START = 5
COINS_MOST = 10
COIN_EVERY = 3              # beats per coin earned
WINDOW = 30                 # beats ahead a brain looks
FREE_DECISIONS = 4          # alpha-beta's look ahead: mine, the reply, mine, the reply; then the fight just runs
FALLEN_TOWER = 100          # a fallen tower ends the match, so it outweighs any change in health
DECIDE_EVERY = 2            # a brain thinks every second beat, to keep a beat short
MCTS_REPEATS = 150
EASY_POWER_REPEATS = 30
WAIT = (-1, -1)             # the move of not dropping anything


class Window:
    """A power match as a brain imagines it: who decides next, and how much time is left to look at."""
    __slots__ = ("match", "units", "towers", "coins", "queues", "beat", "end", "player", "plays", "free", "start")

    def __init__(self, match, units, towers, coins, queues, beat, end, player, plays, free, start):
        self.match = match
        self.units = units
        self.towers = towers
        self.coins = coins          # (left, right)
        self.queues = queues        # for each side, its cards in order; the first HAND are the hand
        self.beat = beat
        self.end = end              # the beat this window ends on
        self.player = player        # who decides next
        self.plays = plays          # units dropped so far; also the number of the next unit
        self.free = free            # decisions that may still drop a card; None means no limit
        self.start = start          # left tower minus right tower when the window opened


# ---------------------------------------------------------- the rules a brain is given

def actions(state):
    """Waiting, then every card in hand the side can pay for, in the lanes or at their front.

    Waiting comes first because alpha-beta keeps the first of equally good moves:
    this way it spends coins only when a drop really changes the score.
    """
    side = state.player
    coins = state.coins[side]
    deck = state.match.decks[side]
    return [WAIT] + [(card, spot) for card in state.queues[side][:HAND] if deck[card]["cost"] <= coins for spot in FIRST_MOVE_SPOTS]


first_moves = actions


def terminal(state):
    return state.beat >= state.end or state.towers[LEFT] <= 0 or state.towers[RIGHT] <= 0


def utility(state):
    """The score at the end of the window: how far left tower minus right tower has moved since it opened."""
    left, right = state.towers
    score = left - right - state.start
    if left <= 0 < right:
        return score - FALLEN_TOWER
    if right <= 0 < left:
        return score + FALLEN_TOWER
    return score


def _with_drop(match, units, coins, queues, plays, side, action):
    card, spot = action
    x, y = match.drops[side][spot]
    units = units + ((plays, side, card, x, y, match.decks[side][card]["health"], 0),)
    if side == LEFT:
        coins = (coins[LEFT] - match.decks[side][card]["cost"], coins[RIGHT])
    else:
        coins = (coins[LEFT], coins[RIGHT] - match.decks[side][card]["cost"])
    queue = queues[side]
    queue = tuple(entry for entry in queue if entry != card) + (card,)
    queues = (queue, queues[RIGHT]) if side == LEFT else (queues[LEFT], queue)
    return units, coins, queues


def _earned(coins, beat):
    if beat % COIN_EVERY == 0:
        return (min(COINS_MOST, coins[LEFT] + 1), min(COINS_MOST, coins[RIGHT] + 1))
    return coins


def result(state, action):
    match = state.match
    side = state.player
    units, coins, queues, plays = state.units, state.coins, state.queues, state.plays
    if action != WAIT:
        units, coins, queues = _with_drop(match, units, coins, queues, plays, side, action)
        plays += 1
    free = None if state.free is None else state.free - 1
    # The fight goes on for one beat, or to the end of the window if no more drops may come. Then the other side decides.
    towers = state.towers
    beat = state.beat
    while True:
        units, towers = battle_step(match, units, towers)
        beat += 1
        coins = _earned(coins, beat)
        if free is None or free > 0 or beat >= state.end or towers[LEFT] <= 0 or towers[RIGHT] <= 0:
            break
    return Window(match, units, towers, coins, queues, beat, state.end, 1 - side, plays, free, state.start)


_RULES = sys.modules[__name__]


# ---------------------------------------------------------------- a match

def _match_of(session):
    decks = [load_roster(session["sides"][side]["department"]) for side in SIDE_NAMES]
    return Match(load_map(), decks[LEFT], decks[RIGHT])


def new_match(left, right, left_brain="alphabeta", right_brain="mcts", seed=None):
    if left_brain not in BRAINS or right_brain not in BRAINS:
        raise ValueError("a brain is one of: " + ", ".join(BRAINS))
    if seed is None:
        seed = random.randrange(1, 1000000)
    session = {"mode": "power", "seed": seed, "sides": {}, "units": [], "towers": [TOWER_HEALTH, TOWER_HEALTH],
               "coins": [COINS_START, COINS_START], "queues": [], "beat": 0, "plays": 0, "memory": {}}
    for place, (side, identity, brain) in enumerate((("left", left, left_brain), ("right", right, right_brain))):
        info = department(identity)
        order = list(range(len(info["cards"])))
        random.Random(seed * 2 + place).shuffle(order)
        session["queues"].append(order)
        session["sides"][side] = {"department": identity, "short": info["short"], "name": info["name"],
                                  "color": info["color"], "emoji": info["emoji"], "motto": info["motto"], "brain": brain}
    return session


def _hand_of(match, session, side):
    """The cards in a side's hand and the next one to come, for the screen."""
    queue = session["queues"][side]
    shown = []
    for card in queue[:HAND]:
        entry = dict(match.decks[side][card])
        entry["index"] = card
        entry["used"] = False
        entry["special"] = special_of(entry)
        shown.append(entry)
    return shown, match.decks[side][queue[HAND]]["name"]


def _winner(session):
    left, right = session["towers"]
    return "left" if left > right else "right" if right > left else "draw"


def is_over(session):
    return session["beat"] >= BEATS or session["towers"][LEFT] <= 0 or session["towers"][RIGHT] <= 0


def view(session):
    match = _match_of(session)
    sides = {}
    for index, side in enumerate(SIDE_NAMES):
        info = session["sides"][side]
        hand, upcoming = _hand_of(match, session, index)
        sides[side] = {"department": info["department"], "short": info["short"], "name": info["name"],
                       "color": info["color"], "emoji": info["emoji"], "motto": info["motto"],
                       "brain": info["brain"], "brain_name": BRAINS[info["brain"]]["name"],
                       "brain_blurb": POWER_BLURB[info["brain"]], "hand": hand, "next": upcoming,
                       "coins": session["coins"][index], "tower": session["towers"][index],
                       "tower_tile": list(match.tower_tile[index]), "drops": [list(tile) for tile in match.drops[index]],
                       "starts": {"top": list(match.starts[index][0]), "bottom": list(match.starts[index][1])}}
    over = is_over(session)
    return {"mode": "power", "seed": session["seed"], "beat": session["beat"], "beats": BEATS, "beat_seconds": BEAT_SECONDS,
            "seconds_left": max(0, round((BEATS - session["beat"]) * BEAT_SECONDS)), "over": over,
            "winner": _winner(session) if over else None, "sides": sides,
            "damage": {"left": TOWER_HEALTH - session["towers"][RIGHT], "right": TOWER_HEALTH - session["towers"][LEFT]},
            "map": {"name": match.grid.name, "rows": match.grid.rows, "width": match.grid.width, "height": match.grid.height,
                    "kinds": match.grid.kinds},
            "rules": {"tower_health": TOWER_HEALTH, "tower_range": TOWER_RANGE, "tower_damage": TOWER_DAMAGE,
                      "coins_most": COINS_MOST, "coin_every": COIN_EVERY}}


POWER_BLURB = {
    "alphabeta": "Tries two drops by each side, then lets the fight run to the end of a short window.",
    "mcts": "Plays %d random games of the next few seconds before it drops." % MCTS_REPEATS,
    "easy": "MCTS with only %d random games. The easiest to beat." % EASY_POWER_REPEATS,
    "human": "Click a card, then any tile on your half, whenever you can pay for it.",
}


def _window(match, session, side, free):
    return Window(match, tuple(tuple(unit) for unit in session["units"]), tuple(session["towers"]), tuple(session["coins"]),
                  tuple(tuple(queue) for queue in session["queues"]), session["beat"], min(BEATS, session["beat"] + WINDOW),
                  side, session["plays"], free, session["towers"][LEFT] - session["towers"][RIGHT])


def _row(match, side, action):
    if action == WAIT:
        return {"card": "Hold on", "icon": "", "index": -1, "spot": -1, "lane": "middle", "tile": [0, 0], "where": "no card this time"}
    return describe_action(match, side, action)


def think(match, session, side, brain, rng):
    """Let a brain choose a drop, or to wait. Returns (action, thinking), in the same shape as the classic game."""
    if brain == "alphabeta":
        action, value, table = alphabeta.alpha_beta_decision(_window(match, session, side, FREE_DECISIONS), _RULES)
        rows = []
        for move, score, exact, positions in table:
            row = _row(match, side, move)
            row.update({"score": score, "exact": exact, "chosen": move == action, "positions": positions})
            rows.append(row)
        rows.sort(key=lambda row: (not row["chosen"], not row["exact"], -row["score"] if side == LEFT else row["score"]))
        return action, {"algorithm": "alphabeta", "side": SIDE_NAMES[side], "choices": rows, "value": value,
                        "searched": alphabeta.searched, "pruned": alphabeta.pruned,
                        "heading": "Alpha-beta: tower swing each drop can reach",
                        "note": "Looked at %d positions and skipped %d moves, for the next %d beats of the fight. A fallen tower counts %d extra." % (
                            alphabeta.searched, alphabeta.pruned, WINDOW, FALLEN_TOWER)}
    repeats = EASY_POWER_REPEATS if brain == "easy" else MCTS_REPEATS
    root = mcts.mcts(_window(match, session, side, None), side, repeats=repeats, rng=rng, rules=_RULES)
    chosen = mcts.choose_move(root)
    rows = []
    for child in root.children:
        row = _row(match, side, child.action)
        row.update({"visits": child.n, "average": round(child.t / child.n, 3) if child.n else 0.0, "chosen": child is chosen})
        rows.append(row)
    rows.sort(key=lambda row: (not row["chosen"], -row["average"]))
    return chosen.action, {"algorithm": "mcts", "side": SIDE_NAMES[side], "choices": rows, "repeats": repeats,
                           "exploration": mcts.EXPLORATION,
                           "heading": "MCTS: random games each drop won",
                           "note": "Played %d random games of the next %d beats and backed the move that won most often." % (repeats, WINDOW)}


def _person_drop(drops, side):
    """A person's drop for this beat, given as "left:CARD:SPOT"."""
    for text in drops:
        name, card, spot = text.split(":")
        if name == SIDE_NAMES[side]:
            return (int(card), int(spot))
    return None


def _can_drop(match, session, side, action):
    card, spot = action
    return (card in session["queues"][side][:HAND] and match.decks[side][card]["cost"] <= session["coins"][side]
            and 0 <= spot < len(match.drops[side]))


def beat(session, drops=()):
    """One beat: each side may drop a card, then the units fight for one battle step."""
    if is_over(session):
        raise ValueError("this match is over")
    match = _match_of(session)
    chosen = {}
    thinking = {}
    refused = []
    for side in (LEFT, RIGHT):
        name = SIDE_NAMES[side]
        brain = session["sides"][name]["brain"]
        if brain == "human":
            action = _person_drop(drops, side)
            if action is not None:
                if _can_drop(match, session, side, action):
                    chosen[side] = action
                else:
                    refused.append(name)
        elif session["beat"] % DECIDE_EVERY == 0:
            # It looks only when it could pay for any card in its hand, or the dear ones would never get played.
            dearest = max(match.decks[side][card]["cost"] for card in session["queues"][side][:HAND])
            if dearest <= session["coins"][side]:
                rng = random.Random(session["seed"] * 1000 + session["beat"] * 10 + side)
                action, thinking[name] = think(match, session, side, brain, rng)
                if action != WAIT:
                    chosen[side] = action

    units = tuple(tuple(unit) for unit in session["units"])
    coins = tuple(session["coins"])
    queues = tuple(tuple(queue) for queue in session["queues"])
    plays = session["plays"]
    deployed = []
    for side in (LEFT, RIGHT):
        if side in chosen:
            units, coins, queues = _with_drop(match, units, coins, queues, plays, side, chosen[side])
            deployed.append(dict(describe_unit(match, units[-1]), move=describe_action(match, side, chosen[side])))
            plays += 1

    log = []
    memory = {int(number): tuple(goal) for number, goal in session["memory"].items()}
    units, towers = battle_step(match, units, tuple(session["towers"]), log, memory)
    session["beat"] += 1
    session["units"] = [list(unit) for unit in units]
    session["towers"] = list(towers)
    session["coins"] = list(_earned(coins, session["beat"]))
    session["queues"] = [list(queue) for queue in queues]
    session["plays"] = plays
    session["memory"] = {str(number): list(goal) for number, goal in memory.items()}
    return {"ok": True, "deployed": deployed, "step": log[0], "thinking": thinking, "refused": refused, "view": view(session)}


def play_out(session):
    """Play a match with no people in it to the end. Used by the balance check and the tests."""
    while not is_over(session):
        beat(session)
    return _winner(session)
