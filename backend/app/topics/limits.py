from ..math_engine import check_constant_equal, limit_value
from ._common import pick_by_weakest_skill

SKILLS = [
    "direct_substitution",
    "factoring_limits",
    "limits_at_infinity",
    "trig_limits",
]

LESSON_TEXT = """
## Limits

A limit describes the value a function approaches as x gets arbitrarily close to some
point -- it doesn't require the function to actually be defined there.

Direct substitution: if f is continuous at x = a, lim(x -> a) f(x) = f(a).

Factoring (0/0 indeterminate form): if direct substitution gives 0/0, factor the
numerator and denominator and cancel the common factor before substituting again.

Limits at infinity: for a rational function, compare the degrees of the numerator and
denominator. Same degree -> the limit is the ratio of leading coefficients.

A key trig limit: lim(x -> 0) sin(x)/x = 1.
""".strip()

PROBLEM_BANK = [
    {"id": "l1", "expr": "3*x + 1", "point": "2", "skill": "direct_substitution", "difficulty": 1},
    {"id": "l2", "expr": "x**2 - 4", "point": "3", "skill": "direct_substitution", "difficulty": 1},
    {"id": "l3", "expr": "(x**2 - 4)/(x - 2)", "point": "2", "skill": "factoring_limits", "difficulty": 2},
    {"id": "l4", "expr": "(x**2 - 1)/(x - 1)", "point": "1", "skill": "factoring_limits", "difficulty": 2},
    {"id": "l5", "expr": "(x**2 + 3*x)/(x**2 - 9)", "point": "3", "skill": "factoring_limits", "difficulty": 3},
    {"id": "l6", "expr": "(3*x**2 + 1)/(x**2 - 5)", "point": "oo", "skill": "limits_at_infinity", "difficulty": 2},
    {"id": "l7", "expr": "(2*x + 1)/(5*x - 3)", "point": "oo", "skill": "limits_at_infinity", "difficulty": 2},
    {"id": "l8", "expr": "sin(x)/x", "point": "0", "skill": "trig_limits", "difficulty": 3},
]


def pick_problem(profile: dict) -> dict:
    return pick_by_weakest_skill(SKILLS, PROBLEM_BANK, profile)


def build_prompt(problem: dict) -> str:
    return f"Evaluate lim(x -> {problem['point']}) of {problem['expr']}"


def solve(problem: dict):
    return limit_value(problem["expr"], problem["point"])


def check_answer(student_text: str, problem: dict) -> bool:
    return check_constant_equal(student_text, solve(problem))
