import json
import os
from datetime import datetime, timedelta
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "data" / "content_log.json"
VIDEOS_DIR = Path(__file__).parent.parent / "data" / "videos"


def load_log():
    with open(LOG_PATH, "r") as f:
        return json.load(f)


def save_log(log):
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def add_entry(persona_id, topic, script, video_path, instagram_post_id, status):
    log = load_log()
    log["entries"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "persona_id": persona_id,
        "topic": topic,
        "script": script,
        "video_path": str(video_path),
        "instagram_post_id": instagram_post_id,
        "status": status,
    })
    save_log(log)


def get_posted_topics(persona_id):
    log = load_log()
    return [
        entry["topic"]
        for entry in log["entries"]
        if entry["persona_id"] == persona_id and entry["status"] == "posted"
    ]


def cleanup_old_videos(days=7):
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    for file in VIDEOS_DIR.iterdir():
        if file.suffix in (".mp4", ".mp3"):
            modified = datetime.fromtimestamp(file.stat().st_mtime)
            if modified < cutoff:
                file.unlink()
                removed += 1
    return removed
