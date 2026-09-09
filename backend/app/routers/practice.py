import uuid

from fastapi import APIRouter, HTTPException

from .. import claude_client
from ..math_engine import MathParseError, check_equivalent, derivative_of
from ..models import PracticeProblem, StartPracticeRequest, StepRequest, StepResponse
from ..session_store import ProblemAttempt, apply_profile_updates, get_session
from ..topics.derivatives import pick_problem

router = APIRouter(prefix="/api/practice", tags=["practice"])

_TOPIC_PICKERS = {"derivatives": pick_problem}


@router.post("/start", response_model=PracticeProblem)
def start_practice(req: StartPracticeRequest):
    session = get_session(req.session_id)
    picker = _TOPIC_PICKERS.get(req.topic)
    if picker is None:
        raise HTTPException(status_code=404, detail=f"Unknown topic '{req.topic}'.")

    problem = picker(session.profile)
    problem_id = str(uuid.uuid4())
    session.active_problems[problem_id] = ProblemAttempt(expression=problem["expr"], skill=problem["skill"])

    return PracticeProblem(
        problem_id=problem_id,
        topic=req.topic,
        skill=problem["skill"],
        prompt=f"Find d/dx of f(x) = {problem['expr']}",
    )


@router.post("/step", response_model=StepResponse)
def submit_step(req: StepRequest):
    session = get_session(req.session_id)
    attempt = session.active_problems.get(req.problem_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Unknown problem_id. Start a practice problem first.")
    if attempt.solved:
        raise HTTPException(status_code=400, detail="This problem is already solved.")
    if not req.student_answer and not req.image_base64:
        raise HTTPException(status_code=400, detail="Provide student_answer text or an image_base64.")

    answer_text = req.student_answer
    if not answer_text and req.image_base64:
        answer_text = claude_client.extract_expression_from_image(req.image_base64)

    attempt.attempts += 1
    correct_expr = derivative_of(attempt.expression)

    try:
        is_correct = bool(answer_text) and check_equivalent(answer_text, correct_expr)
    except MathParseError:
        is_correct = False

    if is_correct:
        attempt.solved = True

    feedback = claude_client.practice_feedback(
        session=session,
        expression=attempt.expression,
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
