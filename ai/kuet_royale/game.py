"""The rules of a match, in the shape of the Lab 04 program.

    State                 a snapshot of the match
    actions(state)        the moves the side to play may make
    result(state, action) the snapshot after that move and the fighting that follows
    terminal(state)       is the match over?
    utility(state)        the final score: left tower health minus right tower health

A move is (card, lane): which unused card of the deck, and 0 for the top lane
or 1 for the bottom lane. The left side plays first and wants the score high.
The right side wants it low.

Nothing here is random, nothing is hidden, and the sides strictly take turns,
so the searches of the course can be used exactly as taught.
"""
from . import fuzzy
from .routes import CAREFUL, HOVER, RECKLESS, ROUTE_SEARCH, SPREAD_SEARCH, STYLES, Routes

LEFT, RIGHT = 0, 1
SIDE_NAMES = ("left", "right")
LANE_NAMES = ("top", "bottom")

TOWER_HEALTH = 20
TOWER_RANGE = 2          # a tower hits the closest enemy within this many tiles ...
TOWER_DAMAGE = 2         # ... for this much, once per battle step
STEPS_PER_CARD = 3       # battle steps after each card
FINAL_STEPS = 15         # extra battle steps after the last card

# A unit is a tuple, so that snapshots are cheap to make:
#     (number, side, card, x, y, health, points)
# "points" are movement points saved up towards a tile the unit could not yet afford.
NUMBER, SIDE, CARD, X, Y, HEALTH, POINTS = range(7)

_routes = {}             # one notebook of search answers per map


class Match:
    """Everything that stays the same from the first card to the last."""

    def __init__(self, grid, left_deck, right_deck):
        self.grid = grid
        if grid.name not in _routes:
            _routes[grid.name] = Routes(grid)
        self.routes = _routes[grid.name]
        self.decks = (left_deck, right_deck)
        self.styles = tuple([STYLES[card["walks"]] for card in deck] for deck in self.decks)
        self.tower_tile = (grid.tower("left"), grid.tower("right"))
        # A unit attacks a tower from a tile next to it.
        self.tower_front = tuple(frozenset(grid.neighbours(tile)) for tile in self.tower_tile)
        self.starts = tuple(tuple(grid.start(side, lane) for lane in LANE_NAMES) for side in SIDE_NAMES)
        self.cost = {tile: grid.cost(tile) for tile in grid.tiles() if grid.passable(tile)}
        self.total_plays = len(left_deck) + len(right_deck)


class State:
    def __init__(self, match, units=(), towers=(TOWER_HEALTH, TOWER_HEALTH), used=(0, 0),
                 player=LEFT, plays=0, steps=0):
        self.match = match
        self.units = units          # every unit on the map, oldest first
        self.towers = towers        # (left tower health, right tower health)
        self.used = used            # per side, one bit per card already played
        self.player = player        # whose turn it is to play a card
        self.plays = plays          # cards played so far; also the number of the next unit
        self.steps = steps          # battle steps fought so far


def actions(state):
    """Every unused card of the side to play, into either lane."""
    used = state.used[state.player]
    deck = state.match.decks[state.player]
    return [(card, lane) for card in range(len(deck)) if not used >> card & 1 for lane in (0, 1)]


def terminal(state):
    return state.plays == state.match.total_plays or state.towers[LEFT] <= 0 or state.towers[RIGHT] <= 0


def utility(state):
    """The final score. Above 0 the left side has won, below 0 the right side, 0 is a draw."""
    return state.towers[LEFT] - state.towers[RIGHT]


def winner(state):
    score = utility(state)
    return LEFT if score > 0 else RIGHT if score < 0 else None


