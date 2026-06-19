# Ask AI Agent - Property Management Assistant

A conversational AI backend (with React frontend) for property management. A property manager chats with the assistant, which answers questions by querying the database and can take actions (send messages, apply credits) -- but only with explicit human approval.

Built with **Strands Agents SDK**, **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Anthropic Claude**.

## Features

- **Streaming Chat**: SSE-streamed responses via FastAPI, with session continuity
- **Analytics Skill**: Text-to-SQL over property/tenant/lease/charge data -- validated, read-only
- **Approval-Gated Actions**: Send message, schedule message, apply credit -- interrupt-based approval flow
- **Clean REST API**: Properties, tenants, sessions, messages -- layered architecture
- **React Frontend**: Chat UI with streaming text, approval cards, session sidebar, domain pages

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for PostgreSQL)
- Node.js 18+ (for frontend)
- Anthropic API key

### 1. Clone and setup

```bash
git clone https://github.com/shamal-durbule/Ask-AI-Agent.git
cd Ask-AI-Agent

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

### 2. Environment variables

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

**Port conflicts?** All ports are configurable via `.env`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DB_PORT` | `5432` | Host port for PostgreSQL container |
| `API_PORT` | `8000` | Uvicorn API server port |
| `VITE_API_PORT` | `8000` | Frontend proxy target (must match `API_PORT`) |
| `DATABASE_URL` | `...localhost:5432/...` | Full database connection string (update port to match `DB_PORT`) |

### 3. Start PostgreSQL

```bash
docker compose up -d
```

### 4. Run migrations and seed data

```bash
alembic upgrade head
python -m scripts.seed_data
```

### 5. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port ${API_PORT:-8000}
```

Or simply: `uvicorn app.main:app --reload --port 8000`

### 6. Start the frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to use the chat UI. The frontend proxies `/api` requests to the backend using `VITE_API_PORT`.

### 7. Try it with curl

```bash
# Health check
curl http://localhost:8000/health

# List properties
curl http://localhost:8000/api/properties | python -m json.tool

# List tenants
curl http://localhost:8000/api/tenants | python -m json.tool

# Chat (SSE stream)
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How much rent is outstanding this month?"}'

# Chat with session continuity
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Which tenants are overdue?", "session_id": "my-session"}'

# List sessions
curl http://localhost:8000/api/chat/sessions | python -m json.tool
```

## Code Quality

```bash
# Lint and format
ruff check .
ruff format .

# Type check
mypy app/

# Run tests
pytest -v
```

## Project Structure

```
ask-ai-agent/
  app/
    main.py              # FastAPI application
    config.py            # Environment configuration
    database.py          # Async SQLAlchemy setup
    models/              # SQLAlchemy ORM models
    schemas/             # Pydantic request/response DTOs
    repositories/        # Data access layer
    services/            # Business logic layer
    api/                 # Thin route handlers
    agent/               # Strands agent setup
      factory.py         # Agent creation
      system_prompt.py   # System prompt
      tools/             # Read, write, and analytics tools
      skills/            # SKILL.md files
      hooks/             # ApprovalHook
    middleware/           # Auth stub
  alembic/               # Database migrations
  scripts/               # Seed data
  tests/                 # Test suite
  docs/                  # Architecture docs
  frontend/              # React + TypeScript UI
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design.

## Key Design Points

- **Single workspace**: All data belongs to one property management company
- **SQL safety**: Generated SQL is parsed with sqlglot (SELECT-only), executed in READ ONLY transactions with timeouts
- **Exactly-once execution**: Write actions use an `action_log` table with CAS status transitions
- **Session continuity**: Strands FileSessionManager persists conversation state
- **Clean layering**: Routes -> Services -> Repositories -> Database (no layer skipping)

See [docs/decisions.md](docs/decisions.md) for detailed tradeoffs.

## Streaming Protocol

The chat uses SSE with typed events: `text`, `tool_start`, `tool_end`, `approval_required`, `done`, `error`.

See [docs/streaming_protocol.md](docs/streaming_protocol.md) for the full protocol spec.
