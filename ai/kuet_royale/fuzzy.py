"""Lab 05: a Mamdani Fuzzy Inference System, written by hand.

No library is used, because the lab worked everything out by hand. The steps
are the four from the lab slides, in the same order:

    1. Fuzzification     crisp input -> a degree between 0 and 1 for every term
    2. Rule evaluation   IF ... OR ... THEN ...      (OR = MAX, AND = MIN, NOT = 1 - x)
    3. Aggregation       cap each output term at its rule strength, combine into one set
    4. Defuzzification   centroid = sum(mu(x) * x) / sum(mu(x)) over sample points

The lab's restaurant-tip example is reproduced in tests/test_fuzzy.py:
service = 3 and food = 6 give Tip = (0.5, 0.33, 0.75) and a crisp tip of about 16%.

The game's own system is at the bottom of this file: TARGET, with three rules.
A unit with several enemies in range hits the one with the highest priority.
"""


# --------------------------------------------------------------------------- #
# Step 1: fuzzification
# --------------------------------------------------------------------------- #

def membership(points, x):
    """Degree of membership of x in a term drawn as straight lines between breakpoints.

    points is a list of (x, degree) corners from left to right, for example
    the lab's "good service" triangle is [(2, 0), (5, 1), (8, 0)].
    """
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 <= x <= x2:
            if x2 == x1:
                return max(y1, y2)
            return y1 + (y2 - y1) / (x2 - x1) * (x - x1)   # the two-point line formula
    return 0.0


def fuzzify(variable, x):
    """Crisp value -> fuzzy value: one degree for every term of the variable."""
    return {term: membership(points, x) for term, points in variable.items()}


# --------------------------------------------------------------------------- #
# Step 2: rules
# --------------------------------------------------------------------------- #

def fuzzy_or(x, y):
    return max(x, y)


def fuzzy_and(x, y):
    return min(x, y)


def fuzzy_not(x):
    return 1 - x


def parse_rule(line):
    """Read one rule written the way the lab writes them.

        IF service is poor OR food is bad THEN tip is cheap
        IF distance is near OR health is low THEN priority is high

    Returns (conditions, connective, output_term) where conditions is a list of
    (variable, term, negated). A rule uses OR or AND, never both.

    The lab's own rules use OR, and so do the game's. AND = MIN and NOT = 1 - x
    come from the lab's operator table; writing "is NOT term" is our spelling.
    """
    text = line.strip()
    if not text.startswith("IF ") or " THEN " not in text:
        raise ValueError("A rule must look like: IF x is a OR y is b THEN z is c")
    left, right = text[3:].split(" THEN ")
    output_term = right.split(" is ")[1].strip()

    connective = "OR"
    if " AND " in left:
        connective = "AND"
        if " OR " in left:
            raise ValueError("A rule may use OR or AND, not both: " + line)

    conditions = []
    for part in left.split(" " + connective + " "):
        variable, term = part.split(" is ")
        term = term.strip()
        negated = term.startswith("NOT ")
        if negated:
            term = term[4:].strip()
        conditions.append((variable.strip(), term, negated))
    return conditions, connective, output_term


def rule_strength(rule, degrees):
    """How strongly one rule fires, given the fuzzified inputs."""
    conditions, connective, output_term = rule
    strength = None
    for variable, term, negated in conditions:
        degree = degrees[variable][term]
        if negated:
            degree = fuzzy_not(degree)
        if strength is None:
            strength = degree
        elif connective == "OR":
            strength = fuzzy_or(strength, degree)
        else:
            strength = fuzzy_and(strength, degree)
    return strength


# --------------------------------------------------------------------------- #
# Steps 3 and 4: aggregation and centroid
# --------------------------------------------------------------------------- #

def aggregate(output_variable, strengths, x):
    """Height of the combined output set at x: every term capped at its rule strength."""
    height = 0.0
    for term, points in output_variable.items():
        capped = min(strengths.get(term, 0.0), membership(points, x))
        height = max(height, capped)
    return height


