from fastapi import APIRouter

from .. import claude_client
from ..models import ChatRequest, ChatResponse
from ..session_store import add_history, apply_profile_updates, get_session, session_lock

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest):
    session = get_session(req.session_id)

    # Locked for the same reason as practice/step: chat_reply reads
    # session.history to build the message list, and a concurrent request
    # appending to that history mid-read would corrupt conversation order.
    with session_lock(req.session_id):
        result = claude_client.chat_reply(session, req.message, req.image_base64)

        add_history(session, "user", req.message)
        add_history(session, "assistant", result.get("reply", ""))
        apply_profile_updates(session, result.get("profile_updates", {}))

        return ChatResponse(reply=result.get("reply", ""), profile=session.profile)
