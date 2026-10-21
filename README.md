# KUET Royale: Department Wars

A small strategy game where two KUET departments fight across a campus battlefield, and two different AI algorithms do the thinking. It is the course project for CSE 3210: Artificial Intelligence Lab.

| | |
|---|---|
| **Status** | Built and playable: the Godot game with 32 warrior figures, the same game in the terminal, a balance checker, 111 automated tests and a scripted player that clicks through a whole match. See [what is and is not checked](#15-what-is-and-is-not-checked). |
| **Must have** | AI against AI, fun to watch. Built. |
| **Bonus** | A person against an AI. Built. |
| **Departments** | CSE, EEE, ME and CE |
| **Team** | Two students |
| **Numbers** | Every figure in this file comes from `ai/balance_check.py` or the tests, run on 10 October 2026 |

---

## 1. The game in one minute

1. Two departments face each other. Each has one **tower** and brings **four cards**. Every card is one unit.
2. They take turns. On your turn you play one card into the **top lane** or the **bottom lane**.
3. Units then walk and fight by themselves. Whoever does more damage to the enemy tower wins.

That is the whole game. Nobody steers a unit after it is played. All the thinking is in three choices: which card, which lane, and in what order.

One department thinks with **alpha-beta search**. The other thinks with **Monte Carlo Tree Search**. So every match is also one algorithm against another. You can also take a side yourself.

### How to play

1. In the menu, pick two departments and who thinks for each: **Alpha-beta**, **MCTS** or **You**. Leave both on an AI to watch.
2. On your turn, **click one of your cards**, then **click the left or right lane** on your half of the arena.
3. Stuck? **Hint** asks alpha-beta for the best card and lane.
4. **1x, 2x, 4x**, **Pause** and **Step** let you stop on any move and explain it.

Every card says in one plain sentence what it is good for, for example "Slow wall that hits hard. Play it first."

### Two legs

A match is played twice, like a home and away tie in football. In the first leg the left side plays first; in the second leg the right side does. The damage from both legs is added.

The reason is measured, not guessed: the side that plays second can always answer the other side's card. Under perfect play it comes out about 3 to 5 points ahead in a single leg (section 14). Two legs cancel that edge.

---

## 2. How a leg works

| Step | What happens | Who decides |
|---|---|---|
| 1. Deck building | Each department's four cards are chosen from its roster of eight. | CSP solver |
| 2. Card turn | The side to play puts one unused card into the top or bottom lane. The unit appears on that lane's start tile. There is no passing. | Alpha-beta, MCTS or a person |
| 3. Battle steps | The battle runs for 3 steps. | The rules |
| 4. Repeat | Steps 2 and 3 alternate until all eight cards are played. | |
| 5. Final battle | After the last card the battle runs for up to 15 more steps, or until no unit is left. | The rules |
| 6. Result | Each side's score is the damage it did to the enemy tower. | |

Both decks lie face up the whole time. Nothing is hidden and nothing is random in the rules.

### What one unit does in one battle step

Every unit does exactly one thing per step:

1. **Is an enemy in range?** Then attack. If several are in range, the fuzzy system picks which one.
2. **Otherwise, pick where to go.** The destination is the enemy unit, or the tile next to the enemy tower, that is cheapest to reach.
3. **Walk.** The unit gets `speed` movement points. Stepping onto a tile costs that tile's price. Points it cannot spend yet are saved for the next step, so a speed-1 unit needs two steps to enter grass and four to enter mud. It stops as soon as an enemy is in range.

Towers fight too. Each step a tower hits the closest enemy within 2 tiles for 2 damage.

All attacks in a step are worked out from where everything stood at the start of the step, and they land together. So the order units are processed in never favours one side.

Several units may stand on the same tile. That avoids traffic-jam rules.

### The numbers

| Rule | Value |
|---|---|
| Tower health | 20 |
| Tower range and damage | 2 tiles, 2 per step |
| Battle steps after each card | 3 |
| Extra battle steps after the last card | up to 15 |
| Cards per deck | 4 |
| Deck cost | 13 or 14 |

---

## 3. The battlefield

A grid 13 tiles wide and 7 tall, as stored in `ai/data/map.json`: left department on the left, right department on the right, a river down the middle.

**On screen the arena stands upright:** the left department is at the top, the right department at the bottom, and what the map file calls the top lane is the lane on the left. Only the drawing is turned; the rules never change. The map is a mirror image, so neither side is favoured by it.

```
       0  1  2  3  4  5  6  7  8  9  10 11 12
row 0  .  .  .  .  .  .  ~  .  .  .  .  .  .
row 1  .  S  =  =  =  =  B  =  =  =  =  S  .     top lane
row 2  .  =  .  .  m  .  ~  .  m  .  .  =  .
row 3  T  =  .  m  m  .  ~  .  m  m  .  =  T
row 4  .  =  .  .  m  .  ~  .  m  .  .  =  .
row 5  .  S  =  =  =  =  B  =  =  =  =  S  .     bottom lane
row 6  .  .  .  .  .  .  ~  .  .  .  .  .  .
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

A worked example you can check on the map: from (3,1) to (3,5).

| Search | Route | Cost |
|---|---|---|
| A* | Round by the road through (1,1) and (1,5) | 8 |
| Best-first | Straight down: grass, mud, grass, road | 9 |
| Breadth-first (hover) | Straight down, 4 steps | 4 steps |

---

## 4. Cards and units

### The six numbers on a card

| Number | Meaning |
|---|---|
| Cost | Energy price. Only matters when building a deck. |
| Health | Damage it can take before it is removed. |
| Damage | Health it removes per attack. |
| Range | How many tiles away it can hit (counted as steps left/right/up/down). Range ignores terrain, so shooting over the river is allowed. |
| Speed | Movement points per battle step. |
| Role | Tank, Ranged or Fast. Used by the deck builder. |

### How a unit walks

Each unit has one walking style. This is the heart of the pathfinding part of the project.

| Style | What it means | Algorithm |
|---|---|---|
| Careful (most units) | Takes the cheapest route, counting road, grass and mud. | A* |
| Reckless | Heads straight at the goal and may wade through mud. | Best-first search |
| Hover | Floats, so every tile costs 1. Fewest steps wins. | Breadth-first search |

### The only special ability

**Splash:** the attack also hurts every enemy within 1 step of the target. The area is found with breadth-first search.

That is all. No spells, no buildings, no healing, no other abilities. A new card is only a new row of numbers in a JSON file.

### The four rosters

**CSE: fast, cheap and clever.**

| Card | Cost | Health | Damage | Range | Speed | Walks | Role |
|---|---|---|---|---|---|---|---|
| Compiler | 5 | 10 | 3 | 1 | 1 | Careful | Tank |
| Kernel | 5 | 13 | 2 | 1 | 1 | Careful | Tank |
| Algorithmist | 3 | 5 | 2 | 3 | 1 | Careful | Ranged |
| Optimizer | 4 | 5 | 3 | 2 | 1 | Careful | Ranged |
| Logic Bomber | 4 | 5 | 2 | 3 | 1 | Careful, Splash | Ranged |
| Debugger | 2 | 4 | 2 | 1 | 2 | Careful | Fast |
| Stack Runner | 2 | 3 | 2 | 1 | 3 | Reckless | Fast |
| Cloud Drone | 3 | 4 | 2 | 2 | 2 | Hover | Fast |

**EEE: hits hard, breaks easily.**

| Card | Cost | Health | Damage | Range | Speed | Walks | Role |
|---|---|---|---|---|---|---|---|
| Capacitor | 5 | 13 | 2 | 1 | 1 | Careful | Tank |
| Transformer | 4 | 10 | 3 | 1 | 1 | Careful | Tank |
| Signal Processor | 4 | 4 | 3 | 3 | 1 | Careful | Ranged |
| Circuit Engineer | 3 | 5 | 2 | 3 | 1 | Careful | Ranged |
| Oscillator | 5 | 5 | 2 | 2 | 1 | Careful, Splash | Ranged |
| Power Engineer | 3 | 5 | 3 | 1 | 2 | Careful | Fast |
| Relay Runner | 2 | 3 | 2 | 1 | 3 | Reckless | Fast |
| Electron | 3 | 3 | 3 | 1 | 3 | Hover | Fast |

**ME: heavy, slow and hard to stop.**

| Card | Cost | Health | Damage | Range | Speed | Walks | Role |
|---|---|---|---|---|---|---|---|
| Heavy Machine | 5 | 14 | 2 | 1 | 1 | Careful | Tank |
| Gearwheel Guard | 4 | 11 | 2 | 1 | 1 | Careful | Tank |
| Robotic Arm | 4 | 4 | 3 | 3 | 1 | Careful | Ranged |
| Steel Rain Cannon | 5 | 6 | 2 | 3 | 1 | Careful, Splash | Ranged |
| Mech Warrior | 3 | 7 | 2 | 1 | 2 | Careful | Fast |
| Gear Runner | 2 | 4 | 2 | 1 | 3 | Reckless | Fast |
| Mini-Bot | 2 | 3 | 2 | 1 | 2 | Reckless | Fast |
| Quadcopter | 3 | 4 | 2 | 2 | 2 | Hover | Fast |

**CE: slow to arrive, slower to leave.**

| Card | Cost | Health | Damage | Range | Speed | Walks | Role |
|---|---|---|---|---|---|---|---|
| Excavator | 5 | 15 | 2 | 1 | 1 | Careful | Tank |
| Road Roller | 4 | 11 | 2 | 1 | 1 | Reckless | Tank |
| Site Engineer | 3 | 5 | 2 | 3 | 1 | Careful | Ranged |
| Crane Operator | 4 | 6 | 3 | 2 | 1 | Careful | Ranged |
| Seismic Crew | 5 | 6 | 2 | 2 | 1 | Careful, Splash | Ranged |
| Surveyor | 2 | 5 | 2 | 1 | 2 | Careful | Fast |
| Construction Crew | 2 | 3 | 2 | 1 | 3 | Reckless | Fast |
| Survey Drone | 3 | 4 | 2 | 2 | 2 | Hover | Fast |

These numbers were tuned with the balance checker until the departments came out close (section 14).

### Deck rules

A deck is four cards from the department's eight:

- one **Tank**, one **Ranged**, one **Fast**, and one **free** slot (any card);
- no card twice;
- total cost of 13 or 14.

Example: Compiler (5) + Algorithmist (3) + Debugger (2) + Cloud Drone (3) = 13.

---

## 5. Winning

| Situation | Result |
|---|---|
| A tower reaches 0 health | The leg ends at once |
| A leg ends | Each side scores the damage it did to the enemy tower |
| Both legs are over | The side with more total damage wins the match |
| Same total | Draw |

Inside one leg, the number both AIs push their way is **left tower health minus right tower health at the end of the leg**. It is a real final score, read off a finished leg. It is not an estimate of an unfinished one.

After each leg the game names the **turning point**: the one card that cost its side the most, compared with what alpha-beta says was the best card at that moment.

---

## 6. The AI: eight algorithms, eight jobs

Every algorithm answers one clear question. All eight were taught in the course.

| # | Algorithm | The question it answers | Runs when | Taught in | Where in the code |
|---|---|---|---|---|---|
| 1 | A* | What is the cheapest route to that tile? | A careful unit gets a destination | Lab 03 | `search.py` |
| 2 | Best-first search | Which way looks closest to the goal? | A reckless unit gets a destination | Lab 03 | `search.py` |
| 3 | Breadth-first search | What is the fewest-steps route? Which tiles are within 1 step? | A hover unit moves; a splash attack lands | Course | `search.py` |
| 4 | Uniform-cost search | Which enemy is cheapest to reach? | A unit has nobody in range | Course | `search.py` |
| 5 | Fuzzy inference | Several enemies are in range. Which one do I hit? | A unit attacks | Lab 05 | `fuzzy.py` |
| 6 | Alpha-beta search | Which card and lane give the best final score? | One department's card turn | Theory (built on Lab 04 minimax) | `alphabeta.py` |
| 7 | Monte Carlo Tree Search | Which card and lane win most often in play-outs? | The other department's card turn | Lab 08 | `mcts.py` |
| 8 | CSP backtracking | Which four cards make a legal deck? | Once, before the match | Lab 06 | `deck_csp.py` |

For numbers 3 and 4, write down whether each was in the lab or the theory class, so the answer is ready in the viva.

### 6.1 A* (careful units)

- **Score of a tile:** `f = g + h`. `g` is the terrain cost walked so far. `h` is the straight step count to the goal (Manhattan distance).
- **Why the answer is the cheapest route:** the cheapest tile costs 1, so `h` never says more than the true remaining cost.
- **Checked:** on 300 random pairs of tiles A* returns exactly the cost uniform-cost search returns, and never explores more tiles.
- **Say in the viva:** "A* finds the cheapest route because it adds what it has already paid to an honest guess of what is left."

### 6.2 Best-first search (reckless units)

- **Score of a tile:** `f = h` only. It ignores what it has already paid.
- **Effect:** quick and direct, but it will happily walk into mud. The game says so when it happens: "Stack Runner takes the greedy route: it costs 25 where A* would pay 12."
- **Say in the viva:** "Best-first is greedy. Put a Stack Runner next to a Debugger and you can see greedy against optimal on the same map."

### 6.3 Breadth-first search (hover units and splash)

- **Hover routing:** a hover unit pays 1 for every tile, so the best route is the one with the fewest steps. Breadth-first search explores one step further each round, so the first time it reaches the goal is the fewest-steps route.
- **Splash area:** start at the target tile and spread out one step. Every enemy on those tiles is hurt.
- **Say in the viva:** "When every step costs the same, breadth-first search already gives the shortest path. No priority queue is needed."

### 6.4 Uniform-cost search (choosing a destination)

- **The problem:** a unit must go to the nearest enemy, but it does not yet know which enemy that is. There are several possible goals: every enemy unit, and the tiles next to the enemy tower.
- **How:** spread out from the unit in order of total travel cost. The first goal tile taken off the queue is the destination.
- **Why not A\*:** A* needs one known goal to aim its guess at. Here there is no single goal yet.
- **Say in the viva:** "Uniform-cost search expands the cheapest tile first, so the first enemy it reaches is the cheapest enemy to reach."

(Hover units ignore terrain cost, so they use breadth-first search for this step as well.)

### 6.5 Fuzzy inference (choosing a target)

Used only when a unit has more than one enemy in range. Done the way Lab 05 does it by hand: straight-line shapes, OR means take the larger, clip each output shape, combine, and take the centre of the area over sample points. No library. The lab's own tip example (service 3, food 6, tip about 16) is reproduced in the tests.

- **Inputs:** how far the enemy is, in tiles (near, medium, far), and how much health it has left, in percent (low, medium, full).
- **Output:** attack priority from 0 to 100. The unit hits the enemy with the highest number.

The whole rule base is three rules:

```
IF distance is near    OR  health is low     THEN priority is high
IF distance is medium  OR  health is medium  THEN priority is medium
IF distance is far     OR  health is full    THEN priority is low
```

The shapes, all straight lines:

| Variable | Term | Corner points (value, degree) |
|---|---|---|
| Distance (0 to 4 tiles) | near | (0, 1) (2, 0) |
| | medium | (0, 0) (2, 1) (4, 0) |
| | far | (2, 0) (4, 1) |
| Health (0 to 100 %) | low | (0, 1) (50, 0) |
| | medium | (0, 0) (50, 1) (100, 0) |
| | full | (50, 0) (100, 1) |
| Priority (0 to 100) | low | (0, 1) (25, 1) (45, 0) |
| | medium | (25, 0) (50, 1) (75, 0) |
| | high | (55, 0) (75, 1) (100, 1) |

One case worked by hand: an enemy 1 tile away with half its health left. Near = 0.5, medium distance = 0.5, far = 0. Low = 0, medium health = 1, full = 0. So high = max(0.5, 0) = 0.5, medium = max(0.5, 1) = 1, low = 0. The centre of the combined shape is 63.5.

- **Say in the viva:** "Finish off what is close and nearly dead. Fuzzy logic lets 'close' and 'nearly dead' be matters of degree instead of hard cut-offs."

### 6.6 Alpha-beta search (one department's brain)

- **A move** is a pair: (card, lane).
- **Shape:** the Lab 04 minimax program (`State`, `actions`, `result`, `terminal`, `utility`, `max_value`, `min_value`) with the two extra values alpha and beta from the theory class.
- **It searches to the very end of the leg.** There is no depth limit and no evaluation function. `utility` is the tower health difference of a finished leg.
- **Pruning:** when a branch cannot change the final choice, it is skipped. The screen counts skipped moves.
- **Checked:** the tests compare it with plain minimax written as in Lab 04. The two always give the same score.
- **Measured:** for the first card of a leg it looks at about 10,300 positions, where plain minimax would need up to 270,025. That takes about 0.2 seconds.
- **Say in the viva:** "Alpha-beta returns exactly what plain minimax would return. It only skips branches that cannot matter."

### 6.7 Monte Carlo Tree Search (the other department's brain)

Exactly the four steps on the Lab 08 slides:

1. **Select** by UCB1: `t/n + C * sqrt(ln N / n)` with `C = 2`.
2. **Expand** all moves of a visited leaf.
3. **Roll out:** play random legal cards to the end of the leg.
4. **Back up:** add 1 to `n` and the result to `t` on the way up.

It repeats this 1,500 times per card, which takes about 0.15 seconds. Nothing was added for the opponent, because the slides teach nothing about one. So this brain imagines the other side will be helpful. It gambles, and that is why alpha-beta usually beats it.

- **Say in the viva:** "MCTS never looks at every line. It plays many random legs and spends more of them on the cards that keep doing well."

### 6.8 CSP backtracking (deck building)

- **Variables:** the four deck slots (Tank, Ranged, Fast, Free).
- **Domains:** the roster cards allowed in each slot.
- **Constraints:** all four different; total cost 13 or 14.
- **Search:** backtracking as in Lab 06, with **MRV** (fill the slot that has the fewest cards left to choose from) and **LCV** (try the card that leaves the other slots the most choices).
- **Honest note:** with the real rosters MRV and LCV choose so well that the solver almost never has to take a card back. A test builds a small roster where it must, to show the backing-up works.
- **Say in the viva:** "A deck is a small constraint problem. The two orderings are there so the solver rarely walks into a dead end."

### 6.9 Why the game is this small

Alpha-beta has to reach the end of the leg, so the leg must be short.

- First card: 4 cards x 2 lanes = 8 choices. Then 8 for the other side, then 6, 6, 4, 4, 2, 2.
- 8 x 8 x 6 x 6 x 4 x 4 x 2 x 2 = **147,456 complete legs** at most, and 270,025 positions counting the ones on the way.

### 6.10 The notebook of search answers

The map never changes, so a search from one tile to another always gives the same answer. `routes.py` keeps each answer after the real search in `search.py` has worked it out once. It decides nothing. The tests check that what it remembers is exactly what the real search returns. This is what lets the brains look ahead through thousands of legs in a fraction of a second.

### 6.11 Why turns, open hands and no dice

Alpha-beta and MCTS as taught assume players alternate, everything is visible, and nothing is left to chance. The game is built to fit those assumptions, so each algorithm can be used exactly as taught.

### 6.12 Choices that are ours, not the course's

Say these openly if asked:

- The score of a leg is the tower health difference, and a match is two legs.
- MCTS runs 1,500 rollouts per card and plays the card with the best average result.
- MCTS scores a rollout as 1 for a win, 0.5 for a draw, 0 for a loss, to the side that is searching.
- The shapes of the fuzzy terms, the map, the terrain costs and the card numbers.
- The four deck slots and the cost limits.
- Movement points, and that a fuzzy priority is rounded to one decimal place so that equal enemies are exactly equal.

---

## 7. What you see on screen

```
+--------------------+  +-----------+  +--------------------+
| CSE        score   |  |  castle   |  | ME         score   |
| top side, thinks   |  |  .  |  .  |  | bottom side,       |
| with Alpha-beta    |  |  .  |  .  |  | thinks with MCTS   |
| tower health       |  | ~~[=]~~[=]|  | tower health       |
| four cards on a    |  |  .  |  .  |  | four cards on a    |
| wooden tray        |  |  .  |  .  |  | wooden tray        |
| what its brain     |  |  castle   |  | what its brain     |
| thought            |  |           |  | thought            |
+--------------------+  +-----------+  +--------------------+
| one sentence about what happened  |  colour key of the searches |
+-------------------------------------------------------------+
```

- **The arena** stands upright in the middle: checkerboard grass, dirt lanes, mud, a river with two wooden bridges, and a stone castle at each end with its health on it.
- **Thirty-two warriors**, one per card, drawn in code from simple shapes: CSE cyber knights, EEE storm warriors, ME iron warriors and war machines, CE earth warriors with two war scorpions. They walk, bob, and swing their weapons when they attack. `--gallery` shows them all.
- **Side panels:** each department's score, tower health, its four cards on a wooden tray, and what its brain thought. Alpha-beta shows the final score each card can force and how many positions it skipped. MCTS shows how many random legs each card won.
- **Cards** show the figure, the cost, health, damage, range and speed, how the unit walks, and one plain sentence saying what it is good for.
- **Visible search:** tiles light up in the order a search explored them, one colour per algorithm, and the route is drawn.
- **Fuzzy priorities** float above the enemies when a unit has to choose a target.
- **Commentary:** one plain sentence per event, in the strip along the bottom.
- **Pick a winner:** before an AI against AI match you can back a side.
- **Turning point:** after each leg, the card that decided it.
- **Speed control** (1x, 2x, 4x), pause and single-step, so a match can be explained live.
- **How the AI works:** a page in the menu listing the eight algorithms and their jobs.

### Modes

| Mode | What it is |
|---|---|
| AI against AI | Pick two departments and give each a brain, then watch |
| You against AI | Choose "You" for one side. Click a card, click a lane. The Hint button asks alpha-beta |

---

## 8. Tech stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Game screen | Godot, GDScript | 4.7.2 | Free, small, good at 2D |
| Rendering | 2D, Compatibility renderer, 1280 x 720 | | Runs on any lab laptop |
| Rules and all AI | Python, standard library only | 3.9 or newer | The labs are in Python, so the code looks like the lab code |
| Priority queue | `heapq` | built in | A*, best-first and uniform-cost search, as in Lab 03 |
| Plain queue | `collections.deque` | built in | Breadth-first search |
| Randomness | `random` with a seed | built in | MCTS rollouts and the order the roster is read in; a seed makes a match repeatable |
| Data | JSON files | | Map and cards can be edited without touching code |
| Godot to Python link | Godot starts `python3 ai/bridge.py` once per decision and reads JSON back | | No server, no sockets, nothing to keep in sync |
| Tests | `unittest` | built in | One test file per part |
| Art | Arena, castles and 32 warriors drawn in code from simple shapes | | No art files to make or license |
| Sound | Short tones generated in code | | No sound files |

**No extra installs.** No `pip` packages are needed.

**Deliberately not used:**

| Not used | Why |
|---|---|
| A network server between Godot and Python | Needed only for real-time play; this game is turn-based |
| A PDDL planner | Only PDDL syntax was taught; deck building is done with CSP instead |
| Fuzzy or search libraries (scikit-fuzzy, networkx) | The course teaches these by hand; the code must show the method |
| Machine learning | Not in the course |

**Machines:** developed on macOS with Python 3.9.6 and 3.13.9. It has not been run on Windows or Linux. The bridge looks for `python3`, then `python`; set the `KUET_ROYALE_PYTHON` environment variable to point it at a particular one.

---

## 9. How the parts fit together

```
        Godot (screen only)                      Python (all rules, all AI)
  +---------------------------+            +--------------------------------+
  | menu, board, units,       |  request   | bridge.py                      |
  | cards, thinking panels,   | ---------> |   reads the match file         |
  | animations, sound         |            |   asks the right brain         |
  |                           |  JSON:     |   plays the card               |
  | plays back the list of    |  steps +   |   runs the battle steps        |
  | steps it is given         |  new view  |   writes the match file        |
  |                           | <--------- |   answers in JSON              |
  +---------------------------+            +--------------------------------+
                                                         |
                                           match file (one JSON per match)
```

**One source of truth.** Every rule lives in Python. Godot never decides anything; it only draws what it is told. So the game is built once, not twice, and the terminal version and the Godot version cannot disagree.

**The match file stores only the moves played.** The position is rebuilt by playing them again, which is safe because nothing in the rules is random.

### Bridge commands

| Command | Does |
|---|---|
| `departments` | Lists departments, their cards and the brains |
| `new --left cse --right me --left-brain alphabeta --right-brain mcts` | Builds both decks and opens leg 1 |
| `step` | Lets the side to play think, plays its card, runs the battle steps |
| `step --card 2 --lane top` | The same, with a person's choice |
| `next` | Opens leg 2 |
| `hint` | What alpha-beta would play |
| `view` | Returns the match as it stands, changing nothing |

### What a `step` answer holds

| Key | Holds |
|---|---|
| `thinking` | The brain's choices: scores and counts for alpha-beta, win shares and visits for MCTS |
| `move` | The card and lane played |
| `deployed` | The new unit |
| `steps` | One entry per battle step: searches, moves, attacks, tower shots, damage, who is out, and a snapshot of every unit |
| `comments` | The commentary sentences, each tagged with the battle step it belongs to |
| `view` | Everything the screen needs to draw the match as it now stands |

If a call ever fails to come back within 15 seconds, the screen looks at the match again and carries on instead of freezing.

---

## 10. Folder layout

```
KUET-Royale/
├── README.md                 this file
├── project.godot             Godot project
├── main.tscn
├── scripts/                  Godot: drawing only
│   ├── main.gd               starts the menu, switches screens
│   ├── menu.gd               pick departments and brains; "How the AI works"
│   ├── match.gd              asks for the next card and plays back what happened
│   ├── board.gd              draws the upright arena, search highlights, routes, castles
│   ├── characters.gd         the 32 warrior figures, drawn from simple shapes
│   ├── unit_piece.gd         one unit on the board
│   ├── card_view.gd          one card
│   ├── thinking_panel.gd     one side: tower, damage, what its brain thought
│   ├── bridge.gd             runs the Python bridge on a thread
│   ├── ui.gd                 colours, fonts, small helpers
│   ├── sfx.gd                generated sounds
│   ├── gallery.gd            a sheet of every figure (--gallery)
│   └── ui_test.gd            a scripted player that clicks through a match (--uitest)
└── ai/                       Python: all rules and all AI
    ├── bridge.py             the only file Godot runs
    ├── play.py               the whole game in the terminal
    ├── balance_check.py      plays many matches, reports fairness and thinking time
    ├── show_map.py           prints the map and the rosters
    ├── kuet_royale/
    │   ├── grid.py           map, terrain costs, neighbours
    │   ├── cards.py          loads and checks a department's cards
    │   ├── search.py         breadth_first, uniform_cost, best_first, a_star
    │   ├── routes.py         remembers search answers
    │   ├── fuzzy.py          Mamdani inference by hand, and the three-rule target system
    │   ├── deck_csp.py       backtracking with MRV and LCV
    │   ├── game.py           State, actions, result, terminal, utility, battle step
    │   ├── alphabeta.py      max_value, min_value with alpha and beta
    │   ├── mcts.py           Node, ucb1, rollout, backpropagate
    │   └── engine.py         a whole match: decks, two legs, commentary, turning point
    ├── data/
    │   ├── map.json
    │   └── cards_cse.json, cards_eee.json, cards_me.json, cards_ce.json
    └── tests/                110 tests, one file per part
```

---

## 11. Running it

### The game

Once, after downloading the project:

```bash
godot --headless --path . --import
```

Then:

```bash
godot --path .
```

Or open the folder in the Godot editor and press Play.

Self-running demos, useful for a presentation:

```bash
godot --path . -- --watch
```

```bash
godot --path . -- --watch --left eee --right ce --speed 2
```

```bash
godot --path . -- --play
```

`--watch` goes straight into alpha-beta against MCTS and closes its own pop-ups. `--play` puts a "person" on the left who plays whatever alpha-beta suggests. `--seed 7` makes either one the same match every time.

All 32 warrior figures on one sheet:

```bash
godot --path . -- --gallery
```

### In the terminal

```bash
cd ai && python3 play.py
```

```bash
cd ai && python3 play.py --left me --right ce --left-brain human
```

### Checks

```bash
cd ai && python3 -m unittest discover -s tests
```

```bash
cd ai && python3 balance_check.py
```

```bash
cd ai && python3 show_map.py
```

A scripted player that clicks through a whole match (menu, Hint, a card, a lane, Pause, Step, Resume, 4x, both result sheets) and prints PASS or FAIL for each:

```bash
godot --headless --path . -- --uitest
```

---

## 12. Adding a department or a card

1. Copy `ai/data/cards_me.json` to `ai/data/cards_<name>.json`.
2. Change the names and numbers. Keep eight cards: at least two Tanks, two Ranged and two Fast, all three walking styles, and exactly one splash card.
3. Run the tests. They check every card file they find.
4. Run `balance_check.py` and adjust the numbers until the new department wins roughly half its matches.

No code changes are needed. The menu finds the file by itself.

---

## 13. What changed from the original plan, and why

The first plan is in `kuet_royale_implementation_plan.md`, `kuet_royale_gameplay_flow.md` and `kuet_royale_algorithm_guide.md`. Where they differ from this file, this file wins.

| Original plan | Now | Why |
|---|---|---|
| Real time, a decision every 500 ms, both sides at once | Strict turns with a battle animation between them | Alpha-beta needs turns. It still looks like a live battle. |
| Hidden hands, shuffled decks | Both decks face up, no shuffling | The taught algorithms assume everything is visible and nothing is random |
| One match | Two legs, each side starting once | The side that plays second has a measured edge |
| Alpha-beta cut off at depth 3 with an evaluation function | Alpha-beta to the end of the leg | Not sure an evaluation function was taught, so none is needed |
| MCTS with guessed hidden hands, guided rollouts, 5-tick cut-off | MCTS exactly as on the slides | Only the plain version was taught |
| 32 x 20 map | 13 x 7 map | Small enough to follow a search by eye |
| 56 cards, spells, buildings, many abilities | 32 cards, one ability | Every card is data only, and every rule can be explained |
| Energy that refills during the match | Energy is only the deck's cost limit | Fewer things to track; the deck builder uses it |
| PDDL planner picks the deck | CSP backtracking picks the deck | A planner program was not taught; CSP was |
| UCS "when the heuristic is unreliable" | UCS picks the nearest target | A* stays correct after terrain changes, so that reason would not survive a viva |
| Breadth-first only for blast areas | Breadth-first for hover units and blast areas | Gives it a real pathfinding job |
| 15 fuzzy rules, four inputs | 3 fuzzy rules, two inputs | Has to be recited and justified from memory |
| TCP server with a mirrored game state | Python is run once per decision | No second copy of the game to keep in sync |

Kept from the original: the theme, the four departments and their personalities, the lane-and-tower shape, most card names, and the idea that every algorithm has a visible job.

Eight cards are new: Cloud Drone, Quadcopter, Electron and Survey Drone are the hover units; Logic Bomber, Steel Rain Cannon, Oscillator and Seismic Crew are the splash units (some were spells in the original plan).

---

## 14. Measured results

From `python3 balance_check.py` on 10 October 2026. Run it again after any change to a card.

### Thinking time (first card of a leg, the slowest decision)

| Brain | Time | Work |
|---|---|---|
| Alpha-beta | 0.22 s on average, 0.32 s at worst | about 10,300 positions; plain minimax would need up to 270,025 |
| MCTS | 0.15 s | 1,500 random legs |

### Are the departments even?

Both sides play perfectly (alpha-beta against alpha-beta), 80 matches of two legs per pairing, decks from the CSP solver.

| Pairing | First named wins | Second named wins | Level |
|---|---|---|---|
| CSE against EEE | 41% | 53% | 5% |
| CSE against ME | 47% | 41% | 11% |
| CSE against CE | 35% | 53% | 11% |
| EEE against ME | 61% | 33% | 5% |
| EEE against CE | 52% | 45% | 2% |
| ME against CE | 45% | 51% | 3% |

With 80 matches each figure can be off by about 11 points either way, so these say "roughly even", not more. EEE against ME is the least even.

### Does playing first or second matter?

In a single leg, with perfect play, the side that plays first scores between 3.0 and 4.7 points less than the other on average, and about a quarter of legs end level. That is why a match has two legs.

### Is one brain better?

CSE against EEE, 26 matches of two legs each way.

| Match-up | Alpha-beta wins | MCTS wins | Level |
|---|---|---|---|
| Alpha-beta on the left | 88% | 7% | 3% |
| Alpha-beta on the right | 84% | 15% | 0% |

MCTS against a side that plays at random: MCTS wins 92% from the left and 88% from the right. So MCTS plays well, and alpha-beta plays better, which is what the theory says.

---

## 15. What is and is not checked

**Checked by the tests (111, passing on Python 3.9 and 3.13):**

- every hand-worked path cost in this file;
- A* matches uniform-cost search on 300 random pairs of tiles;
- alpha-beta gives exactly plain minimax's score;
- the lab's fuzzy tip example, and one targeting case by hand;
- every deck obeys every constraint, and backtracking really takes a card back when it must;
- every rule of a battle step;
- a whole match of two legs, through the same bridge the screen uses;
- every card has a plain sentence saying what it does.

**Checked by a scripted player (`--uitest`, 30 checks, all passing):** it sends mouse clicks to the screen exactly as a mouse would and plays a whole match as the left side: picks "You" in the menu, starts, asks for a Hint and plays it, selects cards and lanes, pauses, steps, resumes, switches to 4x, and reaches both result sheets.

**Checked by running the game itself:** complete matches in AI against AI mode and in the self-playing "person" mode ran from the menu to the final screen with no script errors, and frames of the menu, the intro, a battle, both result screens and the "How the AI works" page were looked at.

**Not checked:**

- No person has played it yet; the clicking above was done by the scripted player.
- Nobody has listened to the sound.
- It has not been run on Windows or Linux.
- Once, in a recorded test run, a call to Python never came back and the screen sat on "Thinking". It could not be made to happen again in seven more runs. A 15-second safety net was added so the game recovers by itself; the safety net itself has not been seen in action.

---

## 16. Ground rules for whoever changes this

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

## 17. Open questions for the viva

| Question | Why it matters |
|---|---|
| Were uniform-cost search and breadth-first search in the lab or the theory class? | The answer to "where was this taught?" |
| Was an evaluation function taught with alpha-beta? | Not needed by this design, but good to know |

---

## 18. Words used in this file

| Word | Meaning |
|---|---|
| Card | One unit a department can play once per leg |
| Deck | The four cards a department brings |
| Roster | All eight cards a department owns |
| Lane | One of the two roads across the map |
| Leg | One game of eight cards. A match is two legs |
| Battle step | One round in which every unit does one thing |
| Card turn | One department playing one card |
| Brain | Whatever picks cards for a department: alpha-beta, MCTS or a person |
| Rollout | One random play-through to the end of the leg, used by MCTS |
| Pruned, skipped | A move alpha-beta did not look at because it could not change the answer |
| Terrain cost | The price of stepping onto a tile |
| Movement points | What a unit spends to step onto a tile; it gets `speed` of them per battle step |
| Heuristic | A quick guess of the remaining distance (here: steps to the goal) |
| Turning point | The card that cost its side the most, compared with the best card at that moment |
