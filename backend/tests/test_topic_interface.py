"""Generic tests that every topic module must satisfy, run once per topic via
the registry. Topic-specific edge cases (e.g. a particular tricky limit,
+C-invariance for integrals) live in each topic's own test file instead.
"""

import re

import pytest

from app.models import SkillLevel
from app.topics.registry import TOPICS


def _profile_all(skills, level):
    return {skill: level for skill in skills}


@pytest.fixture(params=list(TOPICS.items()), ids=list(TOPICS.keys()))
def topic_module(request):
    _, module = request.param
    return module


class TestTopicInterface:
    def test_lesson_text_nonempty(self, topic_module):
        assert isinstance(topic_module.LESSON_TEXT, str)
        assert len(topic_module.LESSON_TEXT.strip()) > 0

    def test_every_problem_targets_a_known_skill(self, topic_module):
        for problem in topic_module.PROBLEM_BANK:
            assert problem["skill"] in topic_module.SKILLS

    def test_every_problem_has_valid_difficulty(self, topic_module):
        for problem in topic_module.PROBLEM_BANK:
            assert problem["difficulty"] in (1, 2, 3)

    def test_problem_ids_are_unique(self, topic_module):
        ids = [p["id"] for p in topic_module.PROBLEM_BANK]
        assert len(ids) == len(set(ids))

    def test_every_skill_has_at_least_one_problem(self, topic_module):
        skills_with_problems = {p["skill"] for p in topic_module.PROBLEM_BANK}
        assert skills_with_problems == set(topic_module.SKILLS)

    def test_pick_problem_returns_a_real_bank_entry(self, topic_module):
        profile = _profile_all(topic_module.SKILLS, SkillLevel.UNKNOWN)
        problem = topic_module.pick_problem(profile)
        assert problem in topic_module.PROBLEM_BANK

    def test_pick_problem_targets_weakest_skill(self, topic_module):
        profile = _profile_all(topic_module.SKILLS, SkillLevel.STRONG)
        weakest = topic_module.SKILLS[-1]
        profile[weakest] = SkillLevel.UNKNOWN
        problem = topic_module.pick_problem(profile)
        assert problem["skill"] == weakest

    def test_pick_problem_tolerates_missing_skills_in_profile(self, topic_module):
        problem = topic_module.pick_problem({})
        assert problem["skill"] == topic_module.SKILLS[0]

    def test_build_prompt_returns_nonempty_string_for_every_problem(self, topic_module):
        for problem in topic_module.PROBLEM_BANK:
            prompt = topic_module.build_prompt(problem)
            assert isinstance(prompt, str)
            assert prompt.strip()

    def test_build_prompt_never_leaks_raw_python_operator_syntax(self, topic_module):
        # A student should read rendered math ($x^2$), never programming
        # syntax like '**' for exponentiation -- that's precisely what made
        # the original problem prompts and lesson text unreadable to a
        # beginner.
        for problem in topic_module.PROBLEM_BANK:
            prompt = topic_module.build_prompt(problem)
            assert "**" not in prompt

    def test_lesson_text_never_leaks_raw_python_operator_syntax(self, topic_module):
        # LESSON_TEXT legitimately uses "**bold**" markdown, which contains
        # "**" flanked by non-word characters (start-of-line, punctuation) --
        # this specifically catches the exponent pattern (e.g. "x**2"),
        # which is flanked by word characters on both sides.
        assert not re.search(r"\w\*\*\w", topic_module.LESSON_TEXT)

    def test_solve_returns_an_answer_that_checks_out_as_correct(self, topic_module):
        # The engine's own computed answer must always be judged correct by
        # the same topic's check_answer -- the core trust guarantee. solve()
        # returns a sympy object; str() of it is valid input syntax again.
        for problem in topic_module.PROBLEM_BANK:
            correct = topic_module.solve(problem)
            assert topic_module.check_answer(str(correct), problem) is True

    def test_check_answer_rejects_an_unrelated_constant(self, topic_module):
        for problem in topic_module.PROBLEM_BANK:
            assert topic_module.check_answer("123456789", problem) is False
