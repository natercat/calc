import pytest

from app.math_engine import MathParseError, parse_expression
from app.models import SkillLevel
from app.topics.derivatives import LESSON_TEXT, PROBLEM_BANK, SKILLS, pick_problem


def _profile_all(level: SkillLevel) -> dict:
    return {skill: level for skill in SKILLS}


class TestLessonContent:
    def test_lesson_text_nonempty(self):
        assert isinstance(LESSON_TEXT, str)
        assert len(LESSON_TEXT.strip()) > 0


class TestProblemBank:
    def test_every_problem_expression_parses(self):
        for problem in PROBLEM_BANK:
            parse_expression(problem["expr"])  # should not raise

    def test_every_problem_targets_a_known_skill(self):
        for problem in PROBLEM_BANK:
            assert problem["skill"] in SKILLS

    def test_every_problem_has_valid_difficulty(self):
        for problem in PROBLEM_BANK:
            assert problem["difficulty"] in (1, 2, 3)

    def test_problem_ids_are_unique(self):
        ids = [p["id"] for p in PROBLEM_BANK]
        assert len(ids) == len(set(ids))

    def test_every_skill_has_at_least_one_problem(self):
        skills_with_problems = {p["skill"] for p in PROBLEM_BANK}
        assert skills_with_problems == set(SKILLS)


class TestPickProblem:
    def test_all_unknown_picks_first_skill_at_easiest_difficulty(self):
        problem = pick_problem(_profile_all(SkillLevel.UNKNOWN))
        assert problem["skill"] == SKILLS[0]
        assert problem["difficulty"] == 1

    def test_weakest_skill_is_targeted_over_strong_ones(self):
        profile = _profile_all(SkillLevel.STRONG)
        profile["chain_rule"] = SkillLevel.UNKNOWN
        problem = pick_problem(profile)
        assert problem["skill"] == "chain_rule"

    def test_developing_level_picks_medium_difficulty(self):
        profile = _profile_all(SkillLevel.STRONG)
        profile["power_rule"] = SkillLevel.DEVELOPING
        problem = pick_problem(profile)
        assert problem["skill"] == "power_rule"
        assert problem["difficulty"] == 2

    def test_missing_skill_in_profile_treated_as_unknown(self):
        # A profile that doesn't mention a skill at all (e.g. a fresh/partial
        # profile) should be treated the same as "unknown", not KeyError.
        problem = pick_problem({})
        assert problem["skill"] == SKILLS[0]

    def test_accepts_plain_string_levels_not_just_enum(self):
        # profile_updates from Claude arrive as raw strings before
        # apply_profile_updates coerces them to SkillLevel; pick_problem
        # should tolerate either.
        profile = {skill: "strong" for skill in SKILLS}
        profile["quotient_rule"] = "weak"
        problem = pick_problem(profile)
        assert problem["skill"] == "quotient_rule"
        # quotient_rule's bank has no difficulty-1 entry, so "weak" (target
        # difficulty 1) should fall back to the nearest available, which is 2.
        assert problem["difficulty"] == 2

    def test_result_is_a_real_problem_bank_entry(self):
        problem = pick_problem(_profile_all(SkillLevel.UNKNOWN))
        assert problem in PROBLEM_BANK
