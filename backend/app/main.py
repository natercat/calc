import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from . import config
from .routers import chat, lessons, practice, session

logger = logging.getLogger(__name__)

app = FastAPI(title="CalcTutor API")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            # Starlette's ServerErrorMiddleware (which handles exceptions
            # that escape the app entirely) sits OUTSIDE user middleware,
            # including CORSMiddleware -- so an unhandled exception would
            # otherwise reach the browser with no CORS headers at all and
            # show up as a misleading "blocked by CORS policy" error rather
            # than the real failure. Catching it here, inside CORSMiddleware,
            # means CORS still sees a normal response to attach headers to.
            logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"detail": "Something went wrong on the server. Please try again."},
            )


# Order matters: middleware added later wraps middleware added earlier, so
# ErrorHandlingMiddleware (added first) must run inside CORSMiddleware.
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(lessons.router)
app.include_router(practice.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
