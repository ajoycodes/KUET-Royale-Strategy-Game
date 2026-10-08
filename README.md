# KUET Royale: Department Wars

A small strategy game where two KUET departments fight across a campus battlefield, and two different AI algorithms do the thinking. It is the course project for CSE 3210: Artificial Intelligence Lab.

| | |
|---|---|
| **Status** | Design agreed on 9 October 2026. **Nothing is built yet.** This file describes what will be built. |
| **Deadline** | About 23 October 2026 (two weeks from the day this was written) |
| **Team** | Two students |
| **Must have** | AI against AI, fun to watch |
| **Bonus** | A person against an AI |
| **Numbers** | Anything marked *starting value* will be tuned during the balance check on days 3 and 4 |

---

## 1. The game in one minute

1. Two departments face each other. Each has one **tower** and brings **four cards**. Every card is one unit.
2. They take turns. On your turn you play one card into the **top lane** or the **bottom lane**.
3. Units then walk and fight by themselves. Whoever's tower has more health at the end wins. Knock a tower down and you win at once.

That is the whole game. Nobody steers a unit after it is played. All the thinking is in three choices: which card, which lane, and in what order.

One department thinks with **alpha-beta search**. The other thinks with **Monte Carlo Tree Search**. So every match is also one algorithm against another.

---

## 2. How a match works

| Step | What happens | Who decides |
|---|---|---|
| 1. Setup | Pick two departments and give each one a brain (alpha-beta or MCTS). | The viewer |
| 2. Deck building | Each department's four cards are chosen from its roster of eight. | CSP solver |
| 3. Card turn | The department on the left goes first. It plays one unused card into the top or bottom lane. The unit appears on that lane's start tile. There is no passing. | Alpha-beta or MCTS |
| 4. Battle steps | The battle runs for 3 steps (*starting value*). | The rules |
| 5. Repeat | Steps 3 and 4 alternate until all eight cards are played. | |
| 6. Final battle | The battle keeps running until no unit is left, or for 15 steps (*starting value*). | The rules |
| 7. Result | Compare the towers. | |

Both decks lie face up the whole time. Nothing is hidden and nothing is random in the rules.

### What one unit does in one battle step

Every unit does exactly one thing per step:

1. **Is an enemy in range?** Then attack. If several are in range, the fuzzy system picks which one.
2. **Otherwise, pick where to go.** The destination is the enemy unit or enemy tower that is cheapest to reach.
3. **Walk.** Move up to `speed` tiles along the route to that destination.

Towers fight too. Each step a tower hits the closest enemy within 2 tiles for 2 damage (*starting values*).

All attacks in a step are worked out from where everything stood at the start of the step, and they land together. So the order units are processed in never favours one side.

Several units may stand on the same tile. That avoids traffic-jam rules.

---

## 3. The battlefield

A grid 13 tiles wide and 7 tall (*starting layout*). Left department on the left, right department on the right, a river down the middle.

```
        0  1  2  3  4  5  6  7  8  9 10 11 12
row 0   .  .  .  .  .  .  ~  .  .  .  .  .  .
row 1   .  S  =  =  =  =  B  =  =  =  =  S  .     top lane
row 2   .  =  .  .  m  .  ~  .  m  .  .  =  .
row 3   T  =  .  m  m  .  ~  .  m  m  .  =  T
row 4   .  =  .  .  m  .  ~  .  m  .  .  =  .
row 5   .  S  =  =  =  =  B  =  =  =  =  S  .     bottom lane
row 6   .  .  .  .  .  .  ~  .  .  .  .  .  .
```

| Mark | Tile | Cost to step onto it |
|---|---|---|
| `=` | Road | 1 |
| `B` | Bridge | 1 |
| `S` | Start tile of a lane (road) | 1 |
| `.` | Grass | 2 |
| `m` | Mud | 4 |
| `~` | River | Cannot be crossed |
| `T` | Tower | Cannot be entered; units attack it from next to it |

Costs are whole numbers on purpose, so every path cost on screen can be checked by hand.

