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
- **No session expiry, rate limiting, or concurrency locking** on the in-memory
  store — fine for single-user local/dev use, worth hardening before any real
  multi-user or public deployment.
