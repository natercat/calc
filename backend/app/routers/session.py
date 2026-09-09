from fastapi import APIRouter

from ..models import SessionResponse
from ..session_store import create_session, get_session

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("", response_model=SessionResponse)
def new_session():
    session_id = create_session()
    session = get_session(session_id)
    return SessionResponse(session_id=session_id, profile=session.profile)
