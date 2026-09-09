import sympy

from ..math_engine import X, check_is_antiderivative, parse_expression, to_latex
from ._common import pick_by_weakest_skill

SKILLS = [
    "power_rule_integration",
    "constant_multiple",
    "sum_rule_integration",
    "trig_integrals",
]

LESSON_TEXT = r"""
## What is an indefinite integral?

An integral is the reverse of a derivative: given $f(x)$, find a function
$F(x)$ whose derivative *is* $f(x)$. It's sometimes described as "undoing"
the derivative.

Because the derivative of any constant is $0$, if $F(x)$ works then so does
$F(x) + 5$, or $F(x)$ plus any other constant -- that's why a fully general
answer is written $F(x) + C$. For practice here, just give one
antiderivative and leave the "+ C" off.

## The power rule for integration (start here)

$$\int x^n\, dx = \frac{x^{n+1}}{n+1} \quad (n \neq -1)$$

**Example**: the integral of $x^2$ is $\dfrac{x^3}{3}$ -- raise the exponent
by one, then divide by the new exponent. You can check this yourself by
taking the derivative of $\dfrac{x^3}{3}$ and confirming you get back $x^2$.

## Once you're comfortable: combining terms

**Constant multiple** -- a constant factor just comes along for the ride:
$$\int k\,f(x)\, dx = k\int f(x)\, dx$$

**Sum rule** -- integrate term by term, same as with derivatives:
$$\int (f(x) + g(x))\, dx = \int f(x)\, dx + \int g(x)\, dx$$

**Trig integrals**:
$\displaystyle\int \sin(x)\, dx = -\cos(x)$ and
$\displaystyle\int \cos(x)\, dx = \sin(x)$
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
    expr_latex = to_latex(problem["expr"])
    return rf"Find the indefinite integral of $f(x) = {expr_latex}$ (omit the constant of integration, + C)."


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
