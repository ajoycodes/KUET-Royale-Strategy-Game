"""Running a whole match: decks, two legs, who thinks how, and what the screen is told.

A match is kept as a plain dictionary (the "session") that can be saved as
JSON between moves. It never stores a board position, only the moves played.
The position is rebuilt by playing those moves again, which is safe because
nothing in the rules is random.

A match has two legs. The side that plays second can always answer the other
side's card, which is an edge. So each side starts one leg and the two scores
are added.
"""
import glob
import json
import os
import random

from . import alphabeta, mcts
from .cards import COST_LEAST, COST_LIMIT, load_roster, special_of
from .deck_csp import SLOTS, build_deck, deck_from_picks
from .fuzzy import TARGET_RULES
from .game import (FINAL_STEPS, FIRST_MOVE_SPOTS, LANE_NAMES, LEFT, RIGHT, SIDE_NAMES, STEPS_PER_CARD, TOWER_DAMAGE,
                   TOWER_HEALTH, TOWER_RANGE, Match, State, describe_unit, is_legal, lane_of, result, terminal, utility)
from .grid import DATA, load_map

SHOWN_FIRST = ("cse", "eee", "me", "ce")          # the order departments are offered in
BRAINS = {
    "alphabeta": {"name": "Alpha-beta", "blurb": "Tries every card on the lane spots, to the end of the leg. The hardest to beat."},
    "mcts": {"name": "MCTS", "blurb": "Plays 1,500 random legs before each card and backs the ones that keep winning."},
    "easy": {"name": "Easy", "blurb": "MCTS with only 100 random legs before each card. The easiest to beat."},
    "human": {"name": "You", "blurb": "Click a card, then any tile on your half of the arena."},
}
EASY_REPEATS = 100
LEGS = 2


def list_departments():
    """Every department that has a card file."""
    found = []
    paths = glob.glob(os.path.join(DATA, "cards_*.json"))
    identity = lambda path: os.path.basename(path)[len("cards_"):-len(".json")]
    paths.sort(key=lambda path: (SHOWN_FIRST.index(identity(path)) if identity(path) in SHOWN_FIRST else len(SHOWN_FIRST), path))
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        found.append({"id": os.path.basename(path)[len("cards_"):-len(".json")], "short": data["department"],
                      "name": data["name"], "motto": data.get("motto", ""), "color": data.get("color", "a8bcc0"),
                      "emoji": data.get("emoji", ""), "cards": [dict(card, special=special_of(card)) for card in data["cards"]]})
    return found


def department(identity):
    for entry in list_departments():
        if entry["id"] == identity:
            return entry
    raise ValueError("no such department: %s" % identity)


def deck_rules():
    """What the troop picker and the warriors screen need to know."""
    return {"slots": list(SLOTS), "cost_least": COST_LEAST, "cost_limit": COST_LIMIT,
            "tower_health": TOWER_HEALTH, "tower_range": TOWER_RANGE, "tower_damage": TOWER_DAMAGE}


def suggest_deck(identity, seed=None):
    """A legal deck from the CSP solver, for a person who would rather not choose."""
    if seed is None:
        seed = random.randrange(1, 1000000)
    deck, _ = build_deck(load_roster(identity), seed)
    return [card["name"] for card in deck]


def new_match(left, right, left_brain="alphabeta", right_brain="mcts", seed=None, left_deck=None, right_deck=None):
    """Start a match: use a person's own picks, or build the deck with the CSP solver, and open the first leg."""
    if left_brain not in BRAINS or right_brain not in BRAINS:
        raise ValueError("a brain is one of: " + ", ".join(BRAINS))
    if seed is None:
        seed = random.randrange(1, 1000000)
    session = {"seed": seed, "sides": {}, "legs": [], "leg": 0}
    picks = {"left": left_deck, "right": right_deck}
    for place, (side, identity, brain) in enumerate((("left", left, left_brain), ("right", right, right_brain))):
        info = department(identity)
        if picks[side]:
            deck, trace = deck_from_picks(info["cards"], picks[side]), []
        else:
            deck, trace = build_deck(info["cards"], seed * 2 + place)
        session["sides"][side] = {"department": identity, "short": info["short"], "name": info["name"],
                                  "color": info["color"], "emoji": info["emoji"], "motto": info["motto"],
                                  "brain": brain, "deck": [card["name"] for card in deck], "deck_trace": trace,
                                  "picked": bool(picks[side])}
    for number in range(LEGS):
        session["legs"].append({"first": SIDE_NAMES[number % 2], "moves": [], "analysis": []})
    return session


