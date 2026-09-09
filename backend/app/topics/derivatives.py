SKILLS = [
    "power_rule",
    "product_rule",
    "quotient_rule",
    "chain_rule",
    "trig_derivatives",
]

LESSON_TEXT = """
## Derivatives

The derivative of a function measures how fast its output changes as its input changes
-- the slope of the tangent line at a point.

Power rule: d/dx[x^n] = n * x^(n-1)

Product rule: d/dx[f(x)g(x)] = f'(x)g(x) + f(x)g'(x)

Quotient rule: d/dx[f(x)/g(x)] = (f'(x)g(x) - f(x)g'(x)) / g(x)^2

Chain rule: d/dx[f(g(x))] = f'(g(x)) * g'(x)

Trig derivatives: d/dx[sin(x)] = cos(x), d/dx[cos(x)] = -sin(x)
""".strip()

PROBLEM_BANK = [
    {"id": "d1", "expr": "x**2 + 3*x", "skill": "power_rule", "difficulty": 1},
    {"id": "d2", "expr": "4*x**5 - 7*x", "skill": "power_rule", "difficulty": 2},
    {"id": "d3", "expr": "sin(x)", "skill": "trig_derivatives", "difficulty": 1},
    {"id": "d4", "expr": "cos(3*x)", "skill": "trig_derivatives", "difficulty": 2},
    {"id": "d5", "expr": "x**3 * sin(x)", "skill": "product_rule", "difficulty": 2},
    {"id": "d6", "expr": "(x**2 + 1) * cos(x)", "skill": "product_rule", "difficulty": 3},
    {"id": "d7", "expr": "(x**2 + 1) / (x - 1)", "skill": "quotient_rule", "difficulty": 2},
    {"id": "d8", "expr": "sin(x) / x**2", "skill": "quotient_rule", "difficulty": 3},
    {"id": "d9", "expr": "sin(x**2)", "skill": "chain_rule", "difficulty": 2},
    {"id": "d10", "expr": "cos(3*x + 1)**2", "skill": "chain_rule", "difficulty": 3},
]

_LEVEL_TO_DIFFICULTY = {
    "unknown": 1,
    "weak": 1,
    "developing": 2,
    "strong": 3,
}

_LEVEL_RANK = {"unknown": 0, "weak": 1, "developing": 2, "strong": 3}


def _level_value(level) -> str:
    return level.value if hasattr(level, "value") else str(level)


def pick_problem(profile: dict) -> dict:
    """Pick a problem targeting the student's weakest derivative skill, at a
    difficulty matching their current estimated level for that skill."""
    weakest_skill = min(SKILLS, key=lambda s: _LEVEL_RANK.get(_level_value(profile.get(s, "unknown")), 0))
    target_difficulty = _LEVEL_TO_DIFFICULTY[_level_value(profile.get(weakest_skill, "unknown"))]

    candidates = [p for p in PROBLEM_BANK if p["skill"] == weakest_skill]
    candidates.sort(key=lambda p: abs(p["difficulty"] - target_difficulty))
    return candidates[0]
