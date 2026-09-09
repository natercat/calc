from ..math_engine import check_equivalent, derivative_of, to_latex
from ._common import pick_by_weakest_skill

SKILLS = [
    "power_rule",
    "product_rule",
    "quotient_rule",
    "chain_rule",
    "trig_derivatives",
]

LESSON_TEXT = r"""
## What is a derivative?

Imagine watching a car's speedometer while its position keeps changing. The
speedometer tells you exactly how fast the position is changing *right now*.
A derivative does the same thing for any function: it tells you how fast the
function's output is changing at a given input.

Graphically, the derivative at a point is the slope of the tangent line
there -- the line that just grazes the curve at that one point. A steep
tangent means the function is changing quickly; a flat one means it's barely
changing at all.

## The power rule (start here)

The rule you'll use most: for a term $x^n$, its derivative is $nx^{n-1}$ --
bring the exponent down as a multiplier, then reduce the exponent by one.

**Example**: the derivative of $x^2$ is $2x$. So at $x = 3$, the slope of
$f(x) = x^2$ is $2(3) = 6$.

This applies term by term. For $f(x) = x^2 + 3x$: the derivative of $x^2$ is
$2x$, and the derivative of $3x$ (think of it as $3x^1$) is $3$. So
$f'(x) = 2x + 3$.

## Once you're comfortable: rules for combined functions

**Product rule** -- for two functions multiplied together, like $x^3\sin(x)$:
$$\frac{d}{dx}[f(x)g(x)] = f'(x)g(x) + f(x)g'(x)$$

**Quotient rule** -- for one function divided by another:
$$\frac{d}{dx}\left[\frac{f(x)}{g(x)}\right] = \frac{f'(x)g(x) - f(x)g'(x)}{g(x)^2}$$

**Chain rule** -- for a function nested inside another, like $\sin(x^2)$:
$$\frac{d}{dx}[f(g(x))] = f'(g(x)) \cdot g'(x)$$

**Trig derivatives** -- worth memorizing:
$\dfrac{d}{dx}[\sin(x)] = \cos(x)$ and $\dfrac{d}{dx}[\cos(x)] = -\sin(x)$
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
    return rf"Find the derivative of $f(x) = {to_latex(problem['expr'])}$."


def solve(problem: dict):
    return derivative_of(problem["expr"])


def check_answer(student_text: str, problem: dict) -> bool:
    return check_equivalent(student_text, solve(problem))
