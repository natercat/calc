from ..math_engine import check_equivalent, derivative_of
from ._common import pick_by_weakest_skill

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


def pick_problem(profile: dict) -> dict:
    return pick_by_weakest_skill(SKILLS, PROBLEM_BANK, profile)


def build_prompt(problem: dict) -> str:
    return f"Find d/dx of f(x) = {problem['expr']}"


def solve(problem: dict):
    return derivative_of(problem["expr"])


def check_answer(student_text: str, problem: dict) -> bool:
    return check_equivalent(student_text, solve(problem))
