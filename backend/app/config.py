import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Comma-separated list of origins allowed to call this API, e.g.
# "https://calc-tutor.vercel.app,https://calc-tutor-git-preview.vercel.app"
# -- a list (not just one) because Vercel gives each preview deployment its
# own URL in addition to the production domain.
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
    if origin.strip()
]

# How long a session may sit untouched before it's evicted from memory.
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(2 * 60 * 60)))

# Caps on Claude API usage: how many Claude-calling requests one session may
# make per minute, and how many new sessions one client IP may create per
# minute (closing the obvious bypass of the first limit -- just make a fresh
# session).
CLAUDE_CALLS_PER_MINUTE = int(os.environ.get("CLAUDE_CALLS_PER_MINUTE", "20"))
SESSION_CREATES_PER_MINUTE_PER_IP = int(os.environ.get("SESSION_CREATES_PER_MINUTE_PER_IP", "10"))
