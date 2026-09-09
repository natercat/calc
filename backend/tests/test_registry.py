from app.topics.registry import ALL_SKILLS, TOPICS


def test_expected_topics_registered():
    assert set(TOPICS.keys()) == {"derivatives", "limits", "integrals"}


def test_all_skills_aggregates_every_topic():
    expected = [skill for module in TOPICS.values() for skill in module.SKILLS]
    assert ALL_SKILLS == expected


def test_no_duplicate_skill_names_across_topics():
    # Skill names double as profile keys shared across the whole session, so
    # two topics silently sharing a name would corrupt each other's tracking.
    assert len(ALL_SKILLS) == len(set(ALL_SKILLS))


def test_every_topic_module_has_the_required_interface():
    required = {"SKILLS", "LESSON_TEXT", "PROBLEM_BANK", "pick_problem", "build_prompt", "solve", "check_answer"}
    for topic_id, module in TOPICS.items():
        missing = required - set(dir(module))
        assert not missing, f"topic '{topic_id}' is missing: {missing}"
