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

# local_dict pins the bare names we expect; parse_expr's default global_dict
# (left as None below) is sympy's own safe namespace, not the real builtins,
# so its internal eval can't reach anything outside sympy.
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
            transformations=_TRANSFORMATIONS,
            evaluate=True,
        )
    except Exception as exc:
        raise MathParseError(f"Could not parse '{text}' as a math expression.") from exc

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
