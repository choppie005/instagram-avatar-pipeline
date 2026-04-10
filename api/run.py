"""Vercel Serverless Function — triggers the pipeline.

Called via Vercel Cron or manually via GET /api/run.
"""

import json
import logging
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.content_log import add_entry, get_posted_topics
from src.persona_selector import get_next_topic, get_todays_personas
from src.script_generator import generate_script
from src.video_generator import generate_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def notify_failure(persona_id, topic, error):
    import requests
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, json={
            "content": f"**Pipeline failed** for `{persona_id}` on topic '{topic}':\n```{error}```"
        })
    except Exception:
        log.warning("Failed to send Discord notification")


def run_for_persona(persona):
    persona_id = persona["id"]
    posted_topics = get_posted_topics(persona_id)
    topic = get_next_topic(persona, posted_topics)

    log.info(f"Processing: {persona_id} | Topic: {topic}")

    try:
        result = generate_script(persona, topic)
        script_text = result["script"]
        caption = result["caption"]
        hashtags = " ".join(result["hashtags"])
        full_caption = f"{caption}\n\n{hashtags}"
        log.info(f"  Script generated ({len(script_text.split())} words)")

        video_path = f"/tmp/{datetime.now().strftime('%Y-%m-%d')}_{persona_id}.mp4"
        video_url = generate_video(
            persona["heygen_avatar_id"],
            script_text,
            persona["heygen_voice_id"],
            video_path,
        )
        log.info(f"  Video generated")

        from src.instagram_poster import post_reel
        post_id = post_reel(video_url, full_caption)
        log.info(f"  Posted! Instagram ID: {post_id}")

        add_entry(persona_id, topic, script_text, video_path, post_id, "posted")
        return {"persona": persona_id, "topic": topic, "status": "posted", "post_id": post_id}

    except Exception as e:
        log.error(f"  FAILED for {persona_id}: {e}")
        add_entry(persona_id, topic, "", "", "", "failed")
        notify_failure(persona_id, topic, str(e))
        return {"persona": persona_id, "topic": topic, "status": "failed", "error": str(e)}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        cron_secret = os.getenv("CRON_SECRET")
        auth_header = self.headers.get("Authorization", "")
        if cron_secret and auth_header != f"Bearer {cron_secret}":
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        personas = get_todays_personas()
        if not personas:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": "No personas scheduled today", "results": []}).encode())
            return

        results = []
        for persona in personas:
            result = run_for_persona(persona)
            results.append(result)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "Pipeline completed", "results": results}).encode())