The two roads are the lanes. The middle is grass and mud. A unit chasing an enemy in the other lane has a real choice: go round by road, or cut across the middle. That is where the path algorithms disagree, and where they become visible.

---

## 4. Cards and units

### The six numbers on a card

| Number | Meaning |
|---|---|
| Cost | Energy price. Only matters when building a deck. |
| Health | Damage it can take before it is removed. |
| Damage | Health it removes per attack. |
| Range | How many tiles away it can hit (counted as steps left/right/up/down). Range ignores terrain, so shooting over the river is allowed. |
| Speed | Tiles it walks per battle step. |
| Role | Tank, Ranged or Fast. Used by the deck builder. |

### How a unit walks

Each unit has one walking style. This is the heart of the pathfinding part of the project.

| Style | What it means | Algorithm |
|---|---|---|
| Careful (most units) | Takes the cheapest route, counting road, grass and mud. | A* |
| Reckless | Heads straight at the goal and may wade through mud. | Best-first search |
| Hover | Floats, so every tile costs the same. Fewest steps wins. | Breadth-first search |

### The only special ability

**Splash:** the attack also hurts every enemy within 1 step of the target. The area is found with breadth-first search.

That is all. No spells, no buildings, no healing, no other abilities. A new card is only a new row of numbers.

### CSE roster (*starting values*)

| Card | Icon | Cost | Health | Damage | Range | Speed | Walks | Role |
|---|---|---|---|---|---|---|---|---|
| Compiler | ⚙️ | 5 | 12 | 2 | 1 | 1 | Careful | Tank |
| Kernel | 🧠 | 5 | 14 | 1 | 1 | 1 | Careful | Tank |
| Algorithmist | 🧮 | 3 | 5 | 2 | 3 | 1 | Careful | Ranged |
| Optimizer | 📈 | 4 | 5 | 3 | 2 | 1 | Careful | Ranged |
| Logic Bomber | 💣 | 4 | 4 | 2 | 2 | 1 | Careful, Splash | Ranged |
| Debugger | 🐞 | 2 | 4 | 2 | 1 | 2 | Careful | Fast |
| Stack Runner | 🏃 | 2 | 3 | 2 | 1 | 3 | Reckless | Fast |
| Cloud Drone | ☁️ | 3 | 3 | 2 | 2 | 2 | Hover | Fast |

### ME roster (*starting values*)

| Card | Icon | Cost | Health | Damage | Range | Speed | Walks | Role |
|---|---|---|---|---|---|---|---|---|
| Heavy Machine | 🚜 | 5 | 15 | 2 | 1 | 1 | Careful | Tank |
| Gearwheel Guard | 🛡️ | 4 | 11 | 1 | 1 | 1 | Careful | Tank |
| Robotic Arm | 🦾 | 4 | 4 | 3 | 3 | 1 | Careful | Ranged |
| Steel Rain Cannon | 🌧️ | 5 | 5 | 2 | 3 | 1 | Careful, Splash | Ranged |
| Mech Warrior | 🦿 | 3 | 7 | 2 | 1 | 2 | Careful | Fast |
| Gear Runner | 🔩 | 2 | 4 | 2 | 1 | 3 | Reckless | Fast |
| Mini-Bot | 🤖 | 2 | 3 | 2 | 1 | 2 | Reckless | Fast |
| Quadcopter | 🚁 | 3 | 3 | 2 | 2 | 2 | Hover | Fast |

CSE leans fast and cheap. ME leans heavy and slow. EEE and CE are extra card lists and come in week 2 if there is time.

### Deck rules

A deck is four cards from the department's eight:

- one **Tank**, one **Ranged**, one **Fast**, and one **free** slot (any card);
- no card twice;
- total cost of 12 or less (*starting value*).

Example: Compiler (5) + Algorithmist (3) + Debugger (2) + Stack Runner (2) = 12.

---

## 5. Winning

| Situation | Result |
|---|---|
| A tower reaches 0 health | The other department wins immediately |
| The final battle ends | The tower with more health left wins |
| Both towers have the same health | Draw |

The number both AIs try to push their way is the **tower health difference at the end of the match**. It is a real final score, read off a finished match. It is not an estimate of an unfinished one.

