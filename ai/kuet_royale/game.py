"""The rules of a match, in the shape of the Lab 04 program.

    State                 a snapshot of the match
    actions(state)        the moves the side to play may make
    result(state, action) the snapshot after that move and the fighting that follows
    terminal(state)       is the leg over?
    utility(state)        the final score: left tower health minus right tower health

A move is (card, spot): which unused card of the deck, and which tile of the
side's half it drops on. Spots 0 and 1 are the starts of the top and bottom
lanes, 2 and 3 the front of those lanes by the bridges, and the rest are the
other tiles of the half. A person may use any spot. Either side may play first.
The left side wants the score high and the right side wants it low.

To keep the search to the end of the leg small enough, deep in the tree both
sides drop on the two lane starts (actions); only the move being chosen right
now also tries the front of the lanes (first_moves).

Nothing here is random, nothing is hidden, and the sides strictly take turns,
so the searches of the course can be used exactly as taught.
"""
from . import fuzzy
from .routes import CAREFUL, HOVER, RECKLESS, ROUTE_SEARCH, SPREAD_SEARCH, STYLES, Routes

LEFT, RIGHT = 0, 1
SIDE_NAMES = ("left", "right")
LANE_NAMES = ("top", "bottom")

TOWER_HEALTH = 20
TOWER_RANGE = 3          # a tower hits the closest enemy within this many tiles ...
TOWER_DAMAGE = 3         # ... for this much, once per battle step
BLAST_DAMAGE = 2         # what a falling unit with the "blast" quirk does to enemies next to it
FIRST_MOVE_SPOTS = (0, 1, 2, 3)     # the lane starts and the front of the lanes
LANE_SPOTS = (0, 1)
STEPS_PER_CARD = 3       # battle steps after each card
FINAL_STEPS = 15         # extra battle steps after the last card

# A unit is a tuple, so that snapshots are cheap to make:
#     (number, side, card, x, y, health, points)
# "points" are movement points saved up towards a tile the unit could not yet afford.
NUMBER, SIDE, CARD, X, Y, HEALTH, POINTS = range(7)

_routes = {}             # one notebook of search answers per map


def drop_tiles(grid, starts, side):
    """Every tile of a side's half a unit can be dropped on, the lane starts first and then the front of the lanes."""
    river = grid.width // 2
    near_river = river - 1 if side == LEFT else river + 1
    fronts = [(near_river, start[1]) for start in starts]
    first = list(starts) + [tile for tile in fronts if grid.passable(tile)]
    rest = [tile for tile in grid.tiles() if grid.passable(tile) and (tile[0] < river if side == LEFT else tile[0] > river)]
    return tuple(first + [tile for tile in rest if tile not in first])


def lane_of(tile):
    """Which lane a tile of the map belongs to, in words."""
    return "top" if tile[1] < 3 else "bottom" if tile[1] > 3 else "middle"


class Match:
    """Everything that stays the same from the first card to the last."""

    def __init__(self, grid, left_deck, right_deck, tower_health=TOWER_HEALTH):
        self.grid = grid
        self.tower_health = tower_health
        if grid.name not in _routes:
            _routes[grid.name] = Routes(grid)
        self.routes = _routes[grid.name]
        self.decks = (left_deck, right_deck)
        self.styles = tuple([STYLES[card["walks"]] for card in deck] for deck in self.decks)
        self.tower_tile = (grid.tower("left"), grid.tower("right"))
        # A unit walks towards the tiles next to a tower, and stops as soon as the tower is in range.
        self.tower_front = tuple(frozenset(grid.neighbours(tile)) for tile in self.tower_tile)
        self.starts = tuple(tuple(grid.start(side, lane) for lane in LANE_NAMES) for side in SIDE_NAMES)
        self.drops = tuple(drop_tiles(grid, self.starts[side], side) for side in (LEFT, RIGHT))
        self.quirks = tuple([card.get("quirk", "") for card in deck] for deck in self.decks)
        self.cost = {tile: grid.cost(tile) for tile in grid.tiles() if grid.passable(tile)}
        self.mud_cost = max(self.cost.values())
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


def _moves(state, spots):
    used = state.used[state.player]
    deck = state.match.decks[state.player]
    return [(card, spot) for card in range(len(deck)) if not used >> card & 1 for spot in spots]


