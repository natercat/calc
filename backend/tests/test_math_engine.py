import sympy
import pytest

from app.math_engine import MathParseError, check_equivalent, derivative_of, parse_expression


class TestParseExpression:
    def test_basic_polynomial(self):
        expr = parse_expression("x**2 + 3*x")
        assert expr == sympy.sympify("x**2 + 3*x")

    def test_caret_power_notation(self):
        assert parse_expression("x^2") == parse_expression("x**2")

    def test_implicit_multiplication(self):
        assert parse_expression("3x") == parse_expression("3*x")

    def test_allowed_functions(self):
        for name in ["sin", "cos", "tan", "exp", "log", "ln", "sqrt"]:
            parse_expression(f"{name}(x)")  # should not raise

    def test_allowed_constants(self):
        parse_expression("pi*x")
        parse_expression("E*x")

    @pytest.mark.parametrize("text", ["", "   ", None])
    def test_empty_input_rejected(self, text):
        with pytest.raises(MathParseError):
            parse_expression(text)

    @pytest.mark.parametrize(
        "text",
        [
            "x**",
            "sin(x",
            "not a math expr at all!!!",
            "x +* 2",
        ],
    )
    def test_malformed_input_rejected(self, text):
        with pytest.raises(MathParseError):
            parse_expression(text)

    def test_extra_symbol_rejected(self):
        with pytest.raises(MathParseError, match="unexpected symbols"):
            parse_expression("x*y")

    def test_only_x_allowed_as_free_variable(self):
        with pytest.raises(MathParseError):
            parse_expression("y**2")


class TestParseExpressionSecurity:
    """Regression tests: parse_expression must never execute arbitrary code.

    parse_expr evaluates the (transformed) input, and sympy's own default
    global namespace re-attaches real Python builtins via exec(), so a naive
    setup lets `__import__(...)`, `open(...)`, etc. actually run. These cases
    must all be rejected as unparsable, not executed.
    """

    @pytest.mark.parametrize(
        "payload",
        [
            "__import__('os').system('echo pwned')",
            "__import__('os')",
            "open('/etc/passwd').read()",
            "[n for n in ().__class__.__base__.__subclasses__()]",
            "().__class__",
            "exec('1')",
            "eval('1')",
        ],
    )
    def test_code_execution_payloads_are_rejected(self, payload):
        with pytest.raises(MathParseError):
            parse_expression(payload)

    def test_no_filesystem_side_effect(self, tmp_path):
        marker = tmp_path / "pwned"
        payload = f"__import__('os').system('touch {marker}')"
        with pytest.raises(MathParseError):
            parse_expression(payload)
        assert not marker.exists()


class TestDerivativeOf:
    def test_power_rule(self):
        assert derivative_of("x**2 + 3*x") == sympy.sympify("2*x + 3")

    def test_trig(self):
        assert derivative_of("sin(x)") == sympy.cos(sympy.Symbol("x"))

    def test_product_rule(self):
        x = sympy.Symbol("x")
        expected = sympy.simplify(sympy.diff(x**3 * sympy.sin(x), x))
        assert derivative_of("x**3 * sin(x)") == expected

    def test_chain_rule(self):
        x = sympy.Symbol("x")
        expected = sympy.simplify(sympy.diff(sympy.sin(x**2), x))
        assert derivative_of("sin(x**2)") == expected

    def test_quotient_rule(self):
        x = sympy.Symbol("x")
        expected = sympy.simplify(sympy.diff((x**2 + 1) / (x - 1), x))
        assert derivative_of("(x**2 + 1) / (x - 1)") == expected


class TestCheckEquivalent:
    def test_exact_match(self):
        correct = derivative_of("x**2 + 3*x")
        assert check_equivalent("2*x + 3", correct) is True

    def test_differently_formed_but_equivalent(self):
        correct = derivative_of("x**3 * sin(x)")
        # algebraically identical, written in a different order/grouping
        assert check_equivalent("sin(x)*3*x**2 + x**3*cos(x)", correct) is True

    def test_trig_identity_form(self):
        # cos(2x) == cos(x)^2 - sin(x)^2 -- exercises .equals() beyond simplify
        x = sympy.Symbol("x")
        target = sympy.cos(2 * x)
        assert check_equivalent("cos(x)**2 - sin(x)**2", target) is True

    def test_wrong_answer_rejected(self):
        correct = derivative_of("x**3 * sin(x)")
        assert check_equivalent("3*x**2*sin(x)", correct) is False

    def test_off_by_constant_rejected(self):
        correct = derivative_of("x**2")
        assert check_equivalent("2*x + 1", correct) is False

    def test_malformed_student_answer_raises(self):
        correct = derivative_of("x**2")
        with pytest.raises(MathParseError):
            check_equivalent("2*x +", correct)

    def test_student_answer_with_extra_symbol_raises(self):
        correct = derivative_of("x**2")
        with pytest.raises(MathParseError):
            check_equivalent("2*y", correct)
