from ..math_engine import check_constant_equal, limit_value, point_to_latex, to_latex
from ._common import pick_by_weakest_skill

SKILLS = [
    "direct_substitution",
    "factoring_limits",
    "limits_at_infinity",
    "trig_limits",
]

LESSON_TEXT = r"""
## What is a limit?

A limit answers the question: "as x gets closer and closer to some value,
what value does the function get closer and closer to?" It's about the
trend, not necessarily an exact value at that point -- the function doesn't
even have to be defined there for the limit to exist.

**Example**: as $x$ gets closer to $2$, $3x + 1$ gets closer to $7$. We
write this as $\lim_{x \to 2} (3x+1) = 7$.

## Direct substitution (start here)

For most ordinary functions, you can just plug the value in:
$$\lim_{x \to a} f(x) = f(a) \quad \text{if } f \text{ is continuous at } a$$

## Once you're comfortable: trickier cases

**The 0/0 case (factoring)**: sometimes plugging in gives $\frac{0}{0}$,
which doesn't mean the limit doesn't exist -- it means you need to simplify
first. Factor the numerator and denominator, cancel what's common between
them, then substitute again.

**Limits at infinity**: for a ratio of polynomials as $x \to \infty$,
compare the highest powers on top and bottom. Same highest power -> the
limit is just the ratio of their leading coefficients.

**A limit worth memorizing**: $\lim_{x \to 0} \dfrac{\sin(x)}{x} = 1$.
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
    point_latex = point_to_latex(problem["point"])
    expr_latex = to_latex(problem["expr"])
    return rf"Evaluate the limit: $\lim_{{x \to {point_latex}}} {expr_latex}$"


def solve(problem: dict):
    return limit_value(problem["expr"], problem["point"])


def check_answer(student_text: str, problem: dict) -> bool:
    return check_constant_equal(student_text, solve(problem))
