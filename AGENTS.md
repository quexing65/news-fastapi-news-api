# AGENTS.md — Project Rules

## Overview

News platform (新闻资讯平台): full-stack, front-end/back-end separated. Backend is **FastAPI + SQLAlchemy async + MySQL + Redis**; frontend is **Vue 3 + Vant 4** (mobile). Features: news categories/browsing, article details with view counts, user auth (JWT), favorites, browsing history, AI Q&A chat.

## Architecture

```
Vue 3 frontend  ──axios(/api/*)──▶  FastAPI backend
                                      │
                            ┌─────────┴─────────┐
                            ▼                   ▼
                        MySQL(业务数据)      Redis(缓存层)
```

- **5-layer backend**: routers → crud → cache → models → schemas
- **Unified response**: all endpoints return `{code, message, data}`
- **Auth**: JWT via `get_current_user` FastAPI dependency injection
- **Redis read-through/write-through**: hot data cached; cache invalidated on writes

## Backend (`toutiao_backend/`)

- **Python 3.13+**, deps managed by **uv** (`pyproject.toml` + `uv.lock`)
- Run: `uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000`
- Swagger docs at `http://127.0.0.1:8000/docs`
- Config via `.env` (see `.env.example`); key var: `ASYNC_DATABASE_URL`
- ORM models in `models/`, Pydantic schemas in `schemas/`, data ops in `crud/`, cache layer in `cache/`, routes in `routers/`, utilities in `utils/`
- No linting or formatting config exists — match existing code style

## Frontend (`xwzx-news/`)

- **Vue 3 + Vite 7 + Vant 4** (mobile UI library)
- State: **Pinia 3** with persistence plugin; routing: **vue-router 4**
- i18n: **vue-i18n 9** (Chinese + English)
- HTTP: **axios**; Markdown: **marked + DOMPurify**
- Run: `npm install && npm run dev` (default port 5173)
- AI chat at `/aichat` route — calls Alibaba DashScope API directly from frontend (no backend proxy), uses `VITE_AI_API_KEY` from `.env.local`

## Conventions

- Backend API prefix: `/api/`
- Protected endpoints require `Authorization: Bearer <token>` header
- No `.editorconfig`, `.prettierrc`, `.eslintrc`, or `Dockerfile` exists
- No automated tests (only `test_main.http` for manual HTTP testing)
- License: learning/personal use only
