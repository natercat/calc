import uuid

from fastapi import APIRouter, HTTPException

from .. import claude_client
from ..math_engine import MathParseError
from ..models import PracticeProblem, StartPracticeRequest, StepRequest, StepResponse
from ..session_store import ProblemAttempt, apply_profile_updates, get_session, session_lock
from ..topics.registry import TOPICS

router = APIRouter(prefix="/api/practice", tags=["practice"])


@router.post("/start", response_model=PracticeProblem)
def start_practice(req: StartPracticeRequest):
    session = get_session(req.session_id)
    module = TOPICS.get(req.topic)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Unknown topic '{req.topic}'.")

    with session_lock(req.session_id):
        problem = module.pick_problem(session.profile)
        problem_id = str(uuid.uuid4())
        session.active_problems[problem_id] = ProblemAttempt(topic=req.topic, problem=problem, skill=problem["skill"])

    return PracticeProblem(
        problem_id=problem_id,
        topic=req.topic,
        skill=problem["skill"],
        prompt=module.build_prompt(problem),
    )


@router.post("/step", response_model=StepResponse)
def submit_step(req: StepRequest):
    session = get_session(req.session_id)

    # The whole handler runs under the lock: two concurrent submissions for
    # the same problem must not both see attempt.solved == False and both
    # get processed as "the" solving attempt, and two concurrent submissions
    # in general must not lose an attempt-count increment to a race.
    with session_lock(req.session_id):
        attempt = session.active_problems.get(req.problem_id)
        if attempt is None:
            raise HTTPException(status_code=404, detail="Unknown problem_id. Start a practice problem first.")
        if attempt.solved:
            raise HTTPException(status_code=400, detail="This problem is already solved.")
        if not req.student_answer and not req.image_base64:
            raise HTTPException(status_code=400, detail="Provide student_answer text or an image_base64.")

        module = TOPICS[attempt.topic]

        answer_text = req.student_answer
        if not answer_text and req.image_base64:
            answer_text = claude_client.extract_expression_from_image(req.image_base64)

        attempt.attempts += 1

        try:
            is_correct = bool(answer_text) and module.check_answer(answer_text, attempt.problem)
        except MathParseError:
            is_correct = False

        if is_correct:
            attempt.solved = True

        feedback = claude_client.practice_feedback(
            session=session,
            problem_prompt=module.build_prompt(attempt.problem),
            skill=attempt.skill,
            student_answer=answer_text or "(could not be read)",
            image_base64=req.image_base64,
            is_correct=is_correct,
            attempt_number=attempt.attempts,
        )
        apply_profile_updates(session, feedback.get("profile_updates", {}))

        return StepResponse(
            correct=is_correct,
            solved=attempt.solved,
            attempt_number=attempt.attempts,
            reply=feedback.get("reply", ""),
            profile=session.profile,
        )
