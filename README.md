# Football Odds Service

An independent service that will collect publicly accessible football
betting-market information (initially from sources such as Oddschecker),
normalize it into a consistent internal format, and expose it through an
API — for use by a simple monitoring UI, and eventually by other
projects such as Hermes_FPL.

**This repository currently contains only the initial architecture and
development foundation.** No scraping, bookmaker adapters, odds
normalization, or prediction logic has been implemented yet — see
[What is NOT implemented yet](#what-is-not-implemented-yet).

## Current MVP scope

This stage proves out the architecture only:

- A minimal FastAPI backend with a health check and a versioned status
  endpoint.
- A minimal Next.js frontend that displays whether the backend is
  reachable.
- CORS configured so the two can talk to each other locally.
- Basic backend tests (pytest).
- Documentation of the intended future architecture.

## Architecture

```
Browser → Next.js UI → HTTP/JSON → FastAPI backend
```

See [docs/architecture.md](docs/architecture.md) for the full diagram,
the intended future odds pipeline (source adapter → normalization →
validation → canonical model → API), and the database recommendation.

## Directory structure

```
Football_Odds_Service/
├── backend/            FastAPI application (Python)
│   ├── app/
│   │   ├── main.py     App entrypoint, /health, CORS
│   │   ├── api/v1/     Versioned routes (/api/v1/status)
│   │   ├── core/       Configuration (env-based settings)
│   │   └── models/     Pydantic response models
│   ├── tests/          pytest tests
│   ├── pyproject.toml
│   └── .env.example
├── frontend/           Next.js application (TypeScript)
│   ├── app/
│   │   └── page.tsx    Home page: shows backend health status
│   └── .env.example
├── docs/
│   └── architecture.md
├── .gitignore
└── README.md
```

`backend/app/services/` does not exist yet — it will be added once there
is actual business logic (e.g. an Oddschecker adapter) to put in it.

## Backend setup

Requires Python 3.12+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # optional, defaults already work locally
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs
at `http://localhost:8000/docs`.

## Frontend setup

Requires Node.js 20+.

```bash
cd frontend
npm install
cp .env.example .env.local   # optional, defaults already work locally
npm run dev
```

The UI will be available at `http://localhost:3000`.

## How frontend and backend communicate

The frontend calls the backend directly over HTTP/JSON from the browser
(no server-side proxy). The backend URL is configured via the
`NEXT_PUBLIC_API_URL` environment variable (see
`frontend/.env.example`), defaulting to `http://localhost:8000`.

The backend allows cross-origin requests from the URL configured in
`FRONTEND_ORIGIN` (see `backend/.env.example`), defaulting to
`http://localhost:3000`.

The backend is fully usable on its own (e.g. via `/docs` or `curl`)
without the frontend running.

## Testing

Backend:

```bash
cd backend
source .venv/bin/activate
pytest
```

Frontend (lint + build, no test suite yet):

```bash
cd frontend
npm run lint
npm run build
```

## Current limitations

- No real odds data — only health/status endpoints exist.
- No database or persistence of any kind.
- No authentication (nothing sensitive is exposed yet).
- No deployment setup (this scaffold targets local development only).
- No frontend test suite beyond lint/build validation.

## What is NOT implemented yet

- Oddschecker scraping or any other bookmaker/data-source adapter.
- Odds normalization, validation, or a canonical odds data model.
- Any persistence layer (see `docs/architecture.md` for the PostgreSQL
  recommendation for when this becomes necessary).
- Hermes_FPL integration of any kind.
- Prediction or betting-analysis algorithms.
- Authentication/authorization.
- Docker, CI/CD, or any deployment infrastructure.
