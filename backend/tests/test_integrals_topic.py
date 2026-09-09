from app.topics.integrals import PROBLEM_BANK, build_prompt, check_answer, solve


def _problem(problem_id):
    return next(p for p in PROBLEM_BANK if p["id"] == problem_id)


def test_power_rule_integration():
    problem = _problem("i1")  # x**2 -> x**3/3
    assert check_answer("x**3/3", problem) is True
    assert check_answer("x**3", problem) is False


def test_plus_constant_form_is_still_accepted():
    # Any additive constant is a valid antiderivative -- the app asks
    # students to omit "+ C", but shouldn't penalize including one.
    problem = _problem("i1")
    assert check_answer("x**3/3 + 5", problem) is True
    assert check_answer("x**3/3 - 100", problem) is True


def test_alternate_but_equivalent_trig_form_accepted():
    # integral of 3*sin(x) + cos(x) dx = sin(x) - 3*cos(x) -- written with
    # terms in the opposite order from how a student might first think of it.
    problem = _problem("i8")
    assert check_answer("-3*cos(x) + sin(x)", problem) is True


def test_wrong_sign_on_cosine_antiderivative_rejected():
    problem = _problem("i7")  # sin(x) -> -cos(x), not cos(x)
    assert check_answer("cos(x)", problem) is False


def test_solve_returns_a_real_antiderivative_not_the_integrand():
    problem = _problem("i1")
    assert solve(problem) != problem["expr"]
    assert check_answer(str(solve(problem)), problem) is True


def test_build_prompt_mentions_omitting_the_constant():
    problem = _problem("i1")
    prompt = build_prompt(problem)
    assert "C" in prompt
