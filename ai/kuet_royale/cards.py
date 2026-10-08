"""The cards of each department.

A card is one unit. Its numbers live in data/cards_<department>.json, so a new
card is a new row of numbers and never new code.
"""
import json
import os

from .grid import DATA

ROLES = ("Tank", "Ranged", "Fast")
WALKS = ("careful", "reckless", "hover")            # A*, best-first, breadth-first
NUMBERS = ("cost", "health", "damage", "range", "speed")

ROSTER_SIZE = 8
DECK_SIZE = 4
COST_LIMIT = 12


def load_roster(department):
    """The eight cards of a department, for example load_roster("cse")."""
    path = os.path.join(DATA, "cards_%s.json" % department.lower())
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["cards"]


def check_roster(cards):
    """Everything wrong with a roster, as a list of sentences. Empty means fine."""
    problems = []
    if len(cards) != ROSTER_SIZE:
        problems.append("a roster has %d cards, found %d" % (ROSTER_SIZE, len(cards)))
    names = [card.get("name") for card in cards]
    if len(set(names)) != len(names):
        problems.append("two cards share a name")
    for card in cards:
        name = card.get("name", "?")
        for number in NUMBERS:
            value = card.get(number)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                problems.append("%s: %s must be a whole number above 0" % (name, number))
        if card.get("role") not in ROLES:
            problems.append("%s: role must be one of %s" % (name, ", ".join(ROLES)))
        if card.get("walks") not in WALKS:
            problems.append("%s: walks must be one of %s" % (name, ", ".join(WALKS)))
        if not isinstance(card.get("splash"), bool):
            problems.append("%s: splash must be true or false" % name)
    for role in ROLES:
        if not any(card.get("role") == role for card in cards):
            problems.append("no card can fill the %s slot" % role)
    return problems
