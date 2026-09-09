from app.topics.limits import PROBLEM_BANK, build_prompt, check_answer


def _problem(problem_id):
    return next(p for p in PROBLEM_BANK if p["id"] == problem_id)


def test_removable_discontinuity_evaluates_correctly():
    # lim(x->2) (x^2-4)/(x-2) -- the classic 0/0 factoring case.
    problem = _problem("l3")
    assert check_answer("4", problem) is True
    assert check_answer("5", problem) is False


def test_limit_at_infinity_same_degree_ratio_of_leading_coefficients():
    problem = _problem("l6")  # (3x^2+1)/(x^2-5) -> 3
    assert check_answer("3", problem) is True


def test_classic_trig_limit_sin_x_over_x():
    problem = _problem("l8")
    assert check_answer("1", problem) is True


def test_check_answer_rejects_infinity_for_a_finite_limit():
    problem = _problem("l1")  # 3x+1 at x=2 -> 7, finite
    assert check_answer("oo", problem) is False


def test_build_prompt_uses_rendered_limit_notation():
    # The prompt should read as real math (LaTeX, for KaTeX to render), not
    # the raw sympy-syntax expression string a student would have to type.
    problem = _problem("l3")
    prompt = build_prompt(problem)
    assert r"\lim" in prompt
    assert "2" in prompt  # the point being approached
    assert problem["expr"] not in prompt