---

## 6. The AI: eight algorithms, eight jobs

Every algorithm answers one clear question. All eight were taught in the course.

| # | Algorithm | The question it answers | Runs when | Taught in | What you see |
|---|---|---|---|---|---|
| 1 | A* | What is the cheapest route to that tile? | A careful unit gets a destination | Lab 03 | Searched tiles light up, route drawn, cost shown |
| 2 | Best-first search | Which way looks closest to the goal? | A reckless unit gets a destination | Lab 03 | A straighter route, sometimes through mud |
| 3 | Breadth-first search | What is the fewest-steps route? Which tiles are within 1 step? | A hover unit moves; a splash attack lands | Course | Rings spreading out one step at a time |
| 4 | Uniform-cost search | Which enemy is cheapest to reach? | A unit has nobody in range | Course | A cost wave spreading until it touches an enemy |
| 5 | Fuzzy inference | Several enemies are in range. Which one do I hit? | A unit attacks | Lab 05 | A priority number above each enemy |
| 6 | Alpha-beta search | Which card and lane give the best final score? | One department's card turn | Theory (built on Lab 04 minimax) | Top three choices with scores; branches searched and pruned |
| 7 | Monte Carlo Tree Search | Which card and lane win most often in play-outs? | The other department's card turn | Lab 08 | Top three choices with win rates and visit counts |
| 8 | CSP backtracking | Which four cards make a legal deck? | Once, before the match | Lab 06 | Slots filling one by one, with back-ups shown |

For numbers 3 and 4, write down whether each was in the lab or the theory class, so the answer is ready in the viva.

### 6.1 A* (careful units)

- **Score of a tile:** `f = g + h`. `g` is the terrain cost walked so far. `h` is the straight step count to the goal (Manhattan distance).
- **Why the answer is the cheapest route:** the cheapest tile costs 1, so `h` never says more than the true remaining cost.
- **Returns:** the route, its total cost, and the tiles it looked at (for the screen).
- **Say in the viva:** "A* finds the cheapest route because it adds what it has already paid to an honest guess of what is left."

### 6.2 Best-first search (reckless units)

- **Score of a tile:** `f = h` only. It ignores what it has already paid.
- **Effect:** quick and direct, but it will happily walk into mud. The same trip costs more than the A* route.
- **Say in the viva:** "Best-first is greedy. Put a Stack Runner next to a Debugger and you can see greedy against optimal on the same map."

### 6.3 Breadth-first search (hover units and splash)

- **Hover routing:** a hover unit pays the same for every tile, so the best route is the one with the fewest steps. Breadth-first search explores one step further each round, so the first time it reaches the goal is the fewest-steps route.
- **Splash area:** start at the target tile and spread out one step. Every enemy on those tiles is hurt.
- **Say in the viva:** "When every step costs the same, breadth-first search already gives the shortest path. No priority queue is needed."

### 6.4 Uniform-cost search (choosing a destination)

- **The problem:** a unit must go to the nearest enemy, but it does not yet know which enemy that is. There are several possible goals.
- **How:** spread out from the unit in order of total travel cost. The first tile reached that holds an enemy unit, or touches the enemy tower, is the destination.
- **Why not A\*:** A* needs one known goal to aim its guess at. Here there is no single goal yet.
- **Say in the viva:** "Uniform-cost search expands the cheapest tile first, so the first enemy it reaches is the cheapest enemy to reach."

(Hover units ignore terrain cost, so they use breadth-first search for this step as well.)

### 6.5 Fuzzy inference (choosing a target)

Used only when a unit has more than one enemy in range. Done the way Lab 05 does it by hand: straight-line shapes, OR means take the larger, clip each output shape, combine, and take the centre of the area over sample points. No library.

- **Inputs:** how far the enemy is (near, medium, far) and how much health it has left (low, medium, full).
- **Output:** attack priority from 0 to 100. The unit hits the enemy with the highest number.

The whole rule base is three rules:

```
IF enemy is near    OR  health is low     THEN priority is high
IF enemy is medium  OR  health is medium  THEN priority is medium
IF enemy is far     OR  health is full    THEN priority is low
```

