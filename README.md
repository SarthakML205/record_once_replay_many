# record_once_replay_many

Deterministic **Discover Once, Replay Many** computer-use layer for API-less back-office UIs.

## Stack

- **Python** — discovery agent, replay engine, HITL, guardrails, schemas
- **React (Vite)** — mock credit-union portal (`target-app/`)
- **Computer-use** — Playwright observe/act plus an LLM decision loop in discovery; replay is zero-LLM (next)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

copy .env.example .env
# set ANTHROPIC_API_KEY in .env — never commit .env

cd target-app
npm install
npm run dev
```

`.env` holds API keys (`ANTHROPIC_API_KEY`, optional `ANTHROPIC_MODEL`, `TARGET_APP_URL`). It is gitignored.

## Discovery (computer use)

With the mock portal running at `http://localhost:5173`:

```bash
python -m src discover --goal "Look up member M10005, open a high-yield savings sub-account named Ops Reserve with initial deposit 40, confirm, and read the confirmation ID"
```

That run writes:

- `evidence/capability_artifact.json` — parameterized, replay-ready capability (no LLM transcript, no literal member values)
- `evidence/discovery_run.log` — redacted JSONL of actions taken (not chain-of-thought)
