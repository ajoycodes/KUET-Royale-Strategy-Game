#!/usr/bin/env python3
"""The classic game in the terminal.

    python3 play.py                                   CSE (alpha-beta) against ME (MCTS)
    python3 play.py --left me --right cse             pick the departments
    python3 play.py --left-brain mcts --right-brain alphabeta
    python3 play.py --left-brain human                play the left side yourself, with your own four cards
    python3 play.py --seed 7                          the same seed gives the same match
    python3 play.py --quiet                           only the card plays and the scores
"""
import argparse

from kuet_royale import engine
from kuet_royale.cards import COST_LEAST, COST_LIMIT, load_roster
from kuet_royale.deck_csp import deck_from_picks
from kuet_royale.game import SIDE_NAMES
from kuet_royale.grid import load_map


def show_decks(view):
    for side in SIDE_NAMES:
        info = view["sides"][side]
        cards = ", ".join("%s (%d)" % (card["name"], card["cost"]) for card in info["deck"])
        print("  %-5s %-4s thinks with %-10s deck, cost %d: %s" % (side, info["short"], info["brain_name"], info["deck_cost"], cards))


def show_map(grid, view):
    overlay = {}
    for unit in view["units"]:
        tile = tuple(unit["tile"])
        overlay[tile] = "+" if tile in overlay else str(unit["unit"])
    print(grid.text(overlay))
    for unit in view["units"]:
        print("    %d = %s's %s, health %d of %d" % (unit["unit"], view["sides"][unit["side"]]["short"], unit["card"],
                                                  unit["health"], unit["full"]))


def show_thinking(thinking):
    if thinking["algorithm"] == "alphabeta":
        print("    alpha-beta looked at %d positions and skipped %d moves (plain minimax: up to %d positions)"
              % (thinking["searched"], thinking["pruned"], thinking["plain_minimax"]))
        for row in thinking["choices"][:3]:
            sign = "" if row["exact"] else "no better than "
            print("      %s %-18s %-16s score %s%+d" % ("->" if row["chosen"] else "  ", row["card"], row["where"], sign, row["score"]))
    elif thinking["algorithm"] == "mcts":
        print("    MCTS played %d random legs" % thinking["repeats"])
        for row in thinking["choices"][:3]:
            print("      %s %-18s %-16s won %3d%% of %d tries" % ("->" if row["chosen"] else "  ", row["card"], row["where"],
                                                              round(row["average"] * 100), row["visits"]))


def ask_deck(identity):
    """A person's own four cards, by name. Nothing typed leaves it to the CSP solver."""
    cards = load_roster(identity)
    print("\nPick four %s warriors: one Tank, one Ranged, one Fast and one more, costing %d or %d in all." % (identity.upper(), COST_LEAST, COST_LIMIT))
    for place, card in enumerate(cards):
        print("  %d = %-18s cost %d  %s" % (place, card["name"], card["cost"], card["role"]))
    while True:
        try:
            words = input("  Four numbers, or nothing to let CSP choose: ").split()
        except EOFError:
            raise SystemExit("\nNo more input. Goodbye.")
        if not words:
            return None
        if all(word.isdigit() and int(word) < len(cards) for word in words):
            names = [cards[int(word)]["name"] for word in words]
            try:
                deck_from_picks(cards, names)
                return names
            except ValueError as problem:
                print("  %s" % problem)
        else:
            print("  Numbers from 0 to %d, please." % (len(cards) - 1))


PLACES = {("top",): 0, ("bottom",): 1, ("top", "front"): 2, ("bottom", "front"): 3}


