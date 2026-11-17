#!/usr/bin/env python3
"""The only file the Godot screen runs. One question in, one JSON answer out.

    python3 bridge.py departments
    python3 bridge.py new --left cse --right me --left-brain alphabeta --right-brain mcts --session match.json
    python3 bridge.py step --session match.json                 an AI plays the next card
    python3 bridge.py step --card 2 --spot 7 --session match.json       a person plays it on a tile of their half
    python3 bridge.py next --session match.json                 open the second leg
    python3 bridge.py hint --session match.json                 what alpha-beta would play
    python3 bridge.py view --session match.json                 the match as it stands
    python3 bridge.py deck --left cse                           a legal deck from the CSP solver, for the troop picker
    python3 bridge.py power_new --left cse --right me --left-brain human --session match.json      start a one-minute power match
    python3 bridge.py power_beat --drop left:2:7 --session match.json           one beat; --drop counts only for a side a person plays

The match is kept in the session file between calls. With --out the answer is
written to a file instead of being printed.
"""
import argparse
import json
import sys
import traceback

from kuet_royale import engine, power


def answer(arguments):
    if arguments.command == "departments":
        return {"ok": True, "departments": engine.list_departments(), "brains": engine.BRAINS, "deck_rules": engine.deck_rules(),
                "power_blurbs": power.POWER_BLURB}
    if arguments.command == "deck":
        return {"ok": True, "deck": engine.suggest_deck(arguments.left, arguments.seed)}
    if arguments.command == "new":
        session = engine.new_match(arguments.left, arguments.right, arguments.left_brain, arguments.right_brain,
                                   arguments.seed, names(arguments.left_deck), names(arguments.right_deck))
        save(arguments.session, session)
        return {"ok": True, "view": engine.view(session)}
    if arguments.command == "power_new":
        session = power.new_match(arguments.left, arguments.right, arguments.left_brain, arguments.right_brain, arguments.seed)
        save(arguments.session, session)
        return {"ok": True, "view": power.view(session)}

    with open(arguments.session, encoding="utf-8") as handle:
        session = json.load(handle)
    if arguments.command == "power_beat":
        reply = power.beat(session, arguments.drop or [])
        save(arguments.session, session)
        return reply
    if arguments.command == "view":
        return {"ok": True, "view": power.view(session) if session.get("mode") == "power" else engine.view(session)}
    if arguments.command == "hint":
        return engine.hint(session)
    if arguments.command == "next":
        reply = engine.next_leg(session)
    else:
        reply = engine.step(session, arguments.card, arguments.lane, arguments.spot)
    save(arguments.session, session)
    return reply


def names(text):
    """A deck on the command line: card names separated by commas."""
    return text.split(",") if text else None


def save(path, session):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(session, handle)


def main():
    parser = argparse.ArgumentParser(description="KUET Royale: the link between the screen and the AI")
    parser.add_argument("command", choices=["departments", "deck", "new", "step", "next", "hint", "view", "power_new", "power_beat"])
    parser.add_argument("--session", default="match.json")
    parser.add_argument("--out")
    parser.add_argument("--left", default="cse")
    parser.add_argument("--right", default="me")
    parser.add_argument("--left-brain", default="alphabeta")
    parser.add_argument("--right-brain", default="mcts")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--card", type=int)
    parser.add_argument("--lane", choices=["top", "bottom"])
    parser.add_argument("--spot", type=int)
    parser.add_argument("--left-deck")
    parser.add_argument("--right-deck")
    parser.add_argument("--drop", action="append")
    arguments = parser.parse_args()
    try:
        reply = answer(arguments)
    except Exception as error:                      # the screen shows the message instead of freezing
        traceback.print_exc()
        reply = {"ok": False, "error": str(error)}
    text = json.dumps(reply, ensure_ascii=False)
    if arguments.out:
        with open(arguments.out, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