- **Say in the viva:** "Finish off what is close and nearly dead. Fuzzy logic lets 'close' and 'nearly dead' be matters of degree instead of hard cut-offs."

### 6.6 Alpha-beta search (one department's brain)

- **A move** is a pair: (card, lane).
- **Shape:** the Lab 04 minimax program (`State`, `actions`, `result`, `terminal`, `utility`, `max_value`, `min_value`) with the two extra values alpha and beta from the theory class.
- **It searches to the very end of the match.** There is no depth limit and no evaluation function. `utility` is the tower health difference of a finished match.
- **Pruning:** when a branch cannot change the final choice, it is skipped. The screen counts skipped branches.
- **Say in the viva:** "Alpha-beta returns exactly what plain minimax would return. It only skips branches that cannot matter."

### 6.7 Monte Carlo Tree Search (the other department's brain)

Exactly the four steps on the Lab 08 slides:

1. **Select** by UCB1: `t/n + C * sqrt(ln N / n)` with `C = 2`.
2. **Expand** all moves of a visited leaf.
3. **Roll out:** play random legal moves to the end of the match.
4. **Back up:** add 1 to `n` and the result to `t` on the way up.

The result of a rollout is 1 for a win, 0.5 for a draw and 0 for a loss, from the side that is thinking.

- **Say in the viva:** "MCTS never looks at every line. It plays many random matches and spends more of them on the moves that keep doing well."

### 6.8 CSP backtracking (deck building)

- **Variables:** the four deck slots (Tank, Ranged, Fast, Free).
- **Domains:** the roster cards allowed in each slot.
- **Constraints:** all four different; total cost 12 or less.
- **Search:** backtracking as in Lab 06, with **MRV** (fill the slot that has the fewest cards left to choose from) and **LCV** (try the card that leaves the other slots the most choices).
- **Say in the viva:** "A deck is a small constraint problem. If an expensive Tank and an expensive Ranged leave no affordable Fast card, the solver backs up and tries again."

### 6.9 Why the game is this small

Alpha-beta has to reach the end of the match, so the match must be short.

- First card: 4 cards x 2 lanes = 8 choices. Then 8 for the other side, then 6, 6, 4, 4, 2, 2.
- 8 x 8 x 6 x 6 x 4 x 4 x 2 x 2 = **147,456 complete matches** at most.

Alpha-beta will skip a large share of those. **How long this takes in Python has not been measured yet.** It is the first check on day 3. If it is too slow, the hand drops to three cards each, which is 2,304 complete matches.

To keep each simulated battle step cheap, a route is worked out once by the real algorithm and stored. The map never changes, so a route depends only on the start tile, the goal tile and the walking style.

### 6.10 Why turns, open hands and no dice

Alpha-beta and MCTS as taught assume players alternate, everything is visible, and nothing is left to chance. The game is built to fit those assumptions, so each algorithm can be used exactly as taught.

### 6.11 Choices that are ours, not the course's

Say these openly if asked:

- The score is the tower health difference.
- MCTS runs 2,000 rollouts per move (*starting value*) and plays the move with the best average result.
- MCTS scores a rollout as 1, 0.5 or 0.
- The shapes of the fuzzy terms, the map, the terrain costs and the card numbers.
- The four deck slots and the cost limit.

---

## 7. What you see on screen

```
+----------------+--------------------------------------+----------------+
|  CSE           |                                      |            ME  |
|  alpha-beta    |          the battlefield             |          MCTS  |
|                |    (units walk, fight, towers fire)  |                |
|  thinking:     |                                      |     thinking:  |
|  1. card, lane |                                      |  1. card, lane |
|  2. ...        |                                      |  2. ...        |
|  3. ...        |                                      |  3. ...        |
|  searched /    |                                      |    rollouts /  |
|  pruned        |                                      |    win rate    |
+----------------+--------------------------------------+----------------+
|  CSE's four cards (face up)      |     ME's four cards (face up)       |
+------------------------------------------------------------------------+
|  commentary line           |  speed: 1x 2x 4x  |  pause  |  step       |
+------------------------------------------------------------------------+
```

