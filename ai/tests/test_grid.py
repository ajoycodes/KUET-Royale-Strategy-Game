"""Checks on the battlefield. Run from the ai folder:

    python3 -m unittest discover -s tests
"""
import unittest

from kuet_royale.grid import LANES, SIDES, Grid, load_map, manhattan, route_cost


class TheMap(unittest.TestCase):
    def setUp(self):
        self.grid = load_map()

    def test_size(self):
        self.assertEqual((self.grid.width, self.grid.height), (13, 7))
        self.assertEqual(len(self.grid.tiles()), 91)

    def test_terrain_costs(self):
        self.assertEqual(self.grid.cost((2, 1)), 1)      # road
        self.assertEqual(self.grid.cost((6, 1)), 1)      # bridge
        self.assertEqual(self.grid.cost((1, 1)), 1)      # start tile
        self.assertEqual(self.grid.cost((2, 2)), 2)      # grass
        self.assertEqual(self.grid.cost((4, 3)), 4)      # mud

    def test_tile_names(self):
        self.assertEqual(self.grid.kind((6, 0)), "river")
        self.assertEqual(self.grid.kind((6, 5)), "bridge")
        self.assertEqual(self.grid.kind((0, 3)), "tower")

    def test_river_is_crossed_only_at_the_two_bridges(self):
        crossings = [y for y in range(self.grid.height) if self.grid.passable((6, y))]
        self.assertEqual(crossings, [1, 5])

    def test_nobody_stands_on_a_tower_or_off_the_map(self):
        self.assertFalse(self.grid.passable((0, 3)))
        self.assertFalse(self.grid.passable((12, 3)))
        self.assertFalse(self.grid.passable((-1, 0)))
        self.assertFalse(self.grid.passable((13, 6)))
        with self.assertRaises(ValueError):
            self.grid.cost((6, 3))

    def test_neighbours_come_in_a_fixed_order(self):
        # up, right, down, left
        self.assertEqual(self.grid.neighbours((3, 1)), [(3, 0), (4, 1), (3, 2), (2, 1)])

    def test_neighbours_leave_out_river_tower_and_the_edge(self):
        self.assertEqual(self.grid.neighbours((0, 0)), [(1, 0), (0, 1)])
        self.assertEqual(self.grid.neighbours((5, 3)), [(5, 2), (5, 4), (4, 3)])       # river to the right
        self.assertEqual(self.grid.neighbours((1, 3)), [(1, 2), (2, 3), (1, 4)])       # tower to the left

    def test_towers_and_starts(self):
        self.assertEqual(self.grid.tower("left"), (0, 3))
        self.assertEqual(self.grid.tower("right"), (12, 3))
        self.assertEqual(self.grid.start("left", "top"), (1, 1))
        self.assertEqual(self.grid.start("right", "bottom"), (11, 5))
        for side in SIDES:
            for lane in LANES:
                self.assertEqual(self.grid.kind(self.grid.start(side, lane)), "start")

    def test_each_tower_can_be_attacked_from_a_road_tile(self):
        self.assertEqual(self.grid.kind((1, 3)), "road")
        self.assertEqual(self.grid.kind((11, 3)), "road")
        self.assertEqual(manhattan((1, 3), self.grid.tower("left")), 1)

    def test_the_map_is_a_mirror_image_so_neither_side_is_favoured(self):
        for row in self.grid.rows:
            self.assertEqual(row, row[::-1])
        for lane in LANES:
            lx, ly = self.grid.start("left", lane)
            self.assertEqual(self.grid.start("right", lane), (self.grid.width - 1 - lx, ly))

    def test_manhattan(self):
        self.assertEqual(manhattan((1, 1), (11, 1)), 10)
        self.assertEqual(manhattan((1, 1), (1, 1)), 0)
        self.assertEqual(manhattan((2, 5), (0, 3)), 4)

    def test_route_cost_counts_every_tile_stepped_onto(self):
        along_the_road = [(1, 1), (2, 1), (3, 1), (4, 1)]
        self.assertEqual(route_cost(self.grid, along_the_road), 3)
        into_the_mud = [(4, 1), (4, 2), (4, 3)]                  # road, then mud, then mud
        self.assertEqual(route_cost(self.grid, into_the_mud), 8)
        self.assertEqual(route_cost(self.grid, [(4, 1)]), 0)

    def test_text_draws_the_map_and_an_overlay(self):
        text = self.grid.text({(2, 1): "*"})
        lines = text.split("\n")
        self.assertEqual(len(lines), 8)                          # numbers, then seven rows
        self.assertTrue(lines[2].startswith("row 1  .  S  *  ="))
        self.assertTrue(lines[4].startswith("row 3  T  =  .  m  m"))


class ABrokenMap(unittest.TestCase):
    def data(self):
        return {
            "name": "tiny",
            "rows": ["TS.ST"],
            "tiles": {"T": {"name": "tower", "cost": None}, "S": {"name": "start", "cost": 1},
                      ".": {"name": "grass", "cost": 2}},
            "towers": {"left": [0, 0], "right": [4, 0]},
            "starts": {"left": {"top": [1, 0], "bottom": [1, 0]}, "right": {"top": [3, 0], "bottom": [3, 0]}},
        }

    def test_a_good_tiny_map_loads(self):
        self.assertEqual(Grid(self.data()).width, 5)

    def test_uneven_rows_are_refused(self):
        data = self.data()
        data["rows"] = ["TS.ST", "..."]
        with self.assertRaises(ValueError):
            Grid(data)

    def test_an_unknown_mark_is_refused(self):
        data = self.data()
        data["rows"] = ["TS?ST"]
        with self.assertRaises(ValueError):
            Grid(data)

    def test_a_tower_in_the_wrong_place_is_refused(self):
        data = self.data()
        data["towers"]["left"] = [2, 0]
        with self.assertRaises(ValueError):
            Grid(data)


if __name__ == "__main__":
    unittest.main()
