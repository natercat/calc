import sympy

from ..math_engine import X, check_is_antiderivative, parse_expression
from ._common import pick_by_weakest_skill

SKILLS = [
    "power_rule_integration",
    "constant_multiple",
    "sum_rule_integration",
    "trig_integrals",
]

LESSON_TEXT = """
## Indefinite Integrals

An indefinite integral (antiderivative) of f(x) is any function F(x) whose derivative is
f(x). Since the derivative of a constant is 0, F(x) + C is also an antiderivative for any
constant C -- but for practice here, give just one antiderivative and omit the "+ C".

Power rule for integration: integral of x^n dx = x^(n+1)/(n+1) + C  (for n != -1)

Constant multiple: integral of k*f(x) dx = k * integral of f(x) dx

Sum rule: integral of (f(x) + g(x)) dx = integral of f(x) dx + integral of g(x) dx

Trig integrals: integral of sin(x) dx = -cos(x) + C, integral of cos(x) dx = sin(x) + C
""".strip()

PROBLEM_BANK = [
    {"id": "i1", "expr": "x**2", "skill": "power_rule_integration", "difficulty": 1},
    {"id": "i2", "expr": "x**4", "skill": "power_rule_integration", "difficulty": 1},
    {"id": "i3", "expr": "5*x**3", "skill": "constant_multiple", "difficulty": 2},
    {"id": "i4", "expr": "7*x**6", "skill": "constant_multiple", "difficulty": 2},
    {"id": "i5", "expr": "x**2 + 3*x", "skill": "sum_rule_integration", "difficulty": 2},
    {"id": "i6", "expr": "4*x**3 - 2*x + 1", "skill": "sum_rule_integration", "difficulty": 3},
    {"id": "i7", "expr": "sin(x)", "skill": "trig_integrals", "difficulty": 1},
    {"id": "i8", "expr": "3*sin(x) + cos(x)", "skill": "trig_integrals", "difficulty": 2},
]


def pick_problem(profile: dict) -> dict:
    return pick_by_weakest_skill(SKILLS, PROBLEM_BANK, profile)


def build_prompt(problem: dict) -> str:
    return f"Find the indefinite integral of f(x) = {problem['expr']} (omit the constant of integration, + C)"


def solve(problem: dict):
    """One valid antiderivative (up to a constant). check_answer doesn't
    compare against this directly -- it verifies correctness by
    differentiating the student's answer back to the integrand instead,
    which accepts any equally valid antiderivative, not just this one."""
    integrand = parse_expression(problem["expr"])
    return sympy.integrate(integrand, X)


def check_answer(student_text: str, problem: dict) -> bool:
    integrand = parse_expression(problem["expr"])
    return check_is_antiderivative(student_text, integrand)