def ask_human(view):
    """Returns "hint", or (card, spot) with spot a tile of the side's half."""
    side = view["to_move"]
    deck = view["sides"][side]["deck"]
    drops = view["sides"][side]["drops"]
    while True:
        print("  Your cards: " + ", ".join("%d = %s" % (card["index"], card["name"]) for card in deck if not card["used"]))
        try:
            words = input("  Card and place (2 top, 2 bottom front, or 2 17 for tile 17), t for the tiles, h for a hint: ").split()
        except EOFError:
            raise SystemExit("\nNo more input. Goodbye.")
        if words == ["h"]:
            return "hint"
        if words == ["t"]:
            print("  Tiles of your half: " + ", ".join("%d = %d,%d" % (spot, tile[0], tile[1]) for spot, tile in enumerate(drops)))
            continue
        if len(words) >= 2 and words[0].isdigit():
            card = int(words[0])
            spot = int(words[1]) if len(words) == 2 and words[1].isdigit() else PLACES.get(tuple(words[1:]))
            if spot is not None and spot < len(drops) and any(entry["index"] == card and not entry["used"] for entry in deck):
                return card, spot
        print("  That does not work. Try again.")


def main():
    parser = argparse.ArgumentParser(description="KUET Royale in the terminal")
    parser.add_argument("--left", default="cse")
    parser.add_argument("--right", default="me")
    parser.add_argument("--left-brain", default="alphabeta", choices=list(engine.BRAINS))
    parser.add_argument("--right-brain", default="mcts", choices=list(engine.BRAINS))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--quiet", action="store_true")
    arguments = parser.parse_args()

    grid = load_map()
    left_deck = ask_deck(arguments.left) if arguments.left_brain == "human" else None
    right_deck = ask_deck(arguments.right) if arguments.right_brain == "human" else None
    session = engine.new_match(arguments.left, arguments.right, arguments.left_brain, arguments.right_brain, arguments.seed, left_deck, right_deck)
    view = engine.view(session)
    print("\nKUET ROYALE: %s against %s   (seed %d)\n" % (view["sides"]["left"]["short"], view["sides"]["right"]["short"], view["seed"]))
    show_decks(view)

    while True:
        print("\n--- Leg %d: %s plays first ---" % (view["leg"], view["sides"][view["first"]]["short"]))
        while not view["leg_over"]:
            side = view["to_move"]
            if view["sides"][side]["brain"] == "human":
                choice = ask_human(view)
                if choice == "hint":
                    hint = engine.hint(session)["hint"]
                    print("  Alpha-beta would play %s in the %s." % (hint["card"], hint["where"]))
                    continue
                reply = engine.step(session, choice[0], spot=choice[1])
            else:
                reply = engine.step(session)
            view = reply["view"]
            print("\nCard %d of %d. %s" % (view["play"], view["plays"], reply["comments"][0]["text"]))
            if not arguments.quiet:
                show_thinking(reply["thinking"])
                for line in reply["comments"][1:]:
                    print("    " + line["text"])
                show_map(grid, view)
            print("    Towers: %s %d, %s %d" % (view["sides"]["left"]["short"], view["sides"]["left"]["tower"],
                                              view["sides"]["right"]["short"], view["sides"]["right"]["tower"]))
        leg = view["legs"][view["leg"] - 1]
        print("\nLeg %d is over. Damage done: %s %d, %s %d." % (leg["number"], view["sides"]["left"]["short"], leg["damage"]["left"],
                                                              view["sides"]["right"]["short"], leg["damage"]["right"]))
        point = leg["turning_point"]
        if point:
            print("Turning point: card %d. %s played %s in the %s; %s in the %s was %d better."
                  % (point["play"], view["sides"][point["side"]]["short"], point["move"]["card"], point["move"]["where"],
                     point["best"]["card"], point["best"]["where"], point["lost"]))
        if view["match_over"]:
            break
        view = engine.next_leg(session)["view"]

    left, right = view["sides"]["left"]["short"], view["sides"]["right"]["short"]
    print("\nFINAL SCORE over two legs: %s %d, %s %d" % (left, view["damage"]["left"], right, view["damage"]["right"]))
    if view["winner"] == "draw":
        print("A draw.\n")
    else:
        print("%s wins.\n" % view["sides"][view["winner"]]["short"])


if __name__ == "__main__":
    main()
