"""Checks on the four path searches. Run from the ai folder:

    python3 -m unittest discover -s tests

Every expected number below can be checked by hand on the map in the README.
"""
import random
import unittest

from kuet_royale.grid import load_map, manhattan, route_cost
from kuet_royale.routes import CAREFUL, HOVER, RECKLESS, Routes
from kuet_royale.search import a_star, best_first, breadth_first, uniform_cost, within


def is_a_walk(grid, route):
    """Every step of a route goes to a neighbouring tile a unit can stand on."""
    return all(b in grid.neighbours(a) for a, b in zip(route, route[1:]))


class OnTheMap(unittest.TestCase):
    def setUp(self):
        self.grid = load_map()
        self.open = [tile for tile in self.grid.tiles() if self.grid.passable(tile)]

    def test_along_the_road_every_search_agrees(self):
        for search in (a_star, best_first):
            answer = search(self.grid, (1, 1), (11, 1))
            self.assertEqual(answer["route"], [(x, 1) for x in range(1, 12)])
            self.assertEqual(answer["cost"], 10)
        self.assertEqual(breadth_first(self.grid, (1, 1), [(11, 1)])["cost"], 10)
        self.assertEqual(uniform_cost(self.grid, (1, 1), [(11, 1)])["cost"], 10)

    def test_a_star_goes_round_by_road_where_best_first_wades_through_mud(self):
        # From (3,1) to (3,5): straight down is grass, mud, grass, road = 2 + 4 + 2 + 1 = 9.
        # Round by the road through (1,1) and (1,5) is eight road tiles = 8.
        careful = a_star(self.grid, (3, 1), (3, 5))
        reckless = best_first(self.grid, (3, 1), (3, 5))
        hover = breadth_first(self.grid, (3, 1), [(3, 5)])
        self.assertEqual(careful["cost"], 8)
        self.assertEqual(len(careful["route"]), 9)
        self.assertEqual(reckless["route"], [(3, 1), (3, 2), (3, 3), (3, 4), (3, 5)])
        self.assertEqual(reckless["cost"], 9)
        self.assertEqual(hover["cost"], 4)                       # steps, not terrain cost

    def test_a_star_avoids_a_column_of_mud(self):
        # From (4,1) to (4,5): straight down is three mud tiles and a road = 13.
        # One column to the right is road, grass, grass, grass, road, road = 9.
        answer = a_star(self.grid, (4, 1), (4, 5))
        self.assertEqual(answer["cost"], 9)
        self.assertNotIn((4, 3), answer["route"])

    def test_the_river_is_crossed_on_a_bridge(self):
        for search in (a_star, best_first):
            route = search(self.grid, (5, 3), (7, 3))["route"]
            self.assertTrue((6, 1) in route or (6, 5) in route)
            self.assertTrue(is_a_walk(self.grid, route))
        self.assertEqual(a_star(self.grid, (5, 3), (7, 3))["cost"], 9)      # grass, road, bridge, road, grass, grass
        self.assertEqual(breadth_first(self.grid, (5, 3), [(7, 3)])["cost"], 6)

    def test_a_star_always_matches_uniform_cost(self):
        rng = random.Random(1)
        for _ in range(300):
            start, goal = rng.choice(self.open), rng.choice(self.open)
            careful = a_star(self.grid, start, goal)
            cheapest = uniform_cost(self.grid, start, [goal])
            self.assertEqual(careful["cost"], cheapest["cost"], (start, goal))
            self.assertEqual(route_cost(self.grid, careful["route"]), careful["cost"])
            self.assertTrue(is_a_walk(self.grid, careful["route"]))

    def test_a_star_explores_no_more_than_uniform_cost(self):
        rng = random.Random(2)
        for _ in range(100):
            start, goal = rng.choice(self.open), rng.choice(self.open)
            self.assertLessEqual(len(a_star(self.grid, start, goal)["explored"]),
                                 len(uniform_cost(self.grid, start, [goal])["explored"]))

    def test_best_first_is_never_cheaper_than_a_star(self):
        rng = random.Random(3)
        dearer = 0
        for _ in range(300):
            start, goal = rng.choice(self.open), rng.choice(self.open)
            greedy = best_first(self.grid, start, goal)
            self.assertTrue(is_a_walk(self.grid, greedy["route"]))
            self.assertEqual(route_cost(self.grid, greedy["route"]), greedy["cost"])
            self.assertGreaterEqual(greedy["cost"], a_star(self.grid, start, goal)["cost"])
            dearer += greedy["cost"] > a_star(self.grid, start, goal)["cost"]
        self.assertGreater(dearer, 30)                           # greedy really does pay more, often

    def test_breadth_first_finds_the_fewest_steps(self):
        rng = random.Random(4)
        for _ in range(200):
            start, goal = rng.choice(self.open), rng.choice(self.open)
            answer = breadth_first(self.grid, start, [goal])
            self.assertEqual(len(answer["route"]) - 1, answer["cost"])
            self.assertGreaterEqual(answer["cost"], manhattan(start, goal))
            self.assertTrue(is_a_walk(self.grid, answer["route"]))
            if (start[0] < 6) == (goal[0] < 6):
                self.assertEqual(answer["cost"], manhattan(start, goal))     # same bank: nothing is in the way

    def test_uniform_cost_stops_on_the_cheapest_of_several_goals(self):
        # From the top-left start, an enemy 3 road tiles away beats one 2 tiles away across mud.
        answer = uniform_cost(self.grid, (3, 1), [(6, 1), (3, 3)])
        self.assertEqual(answer["goal"], (6, 1))                 # 3 by road; (3,3) costs 2 + 4 = 6
        self.assertEqual(answer["cost"], 3)
        self.assertEqual(breadth_first(self.grid, (3, 1), [(6, 1), (3, 3)])["goal"], (3, 3))    # 2 steps beat 3

    def test_no_goal_means_explore_everything(self):
        for search in (breadth_first, uniform_cost):
            answer = search(self.grid, (1, 1))
            self.assertIsNone(answer["goal"])
            self.assertEqual(sorted(answer["explored"]), sorted(self.open))

    def test_uniform_cost_explores_in_order_of_cost(self):
        answer = uniform_cost(self.grid, (1, 1))
        costs = [answer["costs"][tile] for tile in answer["explored"]]
        self.assertEqual(costs, sorted(costs))

    def test_start_equal_to_goal(self):
        for search in (a_star, best_first):
            self.assertEqual(search(self.grid, (2, 2), (2, 2))["route"], [(2, 2)])
            self.assertEqual(search(self.grid, (2, 2), (2, 2))["cost"], 0)

    def test_within_one_step(self):
        self.assertEqual(sorted(within(self.grid, (3, 1), 1)), [(2, 1), (3, 0), (3, 1), (3, 2), (4, 1)])
        self.assertEqual(sorted(within(self.grid, (5, 3), 1)), [(4, 3), (5, 2), (5, 3), (5, 4)])     # the river is not a tile
        self.assertEqual(sorted(within(self.grid, (0, 3), 1)), [(0, 2), (0, 3), (0, 4), (1, 3)])     # around a tower
        self.assertEqual(within(self.grid, (3, 1), 0), [(3, 1)])