- **Thinking panels:** each side's top three choices with their numbers, updated every card turn.
- **Visible search:** tiles light up as a path search explores them. A different colour per algorithm.
- **Priority numbers** above enemies when the fuzzy system picks a target.
- **Commentary:** one plain sentence per event, for example "Stack Runner cuts through the mud. Greedy, and it cost him."
- **Pick a winner:** before the match, the viewer bets on a department.
- **Turning point:** after the match, the one card play that decided it.
- **Speed control,** pause and single-step, so a match can be explained live.

### Modes

| Mode | Priority | What it is |
|---|---|---|
| AI against AI | Must | Pick two departments and their brains, then watch |
| You against AI | Bonus | Click a card, click a lane. Everything else is the same |

---

## 8. Tech stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Game screen | Godot, GDScript | 4.7.2 | Free, small, good at 2D. Installed with Homebrew. |
| Rendering | 2D, Compatibility renderer, 1280 x 720 | | Runs on any lab laptop |
| Rules and all AI | Python, standard library only | 3.9 or newer | The labs are in Python, so the code looks like the lab code |
| Priority queue | `heapq` | built in | A*, best-first and uniform-cost search, as in Lab 03 |
| Plain queue | `collections.deque` | built in | Breadth-first search |
| Randomness | `random` with a seed | built in | MCTS rollouts only; a seed makes a match repeatable |
| Data | JSON files | | Map and cards can be edited without touching code |
| Godot to Python link | Godot starts `python3 ai/bridge.py` once per decision and reads JSON back | | No server, no sockets, nothing to keep in sync |
| Tests | `unittest` | built in | One test file per algorithm |
| Art | Emoji and simple shapes drawn in code | | No art files to make or license |
| Sound | Short tones generated in code | | Optional |

**No extra installs.** No `pip` packages are needed.

**Deliberately not used:**

| Not used | Why |
|---|---|
| A network server between Godot and Python | Needed only for real-time play; this game is turn-based |
| A PDDL planner | Only PDDL syntax was taught; deck building is done with CSP instead |
| Fuzzy or search libraries (scikit-fuzzy, networkx) | The course teaches these by hand; the code must show the method |
| Machine learning | Not in the course |

**Machines:** developed on macOS (Python 3.9.6 and 3.13.9 are both present). It should run the same on Windows or Linux with Godot 4 and Python 3 installed. On Windows the command may be `python` instead of `python3`; the bridge will try both.

---

## 9. How the parts fit together

```
        Godot (screen only)                      Python (all rules, all AI)
  +---------------------------+            +--------------------------------+
  | menu, board, units,       |  request   | bridge.py                      |
  | cards, thinking panels,   | ---------> |   reads the match file         |
  | animations, sound         |            |   asks the right brain         |
  |                           |  JSON:     |   plays the card               |
  | plays back the list of    |  events +  |   runs the battle steps        |
  | events it is given        |  new view  |   writes the match file        |
  |                           | <--------- |   prints events as JSON        |
  +---------------------------+            +--------------------------------+
                                                         |
                                           match file (one JSON per match)
```

**One source of truth.** Every rule lives in Python. Godot never decides anything; it only draws what it is told. So the game is built once, not twice, and the terminal version and the Godot version can never disagree.

### Bridge commands (planned)

| Command | Does |
|---|---|
| `rosters` | Lists departments and their cards |
| `new` | Builds both decks and starts a match |
| `step` | Lets the side to move think, plays its card, runs the battle steps |
| `step --card X --lane top` | Same, with the human's choice |
| `view` | Returns the current match without changing it |

### What one reply looks like (shape, not final)

