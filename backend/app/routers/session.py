from fastapi import APIRouter, Request

from ..models import SessionResponse
from ..rate_limiter import session_creation_limiter
from ..session_store import create_session, get_session

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("", response_model=SessionResponse)
def new_session(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    session_creation_limiter.check(client_ip)

    session_id = create_session()
    session = get_session(session_id)
    return SessionResponse(session_id=session_id, profile=session.profile)