def actions(state):
    """Every unused card of the side to play, into either lane: what the search assumes deep in the tree."""
    return _moves(state, LANE_SPOTS)


def first_moves(state):
    """The moves a brain chooses between right now: the lanes, and the front of the lanes."""
    return _moves(state, FIRST_MOVE_SPOTS)


def is_legal(state, action):
    """A person's move: an unused card on any tile of their own half."""
    card, spot = action
    deck = state.match.decks[state.player]
    return 0 <= card < len(deck) and not state.used[state.player] >> card & 1 and 0 <= spot < len(state.match.drops[state.player])


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
    card, spot = action
    side = state.player
    x, y = match.drops[side][spot]
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


def _blow(match, damage, quirk, foe, foe_side):
    """What one hit does to an enemy unit, once the attacker's and the target's specials are counted."""
    foe_card = foe[CARD]
    if quirk == "finisher":
        if foe[HEALTH] * 2 < match.decks[foe_side][foe_card]["health"]:
            damage += 1
    elif quirk == "anti_air" and match.styles[foe_side][foe_card] == HOVER:
        damage += 2
    if match.quirks[foe_side][foe_card] == "armour":
        damage = max(1, damage - 1)
    return damage


def battle_step(match, units, towers, log=None, memory=None):
    """One step of the fight: every unit does one thing, then the towers fire.

    Everything is decided from where units stood when the step began, and all
    damage lands together, so the order units are looked at favours nobody.
    """
    routes = match.routes
    cost_of = match.cost
    styles = match.styles
    quirks = match.quirks
    by_side = ([unit for unit in units if unit[SIDE] == LEFT], [unit for unit in units if unit[SIDE] == RIGHT])
    # Hover units can only be hit by ranged units, other hover units and towers.
    grounded = ([unit for unit in by_side[LEFT] if styles[LEFT][unit[CARD]] != HOVER],
                [unit for unit in by_side[RIGHT] if styles[RIGHT][unit[CARD]] != HOVER])
    hurt = {}
    tower_hurt = [0, 0]
    acted = []
    entry = None
    if log is not None:
        entry = {"searches": [], "moves": [], "attacks": [], "shots": [], "specials": []}

    for unit in units:
        number, side, card_index, x, y, health, points = unit
        card = match.decks[side][card_index]
        style = styles[side][card_index]
        quirk = quirks[side][card_index]
        foe_side = 1 - side
        reach = card["range"]
        foes = by_side[foe_side] if reach > 1 or style == HOVER else grounded[foe_side]
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
            choices.append((None, tower_distance, towers[foe_side] * 100 // match.tower_health))

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
                if quirk == "siege":
                    damage *= 2
                    if entry is not None:
                        entry["specials"].append({"unit": number, "word": "Siege"})
                tower_hurt[foe_side] += damage
                centre = (tower_x, tower_y)
            else:
                plain = damage
                damage = _blow(match, damage, quirk, foe, foe_side)
                hurt[foe[NUMBER]] = hurt.get(foe[NUMBER], 0) + damage
                centre = (foe[X], foe[Y])
                foe_quirk = quirks[foe_side][foe[CARD]]
                if foe_quirk == "spikes" and target[1] <= 1:
                    hurt[number] = hurt.get(number, 0) + 1
                if entry is not None:
                    if damage > plain:
                        entry["specials"].append({"unit": number, "word": "Finisher" if quirk == "finisher" else "Anti-air"})
                    if foe_quirk == "armour":
                        entry["specials"].append({"unit": foe[NUMBER], "word": "Armour"})
                    elif foe_quirk == "spikes" and target[1] <= 1:
                        entry["specials"].append({"unit": foe[NUMBER], "word": "Spikes"})
            if card["splash"]:
                area = routes.near(centre)          # breadth-first: everything within one step
                for other in foes:
                    if other is not foe and (other[X], other[Y]) in area:
                        hurt[other[NUMBER]] = hurt.get(other[NUMBER], 0) + _blow(match, card["damage"], quirk, other, foe_side)
                        splashed.append(other[NUMBER])
                        if quirks[foe_side][other[CARD]] == "spikes" and abs(other[X] - x) + abs(other[Y] - y) <= 1:
                            hurt[number] = hurt.get(number, 0) + 1
                            if entry is not None:
                                entry["specials"].append({"unit": other[NUMBER], "word": "Spikes"})
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
        goal = routes.nearest(here, goals, style, quirk == "mud_walker", side)
        if entry is not None and memory is not None and memory.get(number) != goal:
            memory[number] = goal
            entry["searches"].append(describe_search(match, number, here, goal, style, quirk == "mud_walker", side))

        # 3. Walk along the route for as long as the movement points last.
        points += card["speed"]
        path = [here]
        while here != goal:
            step = routes.next_step(here, goal, style, side)
            price = 1 if style == HOVER else cost_of[step]
            if quirk == "mud_walker" and price == match.mud_cost:
                price = 1
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
        chosen_unit = None
        for foe in by_side[1 - side]:
            distance = abs(foe[X] - tower_x) + abs(foe[Y] - tower_y)
            if distance <= TOWER_RANGE:
                key = (distance, foe[HEALTH], foe[NUMBER])
                if chosen is None or key < chosen:
                    chosen = key
                    chosen_unit = foe
        if chosen is not None:
            damage = _blow(match, TOWER_DAMAGE, "", chosen_unit, 1 - side)
            hurt[chosen[2]] = hurt.get(chosen[2], 0) + damage
            if entry is not None:
                entry["shots"].append({"side": SIDE_NAMES[side], "target": chosen[2], "damage": damage})

    # A unit about to fall with the "blast" quirk hurts every enemy on the ground next to where it ends the step.
    # The blast lands with everything else, and a unit it kills does not blast in its turn.
    falling = [unit for unit in acted if unit[HEALTH] <= hurt.get(unit[NUMBER], 0) and quirks[unit[SIDE]][unit[CARD]] == "blast"]
    for unit in falling:
        area = routes.near((unit[X], unit[Y]))
        for other in acted:
            if other[SIDE] != unit[SIDE] and styles[other[SIDE]][other[CARD]] != HOVER and (other[X], other[Y]) in area:
                hurt[other[NUMBER]] = hurt.get(other[NUMBER], 0) + _blow(match, BLAST_DAMAGE, "", other, other[SIDE])
        if entry is not None:
            entry["specials"].append({"unit": unit[NUMBER], "word": "Last blast"})

    # All the damage lands together.
    survivors = []
    dead = []
    for unit in acted:
        number = unit[NUMBER]
        lost = hurt.get(number, 0)
        health = unit[HEALTH] - lost
        if health > 0:
            if not lost and quirks[unit[SIDE]][unit[CARD]] == "repair" and health < match.decks[unit[SIDE]][unit[CARD]]["health"]:
                health += 1                         # nothing hit it this step
                if entry is not None:
                    entry["specials"].append({"unit": number, "word": "Repair"})
            survivors.append(unit[:HEALTH] + (health, unit[POINTS]))
        else:
            dead.append(number)
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


def describe_search(match, number, start, goal, style, mud_walker=False, side=LEFT):
    """What the screen needs to show a unit choosing a target and a route to it."""
    routes = match.routes
    route = routes.route(start, goal, style, side)
    answer = {
        "unit": number,
        "from": list(start),
        "goal": list(goal),
        "target_search": SPREAD_SEARCH[style],
        "target_explored": [list(tile) for tile in routes.explored_until(start, goal, style, mud_walker, side)],
        "route_search": ROUTE_SEARCH[style],
        "route_explored": [list(tile) for tile in route["explored"]],
        "route": [list(tile) for tile in route["route"]],
        "cost": route["cost"],
    }
    if mud_walker:
        # Its own price for the route. Greedy against optimal at everyone else's prices would say nothing true of it.
        answer["cost"] = sum(1 if match.cost[tile] == match.mud_cost else match.cost[tile] for tile in route["route"][1:])
    elif style == RECKLESS:
        # What A* would have done from the same tile, so greedy and optimal can be compared on screen.
        cheapest = routes.route(start, goal, CAREFUL, side)
        answer["cheapest_route"] = [list(tile) for tile in cheapest["route"]]
        answer["cheapest_cost"] = cheapest["cost"]
    return answer
