import logging
import os
import threading
import hmac
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request, send_from_directory

from agent import run_main_agent
from post_store import get_posts, get_topics

app = Flask(__name__, static_folder="web", static_url_path="/static")
agent_lock = threading.Lock()
agent_state = {
    "status": "idle",
    "started_at": None,
    "completed_at": None,
    "message": None,
}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/posts")
def posts_route():
    return jsonify(get_posts())


@app.get("/api/topics")
def topics_route():
    topics = get_topics()
    return jsonify({"topics": topics, "total": len(topics)})


def _run_agent() -> None:
    try:
        logging.info("Starting main agent run")
        result = run_main_agent()
        logging.info("Main agent run completed: %s", result)
        with agent_lock:
            agent_state.update(
                status="succeeded",
                completed_at=datetime.now().astimezone().isoformat(),
                message="A new post has been published.",
            )
    except Exception:
        logging.exception("Main agent run failed")
        with agent_lock:
            agent_state.update(
                status="failed",
                completed_at=datetime.now().astimezone().isoformat(),
                message="Generation failed. Check the server logs for details.",
            )


@app.post("/api/run")
def start_agent_route():
    expected_token = os.environ.get("AGENT_RUN_TOKEN")
    authorization = request.headers.get("Authorization", "")
    if not expected_token:
        return jsonify({"error": "Manual generation is not configured."}), 503
    if not hmac.compare_digest(authorization, f"Bearer {expected_token}"):
        return jsonify({"error": "A valid generation key is required."}), 401

    with agent_lock:
        if agent_state["status"] == "running":
            return jsonify({"error": "A generation is already in progress."}), 409
        agent_state.update(
            status="running",
            started_at=datetime.now().astimezone().isoformat(),
            message="Researching and drafting a new post.",
        )
        message = agent_state["message"]
    threading.Thread(target=_run_agent, daemon=True).start()
    return jsonify({"status": "running", "message": message}), 202


@app.get("/api/status")
def agent_status_route():
    with agent_lock:
        return jsonify(dict(agent_state))


scheduler = BackgroundScheduler()


def run_scheduled_agent() -> None:
    with agent_lock:
        if agent_state["status"] == "running":
            logging.info("Skipping scheduled run because a generation is already active")
            return
        agent_state.update(
            status="running",
            started_at=datetime.now().astimezone().isoformat(),
            message="Researching and drafting a new post.",
        )
    _run_agent()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        run_scheduled_agent,
        "interval",
        hours=int(os.environ.get("AGENT_INTERVAL_HOURS", "2")),
        next_run_time=datetime.now(),
        id="main-agent-post-job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logging.info("APScheduler started; main agent will run every 2 hours")


if os.environ.get("RUN_SCHEDULER", "false").lower() == "true":
    start_scheduler()


if __name__ == "__main__":
    start_scheduler()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))