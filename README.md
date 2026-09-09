# CalcTutor

An adaptive Calculus tutoring app covering the core of Calc 1 -- **derivatives,
limits, and indefinite integrals** -- through three interaction modes (lesson,
guided practice, free chat), with a Claude-powered tutor and a SymPy-verified
answer checker.

## How it works

- **Frontend**: React + Vite. Lets a student read a lesson, work a guided practice
  problem step by step, or chat freely (typed math or a photo of handwork), for
  whichever topic is selected.
- **Backend**: FastAPI + SymPy + the Claude API.
  - SymPy is the source of truth for whether a submitted answer is mathematically
    correct. Each topic checks correctness differently -- derivatives compare the
    student's answer to the true derivative; limits compare to the true limit
    value (`sympy.limit`); integrals differentiate the student's answer back and
    compare it to the original integrand, which validates any equivalent
    antiderivative without needing to parse a literal "+ C". Claude never decides
    correctness itself -- it's given SymPy's verdict and explains it.
  - A lightweight in-memory "knowledge profile" (per session, no accounts) tracks
    an estimated level (unknown / weak / developing / strong) per skill, across
    all three topics at once (e.g. product rule, factoring limits, trig
    integrals). Every chat message and practice attempt can update it, and it
    drives which problems get picked next and how much scaffolding Claude
    includes in its explanations.