def centroid(output_variable, strengths, samples):
    """Centre of gravity of the aggregate set, as a weighted average over sample points."""
    top = 0.0
    bottom = 0.0
    for x in samples:
        mu = aggregate(output_variable, strengths, x)
        top += mu * x
        bottom += mu
    if bottom == 0:
        return samples[0]   # our fallback if no rule fires at all; it cannot happen with the game's rules
    return top / bottom


# --------------------------------------------------------------------------- #
# The whole pipeline
# --------------------------------------------------------------------------- #

def make_system(name, inputs, output, rule_lines, samples):
    """Bundle one fuzzy inference system.

    inputs     {variable name: {term: breakpoints}}
    output     {term: breakpoints}
    rule_lines text rules; as in the lab, each output term is concluded by one rule
    samples    the evenly spaced output values used for the centroid
    """
    rules = [parse_rule(line) for line in rule_lines]
    concluded = [rule[2] for rule in rules]
    if len(set(concluded)) != len(concluded):
        raise ValueError(name + ": each output term must be concluded by exactly one rule")
    for conditions, _, output_term in rules:
        if output_term not in output:
            raise ValueError(name + ": unknown output term " + output_term)
        for variable, term, _ in conditions:
            if term not in inputs[variable]:
                raise ValueError(name + ": unknown term " + term + " for " + variable)
    return {"name": name, "inputs": inputs, "output": output, "rules": rules,
            "lines": [line.strip() for line in rule_lines], "samples": samples, "memory": {}}


def infer(system, values):
    """Run the four steps and keep every intermediate result, for explanations.

    values is {variable name: crisp number}. Returns a dict with the crisp
    "output", the "strengths" per output term and the "degrees" of every input.
    """
    degrees = {name: fuzzify(variable, values[name]) for name, variable in system["inputs"].items()}
    strengths = {}
    for rule in system["rules"]:
        strengths[rule[2]] = rule_strength(rule, degrees)
    crisp = centroid(system["output"], strengths, system["samples"])
    return {"output": crisp, "strengths": strengths, "degrees": degrees}


def evaluate(system, values):
    """Crisp inputs -> crisp output. Results are remembered, since the game asks the same questions often."""
    key = tuple(values[name] for name in system["inputs"])
    if key not in system["memory"]:
        system["memory"][key] = infer(system, values)["output"]
    return system["memory"][key]


# --------------------------------------------------------------------------- #
# The game's system: which enemy do I hit?
# --------------------------------------------------------------------------- #

TARGET_RULES = [
    "IF distance is near OR health is low THEN priority is high",
    "IF distance is medium OR health is medium THEN priority is medium",
    "IF distance is far OR health is full THEN priority is low",
]

TARGET = make_system(
    "target",
    inputs={
        # how many tiles away the enemy is
        "distance": {"near": [(0, 1), (2, 0)], "medium": [(0, 0), (2, 1), (4, 0)], "far": [(2, 0), (4, 1)]},
        # how much of its health the enemy has left, in percent
        "health": {"low": [(0, 1), (50, 0)], "medium": [(0, 0), (50, 1), (100, 0)], "full": [(50, 0), (100, 1)]},
    },
    output={"low": [(0, 1), (25, 1), (45, 0)], "medium": [(25, 0), (50, 1), (75, 0)],
            "high": [(55, 0), (75, 1), (100, 1)]},
    rule_lines=TARGET_RULES,
    samples=list(range(5, 100, 10)))


def priority(distance, health_percent):
    """How much a unit wants to hit this enemy, 0 to 100, to one decimal place.

    One decimal place keeps two equally attractive enemies exactly equal, so a
    tie is a real tie and not an accident of arithmetic.
    """
    return round(evaluate(TARGET, {"distance": distance, "health": health_percent}), 1)
