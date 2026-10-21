"""Checks on the rules of a match. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import unittest

from kuet_royale import game
from kuet_royale.cards import load_roster
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
        compiler = unit(0, LEFT, 0, (5, 1), 2)                   # damage 3, nearly dead
        machine = unit(1, RIGHT, 0, (6, 1), 3)                   # damage 2, nearly dead
        units, _ = battle_step(match, (compiler, machine), (20, 20))
        self.assertEqual(units, ())                              # each kills the other

    def test_damage_is_taken_off_health(self):
        match = usual()
        units, _ = battle_step(match, (unit(0, LEFT, 0, (5, 1), 10), unit(1, RIGHT, 0, (6, 1), 13)), (20, 20))
        self.assertEqual([entry[game.HEALTH] for entry in units], [10 - 2, 13 - 3])

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
        self.assertEqual((health[1], health[2], health[3]), (11, 2, 4))

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