- **Topic modules** (`backend/app/topics/`): each topic (`derivatives.py`,
  `limits.py`, `integrals.py`) exports the same interface -- `SKILLS`,
  `LESSON_TEXT`, `PROBLEM_BANK`, `pick_problem(profile)`, `build_prompt(problem)`,
  `solve(problem)`, `check_answer(student_text, problem)` -- and is registered in
  `topics/registry.py`. The lesson/practice routers and the session store are
  written against this interface generically, so adding a fourth topic (e.g.
  Calc 2's sequences and series) means writing one new module with that shape,
  not touching the routers.

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open the printed local URL (default `http://localhost:5173`). The frontend
expects the backend at `http://localhost:8000` by default; override with a
`VITE_API_BASE` env var if needed.

## Testing

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

The suite (100+ tests) covers `math_engine` (expression parsing, derivative/
limit/antiderivative checking, and — importantly — that the parser can't be
used to execute arbitrary code), each topic's problem bank and adaptive
`pick_problem` selection (both generically via `test_topic_interface.py` and
with topic-specific edge cases), the skill registry, and the in-memory session
store. None of it needs `ANTHROPIC_API_KEY` — the Claude-calling paths (lesson
intros, chat, practice feedback, image transcription) aren't covered here and
need manual testing against a real key. All three topics and the image-upload
path (typed math and photos, both chat and practice) have been manually
verified against a live key.

## Deploying to production

The backend keeps sessions, per-session locks, and rate-limit counters in
process memory (see "In-memory only, single process" below), so it **must**
run as a single persistent process -- a serverless/edge platform would
silently break it, since each request could hit a different cold instance
and lose all session state. **Railway** (backend) + **Vercel** (frontend) is
the combination this repo is set up for; the config files below are already
in place, but connecting your own accounts and setting environment variables
has to happen in each platform's dashboard.

### 1. Backend on Railway

1. Sign up at [railway.app](https://railway.app) (GitHub login is simplest --
   it also handles repo access).
2. **New Project → Deploy from GitHub repo** → select this repo → authorize
   Railway's GitHub App if prompted.
3. This is a monorepo, so open the new service's **Settings** and set
   **Root Directory** to `backend`.
4. Railway auto-detects Python via `requirements.txt` (Nixpacks builder) and
   uses `backend/Procfile` for the start command
   (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`) -- no build command
   to configure.
5. Under **Variables**, add:
   - `ANTHROPIC_API_KEY` -- your real key
   - `FRONTEND_ORIGIN` -- set to `http://localhost:5173` for now; you'll
     update this in step 3 once the frontend has a real URL
   - (optional) `ANTHROPIC_MODEL`, `SESSION_TTL_SECONDS`,
     `CLAUDE_CALLS_PER_MINUTE`, `SESSION_CREATES_PER_MINUTE_PER_IP` --
     defaults are reasonable, only set these if you want different values
6. Deploy. Under **Settings → Networking**, click **Generate Domain** to get
   a public HTTPS URL (Railway doesn't expose one automatically).
7. Verify: `curl https://<your-service>.up.railway.app/api/health` should
   return `{"status":"ok"}`.

### 2. Frontend on Vercel

1. Sign up at [vercel.com](https://vercel.com) (GitHub login again simplest).
2. **Add New → Project** → import this same repo → authorize Vercel's
   GitHub App if prompted.
3. In the import screen, set **Root Directory** to `frontend`. Vercel
   auto-detects the Vite framework preset -- no build command changes needed.
4. Add an environment variable: `VITE_API_BASE` = the Railway URL from step
   1 (no trailing slash), e.g. `https://your-service.up.railway.app`.
5. Deploy. Vercel gives you a production URL (e.g.
   `https://calc-tutor.vercel.app`).

### 3. Point the backend back at the frontend

1. Back in Railway, update `FRONTEND_ORIGIN` to your real Vercel URL from
   step 2. If you also want Vercel *preview* deployments (unique URLs per
   branch/PR) to work, add them comma-separated -- `FRONTEND_ORIGIN` accepts
   a comma-separated list.
2. Redeploy the backend (Railway usually redeploys automatically on a
   variable change; trigger one manually if not).

### 4. Verify end to end

Open the Vercel URL in a browser and try all three modes. If the browser
console shows a CORS error, it almost always means `FRONTEND_ORIGIN` on
Railway doesn't exactly match the Vercel URL (scheme, no trailing slash) or
the backend hasn't redeployed since you changed it.

**Before you share the URL**: it's now a public page that calls a paid
Claude API on your key. The rate limits from `CLAUDE_CALLS_PER_MINUTE` /
`SESSION_CREATES_PER_MINUTE_PER_IP` cap abuse but don't eliminate cost --
keep the URL private until you're ready for that, and keep an eye on your
Anthropic Console usage.

## What's simplified for the MVP

- **No accounts** — the knowledge profile and practice state live in memory per
  session and are lost on backend restart. Persistent accounts/progress tracking
  is a deliberate later step, not part of this slice.
- **Guided practice checks only the final answer**, not intermediate algebraic
  steps — verifying that an intermediate step correctly applies (say) the product
  rule symbolically is a harder problem than final-answer equivalence, and is a
  reasonable next enhancement.
- **Limits are curated to have a clean answer** — the problem bank avoids
  two-sided limits that don't exist (e.g. `1/x` at `x=0`), which the current
  answer checker doesn't have a way to express.
- **In-memory only, single process** — the session store, locks, and rate
  limiters all live in this process's memory, so nothing survives a restart
  and nothing coordinates across multiple worker processes. Fine for the
  current single-instance deployment; a scaled-out deployment would need a
  shared store (e.g. Redis) behind all of it. Within that constraint, the
  operational concerns are handled:
  - **Concurrency**: a per-session lock (`session_store.session_lock`) wraps
    every chat/practice route, so concurrent requests against the *same*
    session can't race (see `tests/test_practice_concurrency.py` for the
    exact scenario this closes); different sessions still run fully in
    parallel.
  - **Session expiry**: a session inactive for longer than
    `SESSION_TTL_SECONDS` (default 2 hours) is evicted, along with its lock,
    the next time any request triggers a sweep (throttled to at most once
    per 5 minutes of wall-clock time, piggybacked on ordinary traffic rather
    than a background thread). A session mid-request is never evicted out
    from under it.
  - **Rate limiting**: `CLAUDE_CALLS_PER_MINUTE` caps how often one session
    can trigger a Claude API call, and `SESSION_CREATES_PER_MINUTE_PER_IP`
    caps new-session creation per client IP (closing the obvious bypass of
    the first limit — just make a new session). Both return 429 with a
    `Retry-After` header; the frontend surfaces the message as an inline
    error rather than failing silently.
