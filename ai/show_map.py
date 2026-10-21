#!/usr/bin/env python3
"""Print the battlefield and both rosters in the terminal.

    python3 show_map.py
"""
from kuet_royale.cards import COST_LEAST, COST_LIMIT, DECK_SIZE, check_roster, load_roster
from kuet_royale.grid import LANES, SIDES, load_map


def show_map(grid):
    print("%s  (%d wide, %d tall)\n" % (grid.name, grid.width, grid.height))
    print(grid.text())
    print()
    for mark, kind in grid.kinds.items():
        cost = "cannot be entered" if kind["cost"] is None else "costs %d to step onto" % kind["cost"]
        print("  %s  %-7s %s" % (mark, kind["name"], cost))
    print()
    for side in SIDES:
        starts = ", ".join("%s lane %s" % (lane, grid.start(side, lane)) for lane in LANES)
        print("  %-5s tower %s   starts: %s" % (side, grid.tower(side), starts))


def show_roster(department):
    cards = load_roster(department)
    print("\n%s roster" % department.upper())
    print("  %-18s %4s %6s %6s %5s %5s  %-16s %s" % ("card", "cost", "health", "damage", "range", "speed", "walks", "role"))
    for card in cards:
        walks = card["walks"] + (" +splash" if card["splash"] else "")
        print("  %-18s %4d %6d %6d %5d %5d  %-16s %s" % (
            card["name"], card["cost"], card["health"], card["damage"], card["range"], card["speed"], walks, card["role"]))
    for problem in check_roster(cards):
        print("  PROBLEM: " + problem)


def main():
    show_map(load_map())
    for department in ("cse", "me"):
        show_roster(department)
    print("\nA deck is %d cards costing %d to %d in total." % (DECK_SIZE, COST_LEAST, COST_LIMIT))


if __name__ == "__main__":
    main()