```json
{
  "ok": true,
  "thinking": {
    "side": "left", "algorithm": "alpha-beta",
    "choices": [
      {"card": "Debugger", "lane": "top", "score": 4},
      {"card": "Compiler", "lane": "bottom", "score": 1}
    ],
    "searched": 5120, "pruned": 3870
  },
  "events": [
    {"type": "deploy", "unit": 5, "card": "Debugger", "tile": [1, 1]},
    {"type": "search", "algorithm": "ucs", "unit": 5, "explored": [[1,1],[2,1]], "found": [11, 1]},
    {"type": "search", "algorithm": "astar", "unit": 5, "route": [[2,1],[3,1]], "cost": 2},
    {"type": "move", "unit": 5, "to": [3, 1]},
    {"type": "attack", "unit": 2, "target": 5, "damage": 2},
    {"type": "tower_hit", "side": "right", "health": 18}
  ],
  "view": {"turn": 3, "to_move": "right", "towers": {"left": 20, "right": 18}, "units": []}
}
```

The numbers in this example are made up to show the shape.

---

## 10. Folder layout (planned)

```
KUET-Royale/
├── README.md                 this file
├── project.godot             Godot project
├── main.tscn
├── scripts/                  Godot: drawing only
│   ├── main.gd               starts the menu, switches screens
│   ├── menu.gd               pick departments, brains, mode
│   ├── match.gd              plays back events from Python
│   ├── board.gd              draws tiles, search highlights, routes
│   ├── unit_piece.gd         one unit on the board
│   ├── card_view.gd          one card
│   ├── thinking_panel.gd     top choices and counters for one side
│   ├── bridge.gd             runs the Python bridge on a thread
│   └── ui.gd, sfx.gd         colours, fonts, generated sounds
├── ai/                       Python: all rules and all AI
│   ├── bridge.py             the only file Godot runs
│   ├── play.py               the whole game in the terminal
│   ├── balance_check.py      plays many matches, reports fairness and timing
│   ├── kuet_royale/
│   │   ├── grid.py           map, terrain costs, neighbours
│   │   ├── search.py         breadth_first, uniform_cost, best_first, a_star
│   │   ├── fuzzy.py          the three-rule target system
│   │   ├── deck_csp.py       backtracking with MRV and LCV
│   │   ├── game.py           State, actions, result, terminal, utility, battle step
│   │   ├── alphabeta.py      max_value, min_value with alpha and beta
│   │   ├── mcts.py           Node, ucb1, rollout, backpropagate
│   │   └── engine.py         match bookkeeping and the event list
│   ├── data/
│   │   ├── map.json
│   │   ├── cards_cse.json
│   │   └── cards_me.json
│   └── tests/                one test file per algorithm
└── docs/                     report and slides
```

---

## 11. Running it (once built)

Watch a match in the terminal:

```bash
cd ai && python3 play.py --left cse --right me
```

Run the tests:

```bash
cd ai && python3 -m unittest discover -s tests
```

Check fairness and thinking time:

```bash
cd ai && python3 balance_check.py
```

Open the game:

```bash
godot --path .
```

---

## 12. Two-week plan

| Days | Dates | Goal | Done when |
|---|---|---|---|
| 1 to 2 | 10 to 11 Oct | Rules frozen. Grid, battle step and the four path searches, with tests. | Each search returns a route that can be checked by hand on the map above |
| 3 to 4 | 12 to 13 Oct | Alpha-beta and MCTS play full matches in the terminal. Timing measured. Balance check. | A whole AI against AI match prints in the terminal; first-move thinking time is known |
| 5 to 7 | 14 to 16 Oct | Godot screen: board, units moving, towers, cards, thinking panels. | A match can be watched start to finish in Godot |
| 8 to 9 | 17 to 18 Oct | Fuzzy targeting, CSP deck building, menu. | All eight algorithms run in a real match |
| 10 to 11 | 19 to 20 Oct | Search tiles lighting up, commentary, speed control, pick a winner. | A stranger can follow a match without help |
| 12 | 21 Oct | Human play, EEE and CE cards. Only if everything above works. | |
| 13 to 14 | 22 to 23 Oct | No new features. Report, slides, viva practice. | Each teammate can explain four algorithms |

**Roles:** one teammate owns the Python algorithms. The other owns Godot, the card data and the report. Both must be able to explain every algorithm they present.

**If it slips:** on day 7, if a full AI against AI match does not run in the terminal, cut in this order: human play, extra departments, commentary, pick a winner. Then shrink the hand to three cards.