def match_of(session):
    decks = []
    for side in SIDE_NAMES:
        cards = {card["name"]: card for card in load_roster(session["sides"][side]["department"])}
        decks.append([cards[name] for name in session["sides"][side]["deck"]])
    return Match(load_map(), decks[0], decks[1])


def replay(session, leg_number=None, log_last=False):
    """Rebuild the position of a leg by playing its moves again.

    Returns (state, log). With log_last, log holds the battle steps that
    followed the last move, for the screen; the memory of where each unit was
    heading is carried through all the earlier moves so that only new
    decisions are reported.
    """
    if leg_number is None:
        leg_number = session["leg"]
    leg = session["legs"][leg_number]
    state = State(match_of(session), player=SIDE_NAMES.index(leg["first"]))
    memory = {}
    log = []
    moves = leg["moves"]
    for place, move in enumerate(moves):
        wanted = log_last and place == len(moves) - 1
        steps = []
        state = result(state, tuple(move), steps, memory)
        if wanted:
            log = steps
    return state, log


def leg_score(session, leg_number):
    """(left tower, right tower) of a finished leg, or None while it is still being played."""
    state, _ = replay(session, leg_number)
    if not terminal(state):
        return None
    return state.towers


def describe_action(match, side, action):
    card = match.decks[side][action[0]]
    tile = match.drops[side][action[1]]
    lane = lane_of(tile)
    where = "middle" if lane == "middle" else lane + " lane"
    if action[1] in FIRST_MOVE_SPOTS[len(LANE_NAMES):]:
        where += ", front"
    elif action[1] not in FIRST_MOVE_SPOTS:
        where += ", on the " + match.grid.kind(tile)
    return {"card": card["name"], "icon": card["icon"], "index": action[0], "spot": action[1], "lane": lane,
            "tile": list(tile), "where": where}


def think(session, state, brain, rng):
    """Let a brain pick a move. Returns (action, thinking), thinking being what the screen shows."""
    match = state.match
    side = state.player
    if brain == "alphabeta":
        action, value, table = alphabeta.alpha_beta_decision(state)
        searched, pruned = alphabeta.searched, alphabeta.pruned
        rows = []
        for move, score, exact, positions in table:
            row = describe_action(match, side, move)
            row.update({"score": score, "exact": exact, "chosen": move == action, "positions": positions})
            rows.append(row)
        line = best_line(state, action, 3)
        # The best first; of the others, the ones the search finished looking at before the ones it cut short.
        rows.sort(key=lambda row: (not row["chosen"], not row["exact"], -row["score"] if side == LEFT else row["score"]))
        return action, {"algorithm": "alphabeta", "side": SIDE_NAMES[side], "choices": rows, "value": value,
                        "searched": searched, "pruned": pruned, "line": line,
                        "plain_minimax": positions_without_pruning(state)}
    repeats = EASY_REPEATS if brain == "easy" else mcts.REPEATS
    root = mcts.mcts(state, side, repeats=repeats, rng=rng)
    chosen = mcts.choose_move(root)
    rows = []
    for child in root.children:
        row = describe_action(match, side, child.action)
        row.update({"visits": child.n, "average": round(child.t / child.n, 3) if child.n else 0.0,
                    "chosen": child is chosen})
        rows.append(row)
    rows.sort(key=lambda row: (not row["chosen"], -row["average"]))
    return chosen.action, {"algorithm": "mcts", "side": SIDE_NAMES[side], "choices": rows,
                           "repeats": repeats, "exploration": mcts.EXPLORATION}


def best_line(state, action, length):
    """The moves both sides would play next as alpha-beta sees it, starting with `action`.

    This is what alpha-beta expects to happen; the screen shows it as the
    chosen branch of the search tree.
    """
    line = []
    while action is not None and len(line) < length:
        line.append(dict(describe_action(state.match, state.player, action), side=SIDE_NAMES[state.player]))
        state = result(state, action)
        if terminal(state):
            break
        action = alphabeta.alpha_beta(state)[1]
    return line


