from fastapi import APIRouter, Query

from .. import claude_client
from ..models import LessonResponse
from ..rate_limiter import claude_call_limiter
from ..session_store import get_session
from ..topics.registry import TOPICS

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.get("/{topic}", response_model=LessonResponse)
def get_lesson(topic: str, session_id: str = Query(...)):
    session = get_session(session_id)
    claude_call_limiter.check(session_id)

    module = TOPICS.get(topic)
    content = module.LESSON_TEXT if module else "This topic isn't available yet."
    intro = claude_client.lesson_intro(session, topic)
    return LessonResponse(topic=topic, content=content, intro=intro, profile=session.profile)
