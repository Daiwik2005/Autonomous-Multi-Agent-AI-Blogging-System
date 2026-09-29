# Tweety Journal

An AI-generated editorial journal. Flask serves the responsive web app and JSON API; SQLite stores every published post and its topic history. Before choosing a story, the agent reads that history and avoids topics already used.

## Run locally

Python 3.13 or newer is required. Create a `.env` file with the credentials below, install the project dependencies, and start the app:

```text
GOOGLE_API_KEY=your_google_ai_studio_key
TAVILY_API_KEY=your_tavily_key
```

```powershell
python -m pip install -e .
python back.py
```

Open `http://localhost:5000`. The local database is `tweety.sqlite3` in the project directory by default. Set `TWEETY_DB_PATH` to use a different location.

## Deploy on Render

1. Push this repository to a Git provider connected to Render.
2. In Render, create a Blueprint instance from the repository and apply `render.yaml`.
3. Set the secret values for `GOOGLE_API_KEY`, `TAVILY_API_KEY`, and `AGENT_RUN_TOKEN` in the service environment. Use a long, randomly generated value for `AGENT_RUN_TOKEN`; the manual generate button prompts for it and keeps it only for the current browser tab.
4. Deploy and open the generated service URL. Render checks `/api/health` after deployment.

The Blueprint uses Render's Starter web-service plan because persistent disks are not available on free web services. It runs Flask with Gunicorn and mounts a persistent disk at `/var/data`, where SQLite keeps posts and topics across deploys and restarts. The scheduled agent starts immediately and repeats every two hours. Change `AGENT_INTERVAL_HOURS` or set `RUN_SCHEDULER` to `false` in Render to adjust or disable scheduled publishing. Keep a single web-service instance when using this SQLite disk; SQLite files on a Render disk are not shared between multiple instances.

## API

- `GET /api/health`: deployment health check.
- `GET /api/posts`: published posts, newest first.
- `GET /api/topics`: topic history, newest first.
- `GET /api/status`: current or last agent run status.
- `POST /api/run`: start a manual agent run; returns `202` while it works.
