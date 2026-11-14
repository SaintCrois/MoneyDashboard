# WhyMove web app

React + TypeScript on Vite. Reads from the FastAPI backend through `/api`.

```
# 1. backend (from the repo root)
uvicorn app.main:app --app-dir server --port 8000

# 2. web app
cd web
npm install
npm run dev        # http://localhost:5173
```

Screens: holdings (`#/`), one stock (`#/stock/PTT`), news feed (`#/news`), alerts (`#/alerts`).
The sidebar switches match strictness (strict / medium / loose) and previews the phone layout on a desktop screen.

Data comes from `/api/insights/*` (see `server/app/api/insights.py`). Matching is keyword-level; no AI is used.