class TheNotebook(unittest.TestCase):
    """routes.py only remembers what search.py worked out. These tests check that it remembers truly."""

    def setUp(self):
        self.grid = load_map()
        self.routes = Routes(self.grid)
        self.open = [tile for tile in self.grid.tiles() if self.grid.passable(tile)]

    def test_nearest_is_exactly_where_the_real_search_stops(self):
        rng = random.Random(5)
        for _ in range(300):
            start = rng.choice(self.open)
            goals = rng.sample(self.open, rng.randint(1, 5))
            self.assertEqual(self.routes.nearest(start, set(goals), CAREFUL), uniform_cost(self.grid, start, goals)["goal"])
            self.assertEqual(self.routes.nearest(start, set(goals), RECKLESS), uniform_cost(self.grid, start, goals)["goal"])
            self.assertEqual(self.routes.nearest(start, set(goals), HOVER), breadth_first(self.grid, start, goals)["goal"])

    def test_explored_until_is_what_the_real_search_explored(self):
        rng = random.Random(6)
        for _ in range(100):
            start = rng.choice(self.open)
            goals = rng.sample(self.open, 3)
            goal = self.routes.nearest(start, set(goals), CAREFUL)
            self.assertEqual(self.routes.explored_until(start, goal, CAREFUL), uniform_cost(self.grid, start, goals)["explored"])

    def test_each_walking_style_uses_its_own_search(self):
        self.assertEqual(self.routes.route((3, 1), (3, 5), CAREFUL)["cost"], 8)
        self.assertEqual(self.routes.route((3, 1), (3, 5), RECKLESS)["cost"], 9)
        self.assertEqual(self.routes.route((3, 1), (3, 5), HOVER)["cost"], 4)
        self.assertEqual(self.routes.next_step((3, 1), (3, 5), RECKLESS), (3, 2))
        self.assertEqual(self.routes.next_step((3, 1), (3, 5), CAREFUL), (2, 1))
        self.assertIsNone(self.routes.next_step((3, 1), (3, 1), CAREFUL))

    def test_asking_twice_gives_the_same_answer(self):
        first = self.routes.route((1, 1), (11, 5), CAREFUL)
        self.assertIs(self.routes.route((1, 1), (11, 5), CAREFUL), first)


if __name__ == "__main__":
    unittest.main()