---

## 13. What changed from the original plan, and why

The first plan is in `kuet_royale_implementation_plan.md`, `kuet_royale_gameplay_flow.md` and `kuet_royale_algorithm_guide.md`. Where they differ from this file, this file wins.

| Original plan | Now | Why |
|---|---|---|
| Real time, a decision every 500 ms, both sides at once | Strict turns with a battle animation between them | Alpha-beta needs turns. It still looks like a live battle. |
| Hidden hands, shuffled decks | Both decks face up, no shuffling | The taught algorithms assume everything is visible and nothing is random |
| Alpha-beta cut off at depth 3 with an evaluation function | Alpha-beta to the end of the match | Not sure an evaluation function was taught, so none is needed |
| MCTS with guessed hidden hands, guided rollouts, 5-tick cut-off | MCTS exactly as on the slides | Only the plain version was taught |
| 32 x 20 map | 13 x 7 map | Small enough to follow a search by eye |
| Four departments, 56 cards, spells, buildings, many abilities | Two departments, 16 cards, one ability | Two weeks |
| Energy that refills during the match | Energy is only the deck's cost limit | Fewer things to track; the deck builder uses it |
| PDDL planner picks the deck | CSP backtracking picks the deck | A planner program was not taught; CSP was |
| UCS "when the heuristic is unreliable" | UCS picks the nearest target | A* stays correct after terrain changes, so that reason would not survive a viva |
| Breadth-first only for blast areas | Breadth-first for hover units and blast areas | Gives it a real pathfinding job |
| 15 fuzzy rules, four inputs | 3 fuzzy rules, two inputs | Has to be recited and justified from memory |
| TCP server with a mirrored game state | Python is run once per decision | No second copy of the game to keep in sync |
| 14 weeks | 2 weeks | The deadline |

Kept from the original: the theme, the department personalities, the lane-and-tower shape, most card names, and the idea that every algorithm has a visible job.

---

## 14. Ground rules for whoever builds this

These apply to both teammates and to any AI assistant helping.

1. **Only techniques taught in the course,** used the way they were taught. If something is not in the table in section 6, do not add it.
2. **Alpha-beta searches to the end.** No depth limit, no evaluation function.
3. **MCTS stays as on the slides.** UCB1 with C = 2, expand all, random rollout to the end, back up.
4. **The rules have no hidden information, no chance and no simultaneous moves.**
5. **The fuzzy system stays at three rules,** worked by hand, no library.
6. **Every rule lives in Python.** Godot draws and nothing else.
7. **Whole numbers everywhere,** so results can be checked by hand.
8. **A new card is data only.** If a card needs new code, it does not go in.
9. **Measure before believing.** No timing or balance claim goes in the report until `balance_check.py` has produced it.

---

## 15. Open questions

| Question | Why it matters | When |
|---|---|---|
| How long does alpha-beta take on the first move? | Decides four cards or three | Day 3 |
| Does the side that moves first win too often? | May need the two sides to swap seats between matches | Day 4 |
| Do the card numbers give close matches? | Every *starting value* in this file is untested | Day 4 |
| Were UCS and breadth-first search in the lab or the theory class? | The viva answer for "where was this taught?" | Before the viva |
| Was an evaluation function taught with alpha-beta? | Not needed by this design, but good to know | Before the viva |

---

## 16. Words used in this file

| Word | Meaning |
|---|---|
| Card | One unit a department can play once per match |
| Deck | The four cards a department brings |
| Roster | All eight cards a department owns |
| Lane | One of the two roads across the map |
| Battle step | One round in which every unit does one thing |
| Card turn | One department playing one card |
| Brain | The algorithm that picks cards for a department (alpha-beta or MCTS) |
| Rollout | One random play-through to the end of the match, used by MCTS |
| Pruned | A branch alpha-beta skipped because it could not change the answer |
| Terrain cost | The price of stepping onto a tile |
| Heuristic | A quick guess of the remaining distance (here: steps to the goal) |
| Starting value | A number chosen to begin with and not yet tested |