def result(state, action, log=None, memory=None):
    """Play the card, then let the units fight.

    log, if given, is a list that receives one entry per battle step for the
    screen. memory, if given, remembers where each unit was heading, so the
    screen is only told about a search when a unit changes its mind.
    """
    match = state.match
    card, lane = action
    side = state.player
    x, y = match.starts[side][lane]
    health = match.decks[side][card]["health"]
    units = state.units + ((state.plays, side, card, x, y, health, 0),)
    used = (state.used[0] | 1 << card, state.used[1]) if side == LEFT else (state.used[0], state.used[1] | 1 << card)
    plays = state.plays + 1
    towers = state.towers

    limit = STEPS_PER_CARD
    last_card = plays == match.total_plays
    if last_card:
        limit += FINAL_STEPS
    fought = 0
    while fought < limit and towers[LEFT] > 0 and towers[RIGHT] > 0:
        if last_card and not units:
            break                                   # nobody left to change the score
        units, towers = battle_step(match, units, towers, log, memory)
        fought += 1
    return State(match, units, towers, used, 1 - side, plays, state.steps + fought)


def battle_step(match, units, towers, log=None, memory=None):
    """One step of the fight: every unit does one thing, then the towers fire.

    Everything is decided from where units stood when the step began, and all
    damage lands together, so the order units are looked at favours nobody.
    """
    routes = match.routes
    cost_of = match.cost
    by_side = ([unit for unit in units if unit[SIDE] == LEFT], [unit for unit in units if unit[SIDE] == RIGHT])
    hurt = {}
    tower_hurt = [0, 0]
    acted = []
    entry = None
    if log is not None:
        entry = {"searches": [], "moves": [], "attacks": [], "shots": []}

    for unit in units:
        number, side, card_index, x, y, health, points = unit
        card = match.decks[side][card_index]
        style = match.styles[side][card_index]
        foe_side = 1 - side
        foes = by_side[foe_side]
        reach = card["range"]
        tower_x, tower_y = match.tower_tile[foe_side]

        # 1. Is an enemy in range? Then attack.
        choices = []                                # (foe or None for the tower, distance, health percent)
        for foe in foes:
            distance = abs(foe[X] - x) + abs(foe[Y] - y)
            if distance <= reach:
                full = match.decks[foe_side][foe[CARD]]["health"]
                choices.append((foe, distance, foe[HEALTH] * 100 // full))
        tower_distance = abs(tower_x - x) + abs(tower_y - y)
        if tower_distance <= reach:
            choices.append((None, tower_distance, towers[foe_side] * 100 // TOWER_HEALTH))

        if choices:
            target = choices[0]
            ranking = None
            if len(choices) > 1:
                # Several enemies in range: the fuzzy system says which one. The first of equals is kept.
                ranking = [fuzzy.priority(distance, percent) for _, distance, percent in choices]
                best = ranking[0]
                for place in range(1, len(choices)):
                    if ranking[place] > best:
                        best = ranking[place]
                        target = choices[place]
            foe = target[0]
            damage = card["damage"]
            splashed = []
            if foe is None:
                tower_hurt[foe_side] += damage
                centre = (tower_x, tower_y)
            else:
                hurt[foe[NUMBER]] = hurt.get(foe[NUMBER], 0) + damage
                centre = (foe[X], foe[Y])
            if card["splash"]:
                area = routes.near(centre)          # breadth-first: everything within one step
                for other in foes:
                    if other is not foe and (other[X], other[Y]) in area:
                        hurt[other[NUMBER]] = hurt.get(other[NUMBER], 0) + damage
                        splashed.append(other[NUMBER])
            acted.append((number, side, card_index, x, y, health, 0))
            if entry is not None:
                attack = {"unit": number, "target": "tower" if foe is None else foe[NUMBER],
                          "at": list(centre), "damage": damage, "splash": splashed}
                if ranking is not None:
                    attack["choices"] = []
                    for choice, score in zip(choices, ranking):
                        # The three rule strengths, so the screen can show how the priority came about.
                        strengths = fuzzy.infer(fuzzy.TARGET, {"distance": choice[1], "health": choice[2]})["strengths"]
                        attack["choices"].append({"target": "tower" if choice[0] is None else choice[0][NUMBER],
                                                  "distance": choice[1], "health": choice[2], "priority": score,
                                                  "strengths": {term: round(value, 2) for term, value in strengths.items()}})
                entry["attacks"].append(attack)
            continue

        # 2. Nobody in range: head for the enemy that is cheapest to reach.
        here = (x, y)
        goals = {(foe[X], foe[Y]) for foe in foes}
        goals.update(match.tower_front[foe_side])
        goal = routes.nearest(here, goals, style)
        if entry is not None and memory is not None and memory.get(number) != goal:
            memory[number] = goal
            entry["searches"].append(describe_search(match, number, here, goal, style))

        # 3. Walk along the route for as long as the movement points last.
        points += card["speed"]
        path = [here]
        while here != goal:
            step = routes.next_step(here, goal, style)
            price = 1 if style == HOVER else cost_of[step]
            if points < price:
                break                               # save the points for the next battle step
            points -= price
            here = step
            path.append(here)
            in_range = abs(tower_x - here[0]) + abs(tower_y - here[1]) <= reach
            if not in_range:
                for foe in foes:
                    if abs(foe[X] - here[0]) + abs(foe[Y] - here[1]) <= reach:
                        in_range = True
                        break
            if in_range:
                points = 0                          # close enough to fight: stop here
                break
        if here == goal:
            points = 0
        acted.append((number, side, card_index, here[0], here[1], health, points))
        if entry is not None and len(path) > 1:
            entry["moves"].append({"unit": number, "path": [list(tile) for tile in path]})

    # The towers fire at the closest enemy; of equals the weakest, then the oldest.
    for side in (LEFT, RIGHT):
        tower_x, tower_y = match.tower_tile[side]
        chosen = None
        for foe in by_side[1 - side]:
            distance = abs(foe[X] - tower_x) + abs(foe[Y] - tower_y)
            if distance <= TOWER_RANGE:
                key = (distance, foe[HEALTH], foe[NUMBER])
                if chosen is None or key < chosen:
                    chosen = key
        if chosen is not None:
            hurt[chosen[2]] = hurt.get(chosen[2], 0) + TOWER_DAMAGE
            if entry is not None:
                entry["shots"].append({"side": SIDE_NAMES[side], "target": chosen[2], "damage": TOWER_DAMAGE})

    # All the damage lands together.
    survivors = []
    dead = []
    for unit in acted:
        health = unit[HEALTH] - hurt.get(unit[NUMBER], 0)
        if health > 0:
            survivors.append(unit[:HEALTH] + (health, unit[POINTS]))
        else:
            dead.append(unit[NUMBER])
    towers = (max(0, towers[LEFT] - tower_hurt[LEFT]), max(0, towers[RIGHT] - tower_hurt[RIGHT]))
    units = tuple(survivors)
    if entry is not None:
        entry["dead"] = dead
        entry["hurt"] = [{"unit": number, "damage": damage} for number, damage in sorted(hurt.items())]
        entry["tower_hurt"] = {"left": tower_hurt[LEFT], "right": tower_hurt[RIGHT]}
        entry["towers"] = {"left": towers[LEFT], "right": towers[RIGHT]}
        entry["units"] = [describe_unit(match, unit) for unit in units]
        log.append(entry)
    return units, towers


def describe_unit(match, unit):
    card = match.decks[unit[SIDE]][unit[CARD]]
    return {"unit": unit[NUMBER], "side": SIDE_NAMES[unit[SIDE]], "card": card["name"], "icon": card["icon"],
            "tile": [unit[X], unit[Y]], "health": unit[HEALTH], "full": card["health"], "walks": card["walks"]}


def describe_search(match, number, start, goal, style):
    """What the screen needs to show a unit choosing a target and a route to it."""
    routes = match.routes
    route = routes.route(start, goal, style)
    answer = {
        "unit": number,
        "from": list(start),
        "goal": list(goal),
        "target_search": SPREAD_SEARCH[style],
        "target_explored": [list(tile) for tile in routes.explored_until(start, goal, style)],
        "route_search": ROUTE_SEARCH[style],
        "route_explored": [list(tile) for tile in route["explored"]],
        "route": [list(tile) for tile in route["route"]],
        "cost": route["cost"],
    }
    if style == RECKLESS:
        # What A* would have done from the same tile, so greedy and optimal can be compared on screen.
        cheapest = routes.route(start, goal, CAREFUL)
        answer["cheapest_route"] = [list(tile) for tile in cheapest["route"]]
        answer["cheapest_cost"] = cheapest["cost"]
    return answer
