"""A notebook of search answers.

The map never changes during a match, so a search from one tile to another
always gives the same answer. Each answer is worked out once by the real
search in search.py and kept here. Nothing in this file decides anything: it
only remembers.

Every lookup depends on nothing but its own arguments, so the look-ahead of
the AIs and the real match always walk units the same way.
"""
from .search import a_star, best_first, breadth_first, uniform_cost, within

CAREFUL, RECKLESS, HOVER = 0, 1, 2
STYLES = {"careful": CAREFUL, "reckless": RECKLESS, "hover": HOVER}
ROUTE_SEARCH = {CAREFUL: "astar", RECKLESS: "best_first", HOVER: "breadth_first"}
SPREAD_SEARCH = {CAREFUL: "uniform_cost", RECKLESS: "uniform_cost", HOVER: "breadth_first"}


class Routes:
    def __init__(self, grid):
        self.grid = grid
        self._spread = {}       # (start, hover?) -> answer of a search with no goal
        self._rank = {}         # (start, hover?) -> {tile: place in the order it was explored}
        self._route = {}        # (start, goal, style) -> answer of the route search
        self._next = {}         # (start, goal, style) -> the next tile to step onto
        self._near = {}         # tile -> the tiles within one step of it

    def spread(self, start, style):
        """The whole map in the order this unit's search reaches it.

        Hover units pay the same for every tile, so they spread by steps
        (breadth-first). Everyone else spreads by terrain cost (uniform-cost).
        """
        hover = style == HOVER
        key = (start, hover)
        if key not in self._spread:
            answer = breadth_first(self.grid, start) if hover else uniform_cost(self.grid, start)
            self._spread[key] = answer
            self._rank[key] = {tile: place for place, tile in enumerate(answer["explored"])}
        return self._spread[key]

    def nearest(self, start, goals, style):
        """Which of the goal tiles does the search reach first?

        This is exactly the tile uniform_cost(grid, start, goals) stops on:
        a search with goals explores in the same order as one without, it only
        stops sooner.
        """
        key = (start, style == HOVER)
        if key not in self._rank:
            self.spread(start, style)
        rank = self._rank[key]
        return min(goals, key=rank.__getitem__)

    def explored_until(self, start, goal, style):
        """The tiles the nearest-target search looked at before it stopped on goal."""
        answer = self.spread(start, style)
        place = self._rank[(start, style == HOVER)][goal]
        return answer["explored"][:place + 1]

    def route(self, start, goal, style):
        key = (start, goal, style)
        if key not in self._route:
            if style == HOVER:
                answer = breadth_first(self.grid, start, [goal])
            elif style == RECKLESS:
                answer = best_first(self.grid, start, goal)
            else:
                answer = a_star(self.grid, start, goal)
            self._route[key] = answer
        return self._route[key]

    def next_step(self, start, goal, style):
        """The tile to step onto next on the way from start to goal."""
        key = (start, goal, style)
        if key not in self._next:
            route = self.route(start, goal, style)["route"]
            self._next[key] = route[1] if len(route) > 1 else None
        return self._next[key]

    def near(self, tile):
        """The tiles a splash reaches: everything within one step (breadth-first)."""
        if tile not in self._near:
            self._near[tile] = frozenset(within(self.grid, tile, 1))
        return self._near[tile]
