"""Lab 06: building a deck is a constraint satisfaction problem, solved by backtracking.

    Variables     the four slots of a deck: Tank, Ranged, Fast and Free
    Domains       the cards of the roster that may go in each slot
    Constraints   no card twice, and the deck costs 13 or 14 energy in total

The search is the one from the lab: pick a variable, try its values one by
one, check the constraints, and step back when nothing fits. The two
improvements from the lab decide the order:

    MRV   fill the slot that has the fewest cards left to choose from
    LCV   try first the card that leaves the other slots the most choices
"""
import random

from .cards import COST_LEAST, COST_LIMIT

SLOTS = ("Tank", "Ranged", "Fast", "Free")


def fits_slot(card, slot):
    return slot == "Free" or card["role"] == slot


def is_valid(deck):
    """Does this deck, finished or not, break a constraint?"""
    names = [card["name"] for card in deck.values()]
    if len(set(names)) != len(names):
        return False                                    # the same card twice
    cost = sum(card["cost"] for card in deck.values())
    if cost > COST_LIMIT:
        return False                                    # too dear
    if len(deck) == len(SLOTS) and cost < COST_LEAST:
        return False                                    # finished, but too cheap
    return True


def get_domain(cards, deck, slot):
    """The cards that can still go in this slot without breaking a constraint."""
    domain = []
    for card in cards:
        if fits_slot(card, slot):
            deck[slot] = card
            if is_valid(deck):
                domain.append(card)
            del deck[slot]
    return domain


def select_slot(cards, deck):
    """MRV: the open slot with the fewest cards left. Of equals, the first."""
    best, fewest = None, None
    for slot in SLOTS:
        if slot not in deck:
            size = len(get_domain(cards, deck, slot))
            if fewest is None or size < fewest:
                best, fewest = slot, size
    return best


def order_cards(cards, deck, slot):
    """LCV: the cards for this slot, the least constraining first."""
    def choices_left(card):
        deck[slot] = card
        total = sum(len(get_domain(cards, deck, other)) for other in SLOTS if other not in deck)
        del deck[slot]
        return total
    return sorted(get_domain(cards, deck, slot), key=choices_left, reverse=True)    # equals keep their order


def backtrack(cards, deck, trace):
    if len(deck) == len(SLOTS):
        return True
    slot = select_slot(cards, deck)
    for card in order_cards(cards, deck, slot):
        deck[slot] = card
        trace.append({"step": "try", "slot": slot, "card": card["name"],
                      "cost": sum(chosen["cost"] for chosen in deck.values())})
        if backtrack(cards, deck, trace):
            return True
        del deck[slot]
        trace.append({"step": "undo", "slot": slot, "card": card["name"]})
    return False


def build_deck(cards, seed=None):
    """Returns (deck, trace). The deck is four cards in slot order.

    The seed only shuffles the order the roster is read in, so that cards
    which are equally good choices do not always come out the same way.
    """
    cards = list(cards)
    if seed is not None:
        random.Random(seed).shuffle(cards)
    deck, trace = {}, []
    if not backtrack(cards, deck, trace):
        raise ValueError("no deck satisfies the constraints")
    return [deck[slot] for slot in SLOTS], trace
