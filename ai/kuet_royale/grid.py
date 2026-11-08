"""The battlefield: a small grid of tiles, each with a cost to step onto it.

A tile is a pair (x, y). x counts columns from the left, y counts rows from
the top, both starting at 0. The map itself lives in data/map.json, drawn with
one character per tile, so it can be changed without touching code.

Every path search in the game (A*, best-first, breadth-first, uniform-cost)
asks this module the same three questions:
    neighbours(tile)   which tiles can I step to from here?
    cost(tile)         what does stepping onto that tile cost?
    manhattan(a, b)    how many steps apart are two tiles, ignoring terrain?
"""
import json
import os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# The four ways a unit can step. They are always tried in this order, so a
# search gives the same answer every time it is run. A unit on the right side
# tries them in the mirror order, so it walks as its mirror image on the left does.
STEPS = [(0, -1), (1, 0), (0, 1), (-1, 0)]          # up, right, down, left
MIRROR_STEPS = [(0, -1), (-1, 0), (0, 1), (1, 0)]   # up, left, down, right

SIDES = ("left", "right")
LANES = ("top", "bottom")


class Grid:
    def __init__(self, data):
        self.name = data["name"]
        self.rows = data["rows"]
        self.kinds = data["tiles"]                  # mark -> {"name", "cost"}
        self.height = len(self.rows)
        self.width = len(self.rows[0])
        self.towers = {side: tuple(data["towers"][side]) for side in SIDES}
        self.starts = {side: {lane: tuple(data["starts"][side][lane]) for lane in LANES} for side in SIDES}
        self._check()

    def _check(self):
        """Stop at once if the map file contradicts itself."""
        for row in self.rows:
            if len(row) != self.width:
                raise ValueError("every row of the map must be %d tiles wide: %r" % (self.width, row))
            for mark in row:
                if mark not in self.kinds:
                    raise ValueError("the map uses a mark with no meaning: %r" % mark)
        for side in SIDES:
            if self.mark(self.towers[side]) != "T":
                raise ValueError("the %s tower is not on a T tile" % side)
            for lane in LANES:
                if self.mark(self.starts[side][lane]) != "S":
                    raise ValueError("the %s %s start is not on an S tile" % (side, lane))

    def inside(self, tile):
        x, y = tile
        return 0 <= x < self.width and 0 <= y < self.height

    def mark(self, tile):
        """The character drawn on this tile in the map file."""
        x, y = tile
        return self.rows[y][x]

    def kind(self, tile):
        """The plain name of this tile: road, bridge, start, grass, mud, river or tower."""
        return self.kinds[self.mark(tile)]["name"]

    def passable(self, tile):
        """Can a unit stand here? Rivers and towers have no cost, so nobody can."""
        return self.inside(tile) and self.kinds[self.mark(tile)]["cost"] is not None

    def cost(self, tile):
        """The price of stepping ONTO this tile."""
        if not self.passable(tile):
            raise ValueError("nobody can step onto %s" % (tile,))
        return self.kinds[self.mark(tile)]["cost"]

    def neighbours(self, tile, steps=STEPS):
        """The tiles one step away that a unit can stand on."""
        x, y = tile
        found = []
        for dx, dy in steps:
            other = (x + dx, y + dy)
            if self.passable(other):
                found.append(other)
        return found

    def tiles(self):
        """Every tile on the map, row by row."""
        return [(x, y) for y in range(self.height) for x in range(self.width)]

    def tower(self, side):
        return self.towers[side]

    def start(self, side, lane):
        """Where a unit appears when its card is played into this lane."""
        return self.starts[side][lane]

    def text(self, overlay=None):
        """The map as text, with column and row numbers.

        overlay is an optional {tile: character} to draw over the map, for
        example the tiles of a route.
        """
        overlay = overlay or {}
        lines = ["       " + "".join("%-3d" % x for x in range(self.width)).rstrip()]
        for y in range(self.height):
            cells = [overlay.get((x, y), self.rows[y][x]) for x in range(self.width)]
            lines.append("row %d  " % y + "  ".join(cells))
        return "\n".join(lines)


def manhattan(a, b):
    """Steps between two tiles if nothing were in the way."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def route_cost(grid, route):
    """What a route costs to walk: every tile stepped onto, so not the first one."""
    return sum(grid.cost(tile) for tile in route[1:])


def load_map(file_name="map.json"):
    with open(os.path.join(DATA, file_name), encoding="utf-8") as handle:
        return Grid(json.load(handle))
