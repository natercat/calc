_LEVEL_RANK = {"unknown": 0, "weak": 1, "developing": 2, "strong": 3}
_LEVEL_TO_DIFFICULTY = {"unknown": 1, "weak": 1, "developing": 2, "strong": 3}


def level_value(level) -> str:
    return level.value if hasattr(level, "value") else str(level)


def pick_by_weakest_skill(skills: list, problem_bank: list, profile: dict) -> dict:
    """Pick a problem targeting the student's weakest skill among `skills`,
    at a difficulty matching their current estimated level for that skill
    (falling back to the nearest available difficulty if there's no exact
    match)."""
    weakest_skill = min(skills, key=lambda s: _LEVEL_RANK.get(level_value(profile.get(s, "unknown")), 0))
    target_difficulty = _LEVEL_TO_DIFFICULTY[level_value(profile.get(weakest_skill, "unknown"))]

    candidates = [p for p in problem_bank if p["skill"] == weakest_skill]
    candidates.sort(key=lambda p: abs(p["difficulty"] - target_difficulty))
    return candidates[0]