def positions_without_pruning(state):
    """How many positions plain minimax would look at from here, if no leg ended early.

    The move being chosen offers the lanes and the front of the lanes for every
    card in hand; deeper down each turn offers the two lanes, and the hand
    shrinks by one card each time.
    """
    hands = [len(state.match.decks[side]) - bin(state.used[side]).count("1") for side in (LEFT, RIGHT)]
    side = state.player
    total, layer = 1, 1
    spots = len(FIRST_MOVE_SPOTS)
    while hands[side] > 0:
        layer *= spots * hands[side]
        total += layer
        hands[side] -= 1
        side = 1 - side
        spots = len(LANE_NAMES)
    return total


def value_of(state):
    """The score of a position with best play among the moves the search tries (by alpha-beta)."""
    if terminal(state):
        return utility(state)
    return alphabeta.alpha_beta(state)[0]


def step(session, card=None, lane=None, spot=None):
    """Play the next card of the current leg.

    With a card and a spot (or a lane) it is the human's move; otherwise the
    brain of the side to play thinks. Returns a reply for the screen.
    """
    state, _ = replay(session)
    if terminal(state):
        raise ValueError("this leg is over")
    leg = session["legs"][session["leg"]]
    match = state.match
    side = state.player
    brain = session["sides"][SIDE_NAMES[side]]["brain"]
    rng = random.Random(session["seed"] * 1000 + session["leg"] * 100 + state.plays)

    thinking = None
    if card is not None:
        action = (int(card), int(spot) if spot is not None else LANE_NAMES.index(lane))
        if not is_legal(state, action):
            raise ValueError("that card cannot be played")
        thinking = {"algorithm": "human", "side": SIDE_NAMES[side], "choices": []}
    elif brain == "human":
        raise ValueError("it is your turn: choose a card and a lane")
    else:
        action, thinking = think(session, state, brain, rng)

    # How good was the move? Compare the perfect-play score before and after it.
    if thinking["algorithm"] == "alphabeta":
        before, best_action = thinking["value"], action
    else:
        best_action, before, _ = alphabeta.alpha_beta_decision(state)
    known = {unit[0]: (match.decks[unit[1]][unit[2]]["name"], SIDE_NAMES[unit[1]]) for unit in state.units}
    known[state.plays] = (match.decks[side][action[0]]["name"], SIDE_NAMES[side])
    leg["moves"].append(list(action))
    after_state, log = replay(session, log_last=True)
    after = value_of(after_state)
    # A person's drop on a tile the search does not try can turn out better than its best: nothing was lost.
    lost = max(0, (before - after) if side == LEFT else (after - before))
    leg["analysis"].append({"play": state.plays + 1, "side": SIDE_NAMES[side], "move": describe_action(match, side, action),
                            "best": describe_action(match, side, best_action), "before": before, "after": after,
                            "lost": lost})

    spawned = after_state.plays - 1
    start = match.drops[side][action[1]]
    deployed = describe_unit(match, (spawned, side, action[0], start[0], start[1], match.decks[side][action[0]]["health"], 0))
    return {"ok": True, "thinking": thinking, "move": dict(describe_action(match, side, action), side=SIDE_NAMES[side]),
            "deployed": deployed, "steps": log, "comments": commentary(session, match, side, action, log, known),
            "view": view(session)}


def next_leg(session):
    """Open the second leg once the first is over."""
    state, _ = replay(session)
    if not terminal(state):
        raise ValueError("the current leg is still being played")
    if session["leg"] + 1 >= LEGS:
        raise ValueError("the match is over")
    session["leg"] += 1
    return {"ok": True, "view": view(session)}


def hint(session):
    """What alpha-beta would play here, for a human who asks."""
    state, _ = replay(session)
    if terminal(state):
        raise ValueError("this leg is over")
    action, thinking = think(session, state, "alphabeta", None)
    return {"ok": True, "hint": describe_action(state.match, state.player, action), "thinking": thinking}


