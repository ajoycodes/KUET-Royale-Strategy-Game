"""A notebook of search answers.

The map never changes during a match, so a search from one tile to another
always gives the same answer. Each answer is worked out once by the real
search in search.py and kept here. Nothing in this file decides anything: it
only remembers.

Every lookup depends on nothing but its own arguments, so the look-ahead of
the AIs and the real match always walk units the same way.
"""
from .grid import MIRROR_STEPS
from .search import a_star, best_first, breadth_first, uniform_cost, within

CAREFUL, RECKLESS, HOVER = 0, 1, 2
STYLES = {"careful": CAREFUL, "reckless": RECKLESS, "hover": HOVER}
ROUTE_SEARCH = {CAREFUL: "astar", RECKLESS: "best_first", HOVER: "breadth_first"}
SPREAD_SEARCH = {CAREFUL: "uniform_cost", RECKLESS: "uniform_cost", HOVER: "breadth_first"}


class RightSideMap:
    """The same map for a unit on the right: the steps are tried in the mirror order.

    A search breaks ties by the order it tries steps in, so without this the
    two sides would walk differently on a map that is a mirror image.
    """

    def __init__(self, grid):
        self.cost = grid.cost
        self._grid = grid

    def neighbours(self, tile):
        return self._grid.neighbours(tile, MIRROR_STEPS)


class MudWalkersMap:
    """The map at a mud walker's prices, for its search for the enemy cheapest to reach."""

    def __init__(self, grid, sides_map):
        self.neighbours = sides_map.neighbours
        self._grid = grid

    def cost(self, tile):
        return 1 if self._grid.kind(tile) == "mud" else self._grid.cost(tile)


class Routes:
    def __init__(self, grid):
        self.grid = grid
        self._maps = (grid, RightSideMap(grid))         # one for each side: left, right
        self._mud_walkers_maps = tuple(MudWalkersMap(grid, sides_map) for sides_map in self._maps)
        self._spread = {}       # (start, who, side) -> answer of a search with no goal
        self._rank = {}         # (start, who, side) -> {tile: place in the order it was explored}
        self._route = {}        # (start, goal, style, side) -> answer of the route search
        self._next = {}         # (start, goal, style, side) -> the next tile to step onto
        self._near = {}         # tile -> the tiles within one step of it

    def spread(self, start, style, mud_walker=False, side=0):
        """The whole map in the order this unit's search reaches it.

        Hover units pay the same for every tile, so they spread by steps
        (breadth-first). Everyone else spreads by terrain cost (uniform-cost),
        at the prices this unit really pays.
        """
        key = (start, _who(style, mud_walker), side)
        if key not in self._spread:
            if style == HOVER:
                answer = breadth_first(self._maps[side], start)
            else:
                answer = uniform_cost(self._mud_walkers_maps[side] if mud_walker else self._maps[side], start)
            self._spread[key] = answer
            self._rank[key] = {tile: place for place, tile in enumerate(answer["explored"])}
        return self._spread[key]

    def nearest(self, start, goals, style, mud_walker=False, side=0):
        """Which of the goal tiles does the search reach first?

        This is exactly the tile uniform_cost(grid, start, goals) stops on:
        a search with goals explores in the same order as one without, it only
        stops sooner.
        """
        key = (start, _who(style, mud_walker), side)
        if key not in self._rank:
            self.spread(start, style, mud_walker, side)
        rank = self._rank[key]
        return min(goals, key=rank.__getitem__)

    def explored_until(self, start, goal, style, mud_walker=False, side=0):
        """The tiles the nearest-target search looked at before it stopped on goal."""
        answer = self.spread(start, style, mud_walker, side)
        place = self._rank[(start, _who(style, mud_walker), side)][goal]
        return answer["explored"][:place + 1]

    def route(self, start, goal, style, side=0):
        key = (start, goal, style, side)
        if key not in self._route:
            if style == HOVER:
                answer = breadth_first(self._maps[side], start, [goal])
            elif style == RECKLESS:
                answer = best_first(self._maps[side], start, goal)
            else:
                answer = a_star(self._maps[side], start, goal)
            self._route[key] = answer
        return self._route[key]

    def next_step(self, start, goal, style, side=0):
        """The tile to step onto next on the way from start to goal."""
        key = (start, goal, style, side)
        if key not in self._next:
            route = self.route(start, goal, style, side)["route"]
            self._next[key] = route[1] if len(route) > 1 else None
        return self._next[key]

    def near(self, tile):
        """The tiles a splash reaches: everything within one step (breadth-first)."""
        if tile not in self._near:
            self._near[tile] = frozenset(within(self.grid, tile, 1))
        return self._near[tile]


def _who(style, mud_walker):
    """Whose prices a spread uses."""
    return "hover" if style == HOVER else "mud walker" if mud_walker else "ground"
