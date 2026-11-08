"""Checks on the rules of a match. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import random
import unittest

from kuet_royale import game
from kuet_royale.cards import load_roster, special_of
from kuet_royale.game import (FINAL_STEPS, LEFT, RIGHT, STEPS_PER_CARD, TOWER_DAMAGE, TOWER_HEALTH, Match, State,
                              actions, battle_step, result, terminal, utility, winner)
from kuet_royale.grid import load_map

CSE = {card["name"]: card for card in load_roster("cse")}
ME = {card["name"]: card for card in load_roster("me")}


def match_of(left, right):
    return Match(load_map(), [CSE[name] for name in left], [ME[name] for name in right])


#                 left: 0 Compiler, 1 Algorithmist, 2 Debugger, 3 Stack Runner
#                 right: 0 Heavy Machine, 1 Robotic Arm, 2 Gear Runner, 3 Quadcopter
def usual():
    return match_of(["Compiler", "Algorithmist", "Debugger", "Stack Runner"],
                    ["Heavy Machine", "Robotic Arm", "Gear Runner", "Quadcopter"])


def unit(number, side, card, tile, health, points=0):
    return (number, side, card, tile[0], tile[1], health, points)


class Turns(unittest.TestCase):
    def test_the_opening_offers_every_card_in_both_lanes(self):
        state = State(usual())
        self.assertEqual(actions(state), [(card, lane) for card in range(4) for lane in (0, 1)])
        self.assertEqual(state.player, LEFT)
        self.assertFalse(terminal(state))

    def test_a_card_is_played_once_and_the_sides_take_turns(self):
        state = result(State(usual()), (2, 0))
        self.assertEqual(state.player, RIGHT)
        self.assertEqual(len(actions(state)), 8)                 # the other side still has all four cards
        state = result(state, (0, 1))
        self.assertEqual(state.player, LEFT)
        self.assertEqual(actions(state), [(card, lane) for card in (0, 1, 3) for lane in (0, 1)])
        self.assertEqual(state.plays, 2)

    def test_the_second_leg_starts_with_the_right_side(self):
        state = State(usual(), player=RIGHT)
        state = result(state, (0, 0))
        self.assertEqual(state.units[0][game.SIDE], RIGHT)
        self.assertEqual(state.player, LEFT)

    def test_a_leg_ends_after_eight_cards(self):
        state = State(usual())
        for _ in range(8):
            self.assertFalse(terminal(state))
            state = result(state, actions(state)[0])
        self.assertTrue(terminal(state))
        self.assertEqual(actions(state), [])
        self.assertLessEqual(state.steps, 8 * STEPS_PER_CARD + FINAL_STEPS)

    def test_the_same_moves_always_give_the_same_leg(self):
        def play():
            state = State(usual())
            for move in [(3, 0), (2, 1), (0, 0), (0, 0), (1, 1), (1, 0), (2, 0), (3, 1)]:
                state = result(state, move)
            return state.towers, state.units, state.steps
        self.assertEqual(play(), play())


class Walking(unittest.TestCase):
    def test_a_unit_appears_on_the_start_tile_of_its_lane_and_walks(self):
        match = usual()
        state = result(State(match), (0, 0))                     # Compiler, top lane, speed 1
        self.assertEqual(state.units, (unit(0, LEFT, 0, (1 + STEPS_PER_CARD, 1), 10),))
        state = result(State(match), (2, 1))                     # Debugger, bottom lane, speed 2
        self.assertEqual(state.units[0][game.X:game.Y + 1], (1 + 2 * STEPS_PER_CARD, 5))

    def test_grass_takes_a_slow_unit_two_steps(self):
        match = usual()
        # A Compiler (speed 1) on the grass of the top row, its only enemy two grass tiles to the right.
        units = (unit(0, LEFT, 0, (9, 0), 10), unit(1, RIGHT, 0, (11, 0), 13))
        units, _ = battle_step(match, units, (20, 20))
        self.assertEqual(units[0][game.X:game.POINTS + 1], (9, 0, 10, 1))        # grass costs 2: it saves its 1 point
        units, _ = battle_step(match, units, (20, 20))
        self.assertEqual(units[0][game.X:game.POINTS + 1], (10, 0, 10, 0))       # now it can afford the step

    def test_a_reckless_unit_wades_into_the_mud_and_a_careful_one_goes_round(self):
        match = usual()
        enemy = unit(9, RIGHT, 0, (3, 5), 13)                    # a Heavy Machine standing still in range of nothing
        runner = unit(0, LEFT, 3, (3, 1), 3)                     # Stack Runner: reckless, speed 3
        debugger = unit(1, LEFT, 2, (3, 1), 4)                   # Debugger: careful, speed 2
        log = []
        battle_step(match, (runner, debugger, enemy), (20, 20), log, {})
        searches = {entry["unit"]: entry for entry in log[0]["searches"]}
        self.assertEqual(searches[0]["route_search"], "best_first")
        self.assertEqual(searches[0]["route"][1], [3, 2])        # straight down, towards the mud
        self.assertEqual(searches[0]["cost"], 9)
        self.assertEqual(searches[0]["cheapest_cost"], 8)        # what A* would have paid from the same tile
        self.assertNotIn("cheapest_cost", searches[1])           # a careful unit already walks the A* route
        self.assertEqual(searches[1]["route_search"], "astar")
        self.assertEqual(searches[1]["route"][1], [2, 1])        # back along the road
        self.assertEqual(searches[1]["cost"], 8)
        self.assertEqual(searches[0]["target_search"], "uniform_cost")

    def test_a_hover_unit_pays_one_for_every_tile(self):
        match = usual()
        copter = unit(0, RIGHT, 3, (8, 1), 4)                    # Quadcopter: hover, speed 2, range 2
        enemy = unit(1, LEFT, 0, (8, 6), 10)
        log = []
        units, _ = battle_step(match, (copter, enemy), (20, 20), log, {})
        self.assertEqual(units[0][game.X:game.Y + 1], (8, 3))    # two tiles in one step, the second one mud
        self.assertEqual(log[0]["searches"][0]["route_search"], "breadth_first")
        self.assertEqual(log[0]["searches"][0]["target_search"], "breadth_first")

    def test_a_unit_stops_as_soon_as_an_enemy_is_in_range(self):
        match = usual()
        runner = unit(0, LEFT, 3, (2, 1), 3)                     # speed 3, range 1
        enemy = unit(1, RIGHT, 0, (5, 1), 13)
        units, _ = battle_step(match, (runner, enemy), (20, 20))
        self.assertEqual(units[0][game.X:game.Y + 1], (4, 1))    # next to the enemy after 2 of its 3 tiles
        self.assertEqual(units[0][game.POINTS], 0)

    def test_with_no_enemy_units_everyone_heads_for_the_tower(self):
        match = usual()
        log = []
        battle_step(match, (unit(0, LEFT, 0, (9, 1), 10),), (20, 20), log, {})
        self.assertEqual(log[0]["searches"][0]["goal"], [11, 3])


class Fighting(unittest.TestCase):
    def test_blows_land_together(self):
        match = usual()
        compiler = unit(0, LEFT, 0, (5, 1), 1)                   # damage 3 (2 on armour), nearly dead
        machine = unit(1, RIGHT, 0, (6, 1), 2)                   # damage 2 (1 on armour), nearly dead
        units, _ = battle_step(match, (compiler, machine), (20, 20))
        self.assertEqual(units, ())                              # each kills the other

    def test_damage_is_taken_off_health(self):
        match = usual()
        units, _ = battle_step(match, (unit(0, LEFT, 0, (5, 1), 10), unit(1, RIGHT, 0, (6, 1), 13)), (20, 20))
        self.assertEqual([entry[game.HEALTH] for entry in units], [10 - 1, 13 - 2])     # both wear armour: one less each

    def test_with_two_enemies_in_range_the_fuzzy_system_chooses(self):
        match = usual()
        archer = unit(0, LEFT, 1, (4, 1), 5)                     # Algorithmist: range 3, damage 2
        far_but_weak = unit(1, RIGHT, 0, (7, 1), 2)              # 3 tiles away, 2 of 13 health
        near_but_fresh = unit(2, RIGHT, 2, (5, 1), 4)            # 1 tile away, full health
        log = []
        units, _ = battle_step(match, (archer, far_but_weak, near_but_fresh), (20, 20), log, {})
        attack = [entry for entry in log[0]["attacks"] if entry["unit"] == 0][0]
        scores = {choice["target"]: choice["priority"] for choice in attack["choices"]}
        self.assertEqual(attack["target"], max(scores, key=scores.get))
        self.assertEqual(len(scores), 2)
        for choice in attack["choices"]:
            self.assertEqual(sorted(choice["strengths"]), ["high", "low", "medium"])
            self.assertTrue(all(0.0 <= value <= 1.0 for value in choice["strengths"].values()))

    def test_with_one_enemy_in_range_no_fuzzy_choice_is_made(self):
        match = usual()
        log = []
        battle_step(match, (unit(0, LEFT, 0, (5, 1), 10), unit(1, RIGHT, 0, (6, 1), 13)), (20, 20), log, {})
        self.assertNotIn("choices", log[0]["attacks"][0])

    def test_splash_hurts_everything_within_one_step_of_the_target(self):
        match = match_of(["Compiler", "Logic Bomber", "Debugger", "Stack Runner"],
                         ["Heavy Machine", "Robotic Arm", "Gear Runner", "Quadcopter"])
        bomber = unit(0, LEFT, 1, (3, 1), 5)                     # range 3, damage 2, splash
        target = unit(1, RIGHT, 0, (6, 1), 13)
        beside = unit(2, RIGHT, 2, (7, 1), 4)                    # one step from the target, out of the bomber's range
        apart = unit(3, RIGHT, 2, (9, 1), 4)
        units, _ = battle_step(match, (bomber, target, beside, apart), (20, 20))
        health = {entry[game.NUMBER]: entry[game.HEALTH] for entry in units}
        self.assertEqual((health[1], health[2], health[3]), (12, 2, 4))      # the Heavy Machine's armour takes one off

    def test_a_tower_fires_at_the_closest_enemy_in_range(self):
        match = usual()
        near = unit(0, RIGHT, 2, (1, 3), 4)                      # next to the left tower
        far = unit(1, RIGHT, 2, (2, 3), 4)                       # two tiles away
        outside = unit(2, RIGHT, 2, (3, 3), 4)
        log = []
        units, towers = battle_step(match, (near, far, outside), (20, 20), log, {})
        health = {entry[game.NUMBER]: entry[game.HEALTH] for entry in units}
        self.assertEqual(health[0], 4 - TOWER_DAMAGE)
        self.assertEqual((health[1], health[2]), (4, 4))
        self.assertEqual(log[0]["shots"], [{"side": "left", "target": 0, "damage": TOWER_DAMAGE}])
        self.assertEqual(towers, (20 - 2, 20))                   # the near one hit the tower for its 2 damage

    def test_a_tower_at_zero_ends_the_leg_at_once(self):
        match = usual()
        state = State(match, units=(unit(0, RIGHT, 0, (1, 3), 13),), towers=(2, 20), used=(0, 1), player=LEFT, plays=1)
        state = result(state, (1, 1))                            # whatever the left side plays, the Heavy Machine hits first
        self.assertEqual(state.towers[LEFT], 0)
        self.assertTrue(terminal(state))
        self.assertEqual(state.steps, 1)
        self.assertEqual(utility(state), -20)
        self.assertEqual(winner(state), RIGHT)

    def test_utility_is_left_tower_minus_right_tower(self):
        match = usual()
        self.assertEqual(utility(State(match, towers=(20, 14))), 6)
        self.assertEqual(winner(State(match, towers=(20, 14))), LEFT)
        self.assertEqual(utility(State(match, towers=(11, 11))), 0)
        self.assertIsNone(winner(State(match, towers=(11, 11))))
        self.assertEqual(TOWER_HEALTH, 20)


def fight(left_card, right_card, left_tile, right_tile, left_health=None, right_health=None, towers=(20, 20)):
    """One battle step between one card of each side. Returns (left health, right health, towers); 0 means gone."""
    cards = {card["name"]: card for name in ("cse", "eee", "me", "ce") for card in load_roster(name)}
    filler = ["Stack Runner", "Debugger", "Algorithmist"]
    match = Match(load_map(), [cards[left_card]] + [cards[name] for name in filler],
                  [cards[right_card]] + [cards[name] for name in filler])
    left = unit(0, LEFT, 0, left_tile, cards[left_card]["health"] if left_health is None else left_health)
    right = unit(1, RIGHT, 0, right_tile, cards[right_card]["health"] if right_health is None else right_health)
    units, towers = battle_step(match, (left, right), towers)
    health = {entry[game.NUMBER]: entry[game.HEALTH] for entry in units}
    return health.get(0, 0), health.get(1, 0), towers


class Specials(unittest.TestCase):
    def test_every_warrior_has_exactly_one_special(self):
        for name in ("cse", "eee", "me", "ce"):
            for card in load_roster(name):
                self.assertTrue(special_of(card)["words"], card["name"])

    def test_melee_ground_units_cannot_hit_hover_units(self):
        left, right, _ = fight("Debugger", "Quadcopter", (5, 1), (6, 1))
        self.assertEqual(right, 4)                               # melee: the Quadcopter is out of its reach
        self.assertEqual(left, 4 - 2)                            # the Quadcopter still hits back

    def test_ranged_units_can_hit_hover_units(self):
        _, right, _ = fight("Algorithmist", "Quadcopter", (5, 1), (6, 1))
        self.assertEqual(right, 4 - 2)

    def test_hover_units_can_hit_each_other(self):
        left, right, _ = fight("Electron", "Quadcopter", (5, 1), (6, 1))
        self.assertEqual((left, right), (3 - 2, 4 - 3))

    def test_towers_can_hit_hover_units(self):
        _, right, _ = fight("Debugger", "Quadcopter", (9, 1), (2, 3))
        self.assertEqual(right, 4 - TOWER_DAMAGE)

    def test_armour_takes_one_off_every_blow_but_never_all_of_it(self):
        _, right, _ = fight("Debugger", "Heavy Machine", (5, 1), (6, 1), 4, 10)
        self.assertEqual(right, 10 - (2 - 1))

    def test_spikes_hurt_a_melee_attacker_but_not_a_shooter(self):
        left, _, _ = fight("Stack Runner", "Gearwheel Guard", (5, 1), (7, 1), 3)
        self.assertEqual(left, 3)                                # nobody in reach yet
        left, _, _ = fight("Debugger", "Gearwheel Guard", (5, 1), (6, 1), 4)
        self.assertEqual(left, 4 - 2 - 1)                        # its blow, and the spikes
        left, _, _ = fight("Algorithmist", "Gearwheel Guard", (4, 1), (6, 1), 5)
        self.assertEqual(left, 5)

    def test_finisher_hits_harder_on_a_foe_under_half_health(self):
        _, fresh, _ = fight("Debugger", "Mech Warrior", (5, 1), (6, 1), 4, 6)
        self.assertEqual(fresh, 6 - 2)
        _, hurt, _ = fight("Debugger", "Mech Warrior", (5, 1), (6, 1), 4, 2)
        self.assertEqual(hurt, 0)                                # 3 on a foe with 2 left

    def test_anti_air_hits_harder_on_hover_units(self):
        _, flying, _ = fight("Optimizer", "Quadcopter", (5, 1), (6, 1), 5, 6)
        self.assertEqual(flying, 6 - (3 + 2))

    def test_siege_doubles_damage_to_the_tower(self):
        cards = {card["name"]: card for card in load_roster("ce")}
        match = Match(load_map(), load_roster("cse")[:4], [cards["Excavator"]] + load_roster("ce")[2:5])
        _, towers = battle_step(match, (unit(0, RIGHT, 0, (1, 3), 15),), (20, 20))
        self.assertEqual(towers[LEFT], 20 - 2 * 2)

    def test_repair_heals_a_unit_that_was_not_hit(self):
        left, _, _ = fight("Kernel", "Quadcopter", (2, 1), (10, 5), 5)
        self.assertEqual(left, 6)
        full, _, _ = fight("Kernel", "Quadcopter", (2, 1), (10, 5))
        self.assertEqual(full, 13)                               # never above its full health

    def test_blast_hurts_the_enemies_beside_a_falling_unit(self):
        _, right, _ = fight("Stack Runner", "Heavy Machine", (5, 1), (6, 1), 1, 10)
        self.assertEqual(right, 10 - (2 - 1) - max(1, game.BLAST_DAMAGE - 1))

    def test_a_blast_does_not_set_off_another_blast(self):
        cards = {card["name"]: card for name in ("cse", "ce") for card in load_roster(name)}
        filler = [cards["Debugger"], cards["Algorithmist"], cards["Kernel"]]
        match = Match(load_map(), [cards["Stack Runner"]] + filler, [cards["Construction Crew"]] + filler)
        # The left unit falls to the right unit's blow. Its blast kills a right runner that did not fall to a blow:
        # that runner's own blast must not then hit back.
        left = unit(0, LEFT, 0, (5, 1), 1)
        right = unit(1, RIGHT, 0, (6, 1), 2)
        far_left = unit(2, LEFT, 1, (5, 2), 4)
        units, _ = battle_step(match, (left, right, far_left), (20, 20))
        health = {entry[game.NUMBER]: entry[game.HEALTH] for entry in units}
        self.assertNotIn(0, health)
        self.assertNotIn(1, health)

    def test_a_blast_does_not_reach_hover_units(self):
        cards = {card["name"]: card for name in ("cse", "me") for card in load_roster(name)}
        filler = [cards["Kernel"], cards["Optimizer"], cards["Algorithmist"]]
        match = Match(load_map(), [cards["Stack Runner"]] + filler, [cards["Quadcopter"], cards["Mech Warrior"]] + filler[:2])
        runner = unit(0, LEFT, 0, (5, 1), 1)
        hovering = unit(1, RIGHT, 0, (5, 2), 4)
        on_foot = unit(2, RIGHT, 1, (6, 1), 6)
        units, _ = battle_step(match, (runner, hovering, on_foot), (20, 20))
        health = {entry[game.NUMBER]: entry[game.HEALTH] for entry in units}
        self.assertNotIn(0, health)
        self.assertEqual(health[1], 4)                           # nothing could reach it
        self.assertEqual(health[2], 6 - 2 - game.BLAST_DAMAGE)   # the runner's blow, and its blast

    def test_spikes_answer_a_splash_from_one_tile_away(self):
        cards = {card["name"]: card for name in ("cse", "me") for card in load_roster(name)}
        filler = [cards["Kernel"], cards["Optimizer"], cards["Algorithmist"]]
        match = Match(load_map(), [cards["Logic Bomber"]] + filler, [cards["Gearwheel Guard"], cards["Debugger"]] + filler[:2])
        bomber = unit(0, LEFT, 0, (5, 1), 5)
        guard = unit(1, RIGHT, 0, (6, 1), 11)
        weak = unit(2, RIGHT, 1, (7, 1), 1)
        log = []
        units, _ = battle_step(match, (bomber, guard, weak), (20, 20), log, {})
        attack = [entry for entry in log[0]["attacks"] if entry["unit"] == 0][0]
        self.assertEqual(attack["target"], 2)                    # the fuzzy rules pick the weak one
        self.assertEqual(attack["splash"], [1])
        health = {entry[game.NUMBER]: entry[game.HEALTH] for entry in units}
        self.assertEqual(health[0], 5 - 2 - 1)                   # the Guard's blow, and its spikes

    def test_a_mud_walker_picks_its_enemy_at_its_own_prices(self):
        cards = {card["name"]: card for name in ("cse", "eee") for card in load_roster(name)}
        filler = [cards["Debugger"], cards["Algorithmist"], cards["Kernel"]]
        walker = Match(load_map(), [cards["Relay Runner"]] + filler, [cards["Kernel"]] + filler)
        goal = walker.routes.nearest((2, 3), {(5, 3), (5, 1)}, game.STYLES["reckless"], True)
        self.assertEqual(goal, (5, 3))                           # straight through the mud costs it 4
        self.assertEqual(walker.routes.nearest((2, 3), {(5, 3), (5, 1)}, game.STYLES["reckless"]), (5, 1))

    def test_a_mud_walkers_route_is_priced_as_it_really_pays(self):
        cards = {card["name"]: card for name in ("cse", "eee") for card in load_roster(name)}
        filler = [cards["Debugger"], cards["Algorithmist"], cards["Kernel"]]
        match = Match(load_map(), [cards["Relay Runner"]] + filler, [cards["Kernel"]] + filler)
        answer = game.describe_search(match, 0, (2, 3), (5, 3), game.STYLES["reckless"], True)
        self.assertEqual(answer["cost"], 1 + 1 + 2)              # mud, mud, grass
        self.assertNotIn("cheapest_cost", answer)

    def test_a_mud_walker_goes_through_mud_faster_than_a_runner_who_pays_for_it(self):
        cards = {card["name"]: card for name in ("cse", "eee") for card in load_roster(name)}
        filler = [cards["Debugger"], cards["Algorithmist"], cards["Kernel"]]
        walker, runner = cards["Relay Runner"], cards["Stack Runner"]        # both speed 3 and reckless
        self.assertEqual((walker["speed"], walker["walks"]), (runner["speed"], runner["walks"]))
        reached = {}
        for card in (walker, runner):
            match = Match(load_map(), [card] + filler, filler + [cards["Kernel"]])
            memory, log = {}, []
            battle_step(match, (unit(0, LEFT, 0, (2, 3), card["health"]),), (20, 20), log, memory)
            reached[card["name"]] = log[0]["units"][0]["tile"][0]
        self.assertGreater(reached["Relay Runner"], reached["Stack Runner"])


class DropSpots(unittest.TestCase):
    def test_a_side_may_drop_on_any_free_tile_of_its_half_and_nowhere_else(self):
        match = usual()
        river = match.grid.width // 2
        for side in (LEFT, RIGHT):
            self.assertGreater(len(match.drops[side]), 20)
            self.assertEqual(len(set(match.drops[side])), len(match.drops[side]))
            for tile in match.drops[side]:
                self.assertTrue(match.grid.passable(tile))
                self.assertTrue(tile[0] < river if side == LEFT else tile[0] > river)

    def test_the_first_spots_are_the_lane_starts_and_the_front_of_the_lanes(self):
        match = usual()
        self.assertEqual(match.drops[LEFT][:2], tuple(match.starts[LEFT]))
        self.assertEqual(match.drops[RIGHT][:2], tuple(match.starts[RIGHT]))
        river = match.grid.width // 2
        self.assertEqual([tile[0] for tile in match.drops[LEFT][2:4]], [river - 1, river - 1])
        self.assertEqual([tile[0] for tile in match.drops[RIGHT][2:4]], [river + 1, river + 1])

    def test_a_brain_tries_more_spots_for_the_move_it_is_choosing_than_deep_in_the_tree(self):
        state = State(usual())
        self.assertEqual(len(game.first_moves(state)), 16)
        self.assertEqual(len(actions(state)), 8)

    def test_a_card_drops_on_the_tile_it_was_given(self):
        match = usual()
        spot = len(match.drops[LEFT]) - 1
        state = result(State(match), (0, spot), [], {})
        self.assertTrue(game.is_legal(State(match), (0, spot)))
        self.assertEqual(state.units[0][game.NUMBER], 0)
        log = []
        result(State(match), (2, spot), log, {})
        self.assertEqual(log[0]["moves"][0]["path"][0], list(match.drops[LEFT][spot]))

    def test_a_tile_outside_the_half_or_a_used_card_is_refused(self):
        match = usual()
        self.assertFalse(game.is_legal(State(match), (0, len(match.drops[LEFT]))))
        self.assertFalse(game.is_legal(State(match), (0, -1)))
        state = result(result(State(match), (0, 0)), (0, 0))
        self.assertFalse(game.is_legal(state, (0, 1)))


class DroppedAnywhere(unittest.TestCase):
    def test_every_walking_style_finds_its_way_from_every_tile_of_the_half(self):
        match = usual()                                          # card 0 careful, card 3 reckless on the left
        cards = {card["name"]: card for card in load_roster("cse")}
        filler = [cards["Debugger"], cards["Algorithmist"], cards["Kernel"]]
        for name in ("Debugger", "Stack Runner", "Cloud Drone"):
            match = Match(load_map(), [cards[name]] + filler, [cards["Kernel"]] + filler)
            for side in (LEFT, RIGHT):
                card = 0
                for tile in match.drops[side]:
                    units = (unit(0, side, card, tile, 50),)
                    memory = {}
                    towers = (20, 20)
                    for _ in range(30):
                        units, towers = battle_step(match, units, towers, [], memory)
                        if towers != (20, 20):
                            break
                    self.assertNotEqual(towers, (20, 20), (name, side, tile))


class Mirrored(unittest.TestCase):
    """The map is a mirror image, so a position and its mirror image must play out the same way."""

    def setUp(self):
        self.grid = load_map()
        deck = load_roster("eee")
        self.match = Match(self.grid, deck, deck)

    def mirror(self, tile):
        return (self.grid.width - 1 - tile[0], tile[1])

    def test_every_route_on_the_right_is_the_mirror_of_one_on_the_left(self):
        tiles = [tile for tile in self.grid.tiles() if self.grid.passable(tile)]
        routes = self.match.routes
        for start in tiles[::3]:
            for goal in tiles[::2]:
                for style in game.STYLES.values():
                    left = routes.route(start, goal, style, LEFT)["route"]
                    right = routes.route(self.mirror(start), self.mirror(goal), style, RIGHT)["route"]
                    self.assertEqual([self.mirror(tile) for tile in left], right)

    def test_a_position_and_its_mirror_image_fight_the_same(self):
        chooser = random.Random(5)
        tiles = [tile for tile in self.grid.tiles() if self.grid.passable(tile)]
        for _ in range(400):
            units = []
            for number in range(chooser.randint(1, 6)):
                card = chooser.randrange(8)
                x, y = chooser.choice(tiles)
                units.append((number, chooser.randint(LEFT, RIGHT), card, x, y, chooser.randint(1, self.match.decks[LEFT][card]["health"]), chooser.randint(0, 2)))
            towers = (chooser.randint(1, 20), chooser.randint(1, 20))
            flipped = [(number, 1 - side, card) + self.mirror((x, y)) + (health, points) for number, side, card, x, y, health, points in units]
            after, tower_after = battle_step(self.match, tuple(units), towers)
            mirror_after, mirror_towers = battle_step(self.match, tuple(flipped), towers[::-1])
            expected = [(number, 1 - side, card) + self.mirror((x, y)) + (health, points) for number, side, card, x, y, health, points in after]
            self.assertEqual(sorted(expected), sorted(mirror_after))
            self.assertEqual(tower_after[::-1], mirror_towers)


class TheLogForTheScreen(unittest.TestCase):
    def test_one_entry_per_battle_step_with_a_snapshot(self):
        match = usual()
        log, memory = [], {}
        state = result(State(match), (2, 0), log, memory)
        self.assertEqual(len(log), STEPS_PER_CARD)
        self.assertEqual(log[-1]["units"][0]["tile"], list(state.units[0][game.X:game.Y + 1]))
        self.assertEqual(log[-1]["towers"], {"left": 20, "right": 20})
        self.assertEqual(log[0]["moves"][0]["path"][0], [1, 1])

    def test_a_search_is_reported_only_when_a_unit_changes_its_mind(self):
        match = usual()
        log, memory = [], {}
        result(State(match), (2, 0), log, memory)
        self.assertEqual([len(entry["searches"]) for entry in log], [1, 0, 0])

    def test_logging_changes_nothing(self):
        match = usual()
        plain = result(State(match), (3, 1))
        logged = result(State(match), (3, 1), [], {})
        self.assertEqual((plain.units, plain.towers), (logged.units, logged.towers))


if __name__ == "__main__":
    unittest.main()
