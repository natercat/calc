from fastapi import APIRouter

from .. import claude_client
from ..models import ChatRequest, ChatResponse
from ..session_store import add_history, apply_profile_updates, get_session

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest):
    session = get_session(req.session_id)
    result = claude_client.chat_reply(session, req.message, req.image_base64)

    add_history(session, "user", req.message)
    add_history(session, "assistant", result.get("reply", ""))
    apply_profile_updates(session, result.get("profile_updates", {}))

    return ChatResponse(reply=result.get("reply", ""), profile=session.profile)
