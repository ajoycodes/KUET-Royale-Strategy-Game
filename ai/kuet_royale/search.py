"""The four path searches of the course, each written the way the labs write them.

    breadth_first    fewest steps. Every step counts 1.           (queue)
    uniform_cost     cheapest path. Expands the cheapest first.   (priority queue on g)
    best_first       greedy. Expands what looks closest.          (priority queue on h)
    a_star           cheapest path, aimed at the goal.            (priority queue on g + h)

    g = what the path has cost so far
    h = Manhattan distance to the goal

Every search returns the same kind of answer, a dict:

    goal      the tile it stopped on (None if nothing was found)
    route     the tiles from start to goal, both included
    cost      what the route costs (steps for breadth_first, terrain cost for the others)
    explored  every tile taken off the queue, in order: this is what the screen lights up
    costs     the cost of reaching every tile the search touched

In the game each one has its own job:
    breadth_first    hover units (terrain means nothing to them) and splash areas
    uniform_cost     "which enemy is cheapest to reach?" when there are several goals
    best_first       the route of a reckless unit
    a_star           the route of a careful unit
"""
import heapq
from collections import deque

from .grid import manhattan


def reconstruct_path(came_from, start, goal):
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def _answer(goal, came_from, start, costs, explored):
    if goal is None:
        return {"goal": None, "route": [], "cost": None, "explored": explored, "costs": costs}
    return {"goal": goal, "route": reconstruct_path(came_from, start, goal), "cost": costs[goal],
            "explored": explored, "costs": costs}


def breadth_first(grid, start, goals=()):
    """Spread out one step at a time until a goal tile comes off the queue.

    With no goals it explores everything it can reach.
    """
    goals = set(goals)
    frontier = deque([start])
    came_from = {start: None}
    steps = {start: 0}
    explored = []
    while frontier:
        current = frontier.popleft()
        explored.append(current)
        if current in goals:
            return _answer(current, came_from, start, steps, explored)
        for neighbour in grid.neighbours(current):
            if neighbour not in came_from:
                came_from[neighbour] = current
                steps[neighbour] = steps[current] + 1
                frontier.append(neighbour)
    return _answer(None, came_from, start, steps, explored)


def uniform_cost(grid, start, goals=()):
    """Spread out in order of path cost until a goal tile comes off the queue.

    The first goal reached is the cheapest goal to reach. With no goals it
    explores everything it can reach.
    """
    goals = set(goals)
    frontier = [(0, 0, start)]              # (path cost, order added, tile)
    added = 1
    came_from = {start: None}
    path_cost = {start: 0}
    explored = []
    done = set()
    while frontier:
        cost, _, current = heapq.heappop(frontier)
        if current in done:
            continue                        # an older, dearer copy of a tile already handled
        done.add(current)
        explored.append(current)
        if current in goals:
            return _answer(current, came_from, start, path_cost, explored)
        for neighbour in grid.neighbours(current):
            new_cost = cost + grid.cost(neighbour)
            if neighbour not in path_cost or new_cost < path_cost[neighbour]:
                path_cost[neighbour] = new_cost
                came_from[neighbour] = current
                heapq.heappush(frontier, (new_cost, added, neighbour))
                added += 1
    return _answer(None, came_from, start, path_cost, explored)


def best_first(grid, start, goal):
    """Greedy best-first search: always expand the tile that looks closest to the goal.

    It never looks at what a tile costs, so its route can be dearer than the
    cheapest one.
    """
    frontier = [(manhattan(start, goal), 0, start)]     # (h, order added, tile)
    added = 1
    came_from = {start: None}
    explored = []
    while frontier:
        _, _, current = heapq.heappop(frontier)
        explored.append(current)
        if current == goal:
            route = reconstruct_path(came_from, start, goal)
            costs = {goal: sum(grid.cost(tile) for tile in route[1:])}
            return {"goal": goal, "route": route, "cost": costs[goal], "explored": explored, "costs": costs}
        for neighbour in grid.neighbours(current):
            if neighbour not in came_from:
                came_from[neighbour] = current
                heapq.heappush(frontier, (manhattan(neighbour, goal), added, neighbour))
                added += 1
    return {"goal": None, "route": [], "cost": None, "explored": explored, "costs": {}}


def a_star(grid, start, goal):
    """A*: expand the tile with the smallest f = g + h.

    The cheapest tile costs 1, so the Manhattan distance never claims more than
    the true remaining cost, and the route found is the cheapest one.
    """
    frontier = [(manhattan(start, goal), 0, start)]     # (f, order added, tile)
    added = 1
    came_from = {start: None}
    path_cost = {start: 0}
    explored = []
    done = set()
    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in done:
            continue
        done.add(current)
        explored.append(current)
        if current == goal:
            return _answer(goal, came_from, start, path_cost, explored)
        for neighbour in grid.neighbours(current):
            new_cost = path_cost[current] + grid.cost(neighbour)
            if neighbour not in path_cost or new_cost < path_cost[neighbour]:
                path_cost[neighbour] = new_cost
                came_from[neighbour] = current
                heapq.heappush(frontier, (new_cost + manhattan(neighbour, goal), added, neighbour))
                added += 1
    return _answer(None, came_from, start, path_cost, explored)


def within(grid, centre, steps):
    """Breadth-first search with a step limit: every tile within `steps` of the centre.

    Used for splash damage. The centre is included even if nobody can stand on
    it (a tower).
    """
    frontier = deque([centre])
    distance = {centre: 0}
    while frontier:
        current = frontier.popleft()
        if distance[current] == steps:
            continue
        for neighbour in grid.neighbours(current):
            if neighbour not in distance:
                distance[neighbour] = distance[current] + 1
                frontier.append(neighbour)
    return list(distance)
