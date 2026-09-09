from typing import Optional

from anthropic import Anthropic

from . import config
from .session_store import SessionState

_client: Optional[Anthropic] = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


TUTOR_PERSONA = """
You are a patient, encouraging calculus tutor helping a college student. You adapt your
explanations to the student's demonstrated skill level rather than following a fixed script.

Rules:
- Never do the student's work for them during guided practice. Give hints, ask leading
  questions, and point at the relevant rule -- do not reveal the final answer unless the
  student has made several attempts and is stuck, or explicitly asks for the answer.
- Use the student's current knowledge profile to calibrate depth: for skills marked
  "unknown" or "weak", include more scaffolding and remind them of the relevant rule;
  for skills marked "strong", be more concise and don't over-explain.
- If the student's message reveals a gap in a prerequisite skill, mention it briefly and
  offer to address it, but let the student decide whether to detour.
- Use $...$ for inline math and $$...$$ for display math in your replies so it renders
  correctly on the page.
- Keep replies focused and conversational, not lecture-length.
""".strip()

_RESPOND_TOOL = {
    "name": "respond_to_student",
    "description": "Send a reply to the student and report any updates to their knowledge profile.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string",
                "description": "The natural-language reply to show the student.",
            },
            "profile_updates": {
                "type": "object",
                "description": (
                    "Map of skill name to newly assessed level (unknown, weak, developing, "
                    "strong) for any skill your confidence changed on based on this "
                    "interaction. Omit skills that didn't change."
                ),
                "additionalProperties": {
                    "type": "string",
                    "enum": ["unknown", "weak", "developing", "strong"],
                },
            },
        },
        "required": ["reply"],
    },
}


def _call_tool(system: str, messages: list) -> dict:
    response = _get_client().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system,
        messages=messages,
        tools=[_RESPOND_TOOL],
        tool_choice={"type": "tool", "name": "respond_to_student"},
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    return {"reply": "Sorry, I had trouble putting together a response. Could you try again?"}


def _profile_context(session: SessionState) -> str:
    lines = [f"- {skill}: {level.value}" for skill, level in session.profile.items()]
    return "Student's current knowledge profile:\n" + "\n".join(lines)


def _user_content_blocks(text: str, image_base64: Optional[str]) -> list:
    blocks = []
    if image_base64:
        blocks.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64},
            }
        )
    blocks.append({"type": "text", "text": text})
    return blocks


def chat_reply(session: SessionState, message: str, image_base64: Optional[str]) -> dict:
    system = f"{TUTOR_PERSONA}\n\n{_profile_context(session)}"
    messages = list(session.history) + [
        {"role": "user", "content": _user_content_blocks(message, image_base64)}
    ]
    return _call_tool(system, messages)


def practice_feedback(
    session: SessionState,
    expression: str,
    skill: str,
    student_answer: str,
    image_base64: Optional[str],
    is_correct: bool,
    attempt_number: int,
) -> dict:
    system = f"{TUTOR_PERSONA}\n\n{_profile_context(session)}"
    verdict = "correct" if is_correct else "incorrect"
    prompt = (
        f"The student is finding the derivative of f(x) = {expression} (this problem "
        f"targets the '{skill}' skill). This is attempt #{attempt_number}. Their submitted "
        f"answer has been verified with a symbolic math engine to be {verdict} -- trust "
        "this verdict, it is not your job to re-derive it.\n\n"
        f"Student's submitted answer: {student_answer or '(see attached image)'}\n\n"
        "Respond accordingly: if correct, congratulate them briefly and note what they did "
        "well. If incorrect, do NOT give the final answer -- give a hint appropriate to the "
        f"attempt number (a gentle nudge on attempt 1-2, pointing at the specific rule and "
        "which part of the expression to reapply it to on attempt 3+). Update the profile "
        f"for '{skill}' based on this attempt."
    )
    messages = [{"role": "user", "content": _user_content_blocks(prompt, image_base64)}]
    return _call_tool(system, messages)


def extract_expression_from_image(image_base64: str) -> Optional[str]:
    system = (
        "You read a photo of a student's handwritten calculus work and transcribe the "
        "final mathematical expression they wrote, in plain text using Python/sympy-style "
        "syntax (e.g. 'x**2 + 3*x', 'sin(x)*cos(x)'). Reply with only the transcribed "
        "expression, nothing else."
    )
    response = _get_client().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=200,
        system=system,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64},
                    },
                    {"type": "text", "text": "Transcribe the final expression from this image."},
                ],
            }
        ],
    )
    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    return None


def lesson_intro(session: SessionState, topic: str) -> str:
    prompt = (
        f"Write a short (2-4 sentence) personalized introduction to a lesson on '{topic}' "
        "for this student, based on their knowledge profile below. If they already show "
        "strength in related skills, acknowledge that and set expectations accordingly; if "
        f"skills are unknown/weak, frame it as starting from the fundamentals.\n\n"
        f"{_profile_context(session)}"
    )
    response = _get_client().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=300,
        system=TUTOR_PERSONA,
        messages=[{"role": "user", "content": prompt}],
    )
    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    return ""
