# CalcTutor

An adaptive Calculus tutoring app. This is the MVP slice: **derivatives**, through
all three interaction modes (lesson, guided practice, free chat), with a Claude-powered
tutor and a SymPy-verified answer checker.

## How it works

- **Frontend**: React + Vite. Lets a student read a lesson, work a guided practice
  problem step by step, or chat freely (typed math or a photo of handwork).
- **Backend**: FastAPI + SymPy + the Claude API.
  - SymPy is the source of truth for whether a submitted answer is mathematically
    correct (parses expressions, computes the real derivative, checks equivalence).
  - Claude generates all natural-language content: lesson intros, hints, chat replies.
    It never decides correctness itself — it's given SymPy's verdict and explains it.
  - A lightweight in-memory "knowledge profile" (per session, no accounts) tracks an
    estimated level (unknown / weak / developing / strong) per derivative skill
    (power rule, product rule, quotient rule, chain rule, trig derivatives). Every
    chat message and practice attempt can update it, and it drives which problems get
    picked next and how much scaffolding Claude includes in its explanations.

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

The suite covers `math_engine` (expression parsing, derivative checking,
answer-equivalence, and — importantly — that the parser can't be used to
execute arbitrary code), the derivatives problem bank and its adaptive
`pick_problem` selection, and the in-memory session store. None of it needs
`ANTHROPIC_API_KEY` — the Claude-calling paths (lesson intros, chat, practice
feedback, image transcription) aren't covered here and need manual testing
against a real key.

## What's simplified for the MVP

- **One topic** (derivatives). The lesson content, problem bank, and skill list live
  in `backend/app/topics/derivatives.py` — adding a new topic means adding a sibling
  module with the same shape (skills, lesson text, problem bank, a `pick_problem`
  function) and registering it in the routers.
- **No accounts** — the knowledge profile and practice state live in memory per
  session and are lost on backend restart. Persistent accounts/progress tracking
  is a deliberate later step, not part of this slice.
- **Guided practice checks only the final answer**, not intermediate algebraic
  steps — verifying that an intermediate step correctly applies (say) the product
  rule symbolically is a harder problem than final-answer equivalence, and is a
  reasonable next enhancement once this slice is working end-to-end.
