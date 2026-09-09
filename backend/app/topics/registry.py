from . import derivatives, integrals, limits

# Each topic module exports: SKILLS, LESSON_TEXT, PROBLEM_BANK,
# pick_problem(profile), build_prompt(problem), solve(problem), and
# check_answer(student_text, problem) -- see topics/derivatives.py for the
# reference shape.
TOPICS = {
    "derivatives": derivatives,
    "limits": limits,
    "integrals": integrals,
}

ALL_SKILLS = [skill for module in TOPICS.values() for skill in module.SKILLS]