def commentary(session, match, side, action, log, known):
    """One plain sentence per notable thing that happened after a card was played.

    known maps a unit's number to (card name, side name) for every unit on the map.
    """
    names = {name: session["sides"][name]["short"] for name in SIDE_NAMES}
    leg = session["legs"][session["leg"]]
    at_tower = leg.setdefault("at_tower", [])               # units already announced as hitting a tower
    card = match.decks[side][action[0]]
    lines = [{"step": -1, "text": "%s plays %s in the %s." % (names[SIDE_NAMES[side]], card["name"], describe_action(match, side, action)["where"])}]
    for place, entry in enumerate(log):
        for search in entry["searches"]:
            if "cheapest_cost" in search and search["cost"] > search["cheapest_cost"]:
                lines.append({"step": place, "text": "%s takes the greedy route: it costs %d where A* would pay %d."
                              % (known[search["unit"]][0], search["cost"], search["cheapest_cost"])})
        for attack in entry["attacks"]:
            if attack["target"] == "tower" and attack["unit"] not in at_tower:
                at_tower.append(attack["unit"])
                name, owner = known[attack["unit"]]
                lines.append({"step": place, "text": "%s reaches %s's tower and starts hitting it."
                              % (name, names["right" if owner == "left" else "left"])})
        for number in entry["dead"]:
            name, owner = known[number]
            lines.append({"step": place, "text": "%s's %s is out." % (names[owner], name)})
    return lines


def turning_point(session, leg_number):
    """The one card that cost its side the most, measured against perfect play. None if nobody slipped."""
    worst = None
    for entry in session["legs"][leg_number]["analysis"]:
        if entry["lost"] > 0 and (worst is None or entry["lost"] > worst["lost"]):
            worst = entry
    return worst


def view(session):
    """Everything the screen needs to draw the match as it stands."""
    state, _ = replay(session)
    match = state.match
    leg = session["legs"][session["leg"]]
    sides = {}
    for index, side in enumerate(SIDE_NAMES):
        info = session["sides"][side]
        deck = []
        for place, card in enumerate(match.decks[index]):
            shown = dict(card)
            shown["index"] = place
            shown["special"] = special_of(card)
            shown["used"] = bool(state.used[index] >> place & 1)
            deck.append(shown)
        sides[side] = {"department": info["department"], "short": info["short"], "name": info["name"],
                       "color": info["color"], "emoji": info["emoji"], "motto": info["motto"],
                       "brain": info["brain"], "brain_name": BRAINS[info["brain"]]["name"],
                       "brain_blurb": BRAINS[info["brain"]]["blurb"], "deck": deck, "deck_trace": info["deck_trace"],
                       "picked": bool(info.get("picked", False)), "drops": [list(tile) for tile in match.drops[index]],
                       "deck_cost": sum(card["cost"] for card in match.decks[index]),
                       "tower": state.towers[index], "tower_tile": list(match.tower_tile[index]),
                       "starts": {lane: list(match.starts[index][place]) for place, lane in enumerate(LANE_NAMES)}}

    legs = []
    total = [0, 0]
    for number in range(LEGS):
        score = leg_score(session, number) if number <= session["leg"] else None
        entry = {"number": number + 1, "first": session["legs"][number]["first"], "finished": score is not None}
        if score is not None:
            entry["towers"] = {"left": score[LEFT], "right": score[RIGHT]}
            entry["damage"] = {"left": TOWER_HEALTH - score[RIGHT], "right": TOWER_HEALTH - score[LEFT]}
            total[LEFT] += TOWER_HEALTH - score[RIGHT]
            total[RIGHT] += TOWER_HEALTH - score[LEFT]
            point = turning_point(session, number)
            entry["turning_point"] = point
        legs.append(entry)

    leg_over = terminal(state)
    match_over = leg_over and session["leg"] == LEGS - 1
    winner = None
    if match_over:
        winner = "left" if total[LEFT] > total[RIGHT] else "right" if total[RIGHT] > total[LEFT] else "draw"
    return {
        "seed": session["seed"],
        "leg": session["leg"] + 1,
        "legs": legs,
        "first": leg["first"],
        "play": state.plays,
        "plays": match.total_plays,
        "to_move": None if leg_over else SIDE_NAMES[state.player],
        "leg_over": leg_over,
        "match_over": match_over,
        "winner": winner,
        "damage": {"left": total[LEFT], "right": total[RIGHT]},
        "sides": sides,
        "units": [describe_unit(match, unit) for unit in state.units],
        "map": {"name": match.grid.name, "rows": match.grid.rows, "width": match.grid.width, "height": match.grid.height,
                "kinds": match.grid.kinds},
        "rules": {"tower_health": TOWER_HEALTH, "tower_range": TOWER_RANGE, "tower_damage": TOWER_DAMAGE,
                  "steps_per_card": STEPS_PER_CARD, "final_steps": FINAL_STEPS, "legs": LEGS,
                  "cost_least": COST_LEAST, "cost_limit": COST_LIMIT, "slots": list(SLOTS), "fuzzy": TARGET_RULES},
    }
