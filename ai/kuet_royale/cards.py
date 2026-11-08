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
COST_LEAST = 13             # a deck must spend at least this much ...
COST_LIMIT = 14             # ... and at most this much
ABOUT_LENGTH = 60           # the plain sentence on a card has to fit on the card

# Every warrior has exactly one special: hover, splash, or one of these quirks.
# Each is one short rule, and each card names its own in its data file.
QUIRKS = {
    "armour": ("Armour", "Every hit on it does 1 less, but always at least 1."),
    "repair": ("Self-repair", "Heals 1 after any battle step in which nothing hit it."),
    "finisher": ("Finisher", "Hits a unit for 1 more when that unit is below half health."),
    "anti_air": ("Anti-air", "Hits hover units for 2 more."),
    "blast": ("Last blast", "When it falls, ground enemies within one step take 2."),
    "spikes": ("Spikes", "Any unit that hits it from one tile away takes 1."),
    "siege": ("Siege", "Hits towers for double damage."),
    "mud_walker": ("Mud walker", "Mud costs it only 1 to step on."),
}
HOVER_SPECIAL = ("Hover", "Only ranged units, towers and other hover units can hit it.")
SPLASH_SPECIAL = ("Splash", "Also hits every enemy unit within one step of the target.")


def load_roster(department):
    """The eight cards of a department, for example load_roster("cse")."""
    path = os.path.join(DATA, "cards_%s.json" % department.lower())
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["cards"]


def special_of(card):
    """A card's one special, in words for the screen."""
    if card["walks"] == "hover":
        name, words = HOVER_SPECIAL
    elif card["splash"]:
        name, words = SPLASH_SPECIAL
    else:
        name, words = QUIRKS[card["quirk"]]
    return {"name": name, "words": words}


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
        if card.get("walks") == "hover" and card.get("splash") is True:
            problems.append("%s: a card has one special, so a hover card has no splash" % name)
        has_special = card.get("walks") == "hover" or card.get("splash") is True
        if has_special and "quirk" in card:
            problems.append("%s: a card has one special, so hover and splash cards have no quirk" % name)
        if not has_special and card.get("quirk") not in QUIRKS:
            problems.append("%s: quirk must be one of %s" % (name, ", ".join(QUIRKS)))
        about = card.get("about")
        if not isinstance(about, str) or not 0 < len(about) <= ABOUT_LENGTH:
            problems.append("%s: about is one plain sentence of at most %d characters" % (name, ABOUT_LENGTH))
    for role in ROLES:
        if not any(card.get("role") == role for card in cards):
            problems.append("no card can fill the %s slot" % role)
    return problems
