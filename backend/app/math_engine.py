import sympy
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

X = sympy.symbols("x")

_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# parse_expr ultimately evals the (transformed) input. Passing global_dict=None
# makes sympy build its own namespace via `exec("from sympy import *", d)` --
# but exec() always re-attaches the real `__builtins__` to that dict, so
# `__import__(...)`, `open(...)`, etc. would still resolve and actually run.
# Building that same sympy namespace ourselves and then stripping __builtins__
# keeps Integer/Symbol/etc. available (auto-number and other transformations
# depend on them) while removing arbitrary code execution.
_SYMPY_GLOBALS: dict = {}
exec("from sympy import *", _SYMPY_GLOBALS)  # noqa: S102 -- populates a fixed, then-neutered namespace
_SYMPY_GLOBALS["__builtins__"] = {}

# local_dict pins the bare names we expect; auto_symbol falls back to this for
# any bare NAME token that isn't already in _SYMPY_GLOBALS.
_ALLOWED_NAMES = {
    "x": X,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "exp": sympy.exp,
    "log": sympy.log,
    "ln": sympy.log,
    "sqrt": sympy.sqrt,
    "pi": sympy.pi,
    "E": sympy.E,
}


class MathParseError(ValueError):
    pass


def parse_expression(text: str) -> sympy.Expr:
    if not text or not text.strip():
        raise MathParseError("Empty expression.")
    try:
        expr = parse_expr(
            text.strip(),
            local_dict=_ALLOWED_NAMES,
            global_dict=_SYMPY_GLOBALS,
            transformations=_TRANSFORMATIONS,
            evaluate=True,
        )
    except Exception as exc:
        raise MathParseError(f"Could not parse '{text}' as a math expression.") from exc

    if not isinstance(expr, sympy.Basic):
        # A handful of degenerate inputs (e.g. bare literals/collections) eval
        # to a plain Python object instead of a sympy type.
        raise MathParseError(f"'{text}' is not a valid math expression.")

    extra_symbols = expr.free_symbols - {X}
    if extra_symbols:
        names = ", ".join(str(s) for s in extra_symbols)
        raise MathParseError(f"Expression uses unexpected symbols: {names}. Only 'x' is allowed.")
    return expr


def derivative_of(expr_text: str) -> sympy.Expr:
    expr = parse_expression(expr_text)
    return sympy.simplify(sympy.diff(expr, X))


def check_equivalent(student_text: str, correct_expr: sympy.Expr) -> bool:
    student_expr = parse_expression(student_text)
    diff = sympy.simplify(student_expr - correct_expr)
    if diff == 0:
        return True
    return bool((student_expr - correct_expr).equals(0))


_INFINITY_ALIASES = {
    "oo": sympy.oo,
    "inf": sympy.oo,
    "infinity": sympy.oo,
    "+oo": sympy.oo,
    "+inf": sympy.oo,
    "+infinity": sympy.oo,
    "-oo": -sympy.oo,
    "-inf": -sympy.oo,
    "-infinity": -sympy.oo,
}


def parse_constant(text: str) -> sympy.Expr:
    """Parse a bare number (or +-infinity) with no 'x' allowed -- used for a
    limit's approach point and for a student's answer to a limit problem,
    neither of which may depend on x."""
    if not text or not text.strip():
        raise MathParseError("Empty value.")
    normalized = text.strip().lower()
    if normalized in _INFINITY_ALIASES:
        return _INFINITY_ALIASES[normalized]

    try:
        value = parse_expr(
            text.strip(),
            local_dict=_ALLOWED_NAMES,
            global_dict=_SYMPY_GLOBALS,
            transformations=_TRANSFORMATIONS,
            evaluate=True,
        )
    except Exception as exc:
        raise MathParseError(f"Could not parse '{text}' as a number.") from exc

    if not isinstance(value, sympy.Basic):
        raise MathParseError(f"'{text}' is not a valid number.")
    if value.free_symbols:
        raise MathParseError(f"'{text}' should be a number, not an expression in x.")
    return value


def limit_value(expr_text: str, point_text: str) -> sympy.Expr:
    expr = parse_expression(expr_text)
    point = parse_constant(point_text)
    return sympy.limit(expr, X, point)


def check_constant_equal(student_text: str, correct_value: sympy.Expr) -> bool:
    student_value = parse_constant(student_text)
    if student_value.is_infinite or correct_value.is_infinite:
        # simplify()/.equals() on infinite quantities can produce nan for
        # cases that are trivially unequal (oo vs -oo); direct comparison is
        # both correct and simpler here.
        return student_value == correct_value
    if student_value == correct_value:
        return True
    diff = sympy.simplify(student_value - correct_value)
    if diff == 0:
        return True
    return bool((student_value - correct_value).equals(0))


def to_latex(expr_text: str) -> str:
    """Render a sympy-syntax expression as LaTeX, for display (problem
    prompts, lesson text) -- students should never have to read '**' or
    read raw code syntax as if it were math notation."""
    return sympy.latex(parse_expression(expr_text))


def point_to_latex(point_text: str) -> str:
    return sympy.latex(parse_constant(point_text))


def check_is_antiderivative(student_text: str, integrand: sympy.Expr) -> bool:
    """An indefinite-integral answer is correct iff its derivative equals the
    original integrand. Checking it this way (rather than comparing to one
    canonical antiderivative from sympy.integrate) sidesteps two problems:
    different valid techniques can produce antiderivatives that look nothing
    alike, and it never needs to parse a literal '+ C'."""
    student_expr = parse_expression(student_text)
    student_derivative = sympy.simplify(sympy.diff(student_expr, X))
    diff = sympy.simplify(student_derivative - integrand)
    if diff == 0:
        return True
    return bool((student_derivative - integrand).equals(0))
