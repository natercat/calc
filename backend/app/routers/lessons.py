from fastapi import APIRouter, Query

from .. import claude_client
from ..models import LessonResponse
from ..session_store import get_session
from ..topics.derivatives import LESSON_TEXT

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

_TOPICS = {"derivatives": LESSON_TEXT}


@router.get("/{topic}", response_model=LessonResponse)
def get_lesson(topic: str, session_id: str = Query(...)):
    session = get_session(session_id)
    content = _TOPICS.get(topic, "This topic isn't available yet.")
    intro = claude_client.lesson_intro(session, topic)
    return LessonResponse(topic=topic, content=content, intro=intro, profile=session.profile)
