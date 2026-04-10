"""Main pipeline orchestrator.

Runs the full daily flow:
1. Select today's personas and their next topics
2. For each persona: generate script -> voice -> video -> post to Instagram
3. Log results and clean up old files
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / "config" / ".env")

from src.content_log import add_entry, cleanup_old_videos, get_posted_topics
from src.instagram_poster import post_reel
from src.persona_selector import get_next_topic, get_todays_personas
from src.script_generator import generate_script
from src.video_generator import generate_video

VIDEOS_DIR = PROJECT_ROOT / "data" / "videos"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "data" / "pipeline.log"),
    ],
)
log = logging.getLogger(__name__)


def retry(func, *args, max_retries=1, **kwargs):
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise
            wait = 2 ** (attempt + 1)
            log.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {wait}s: {e}")
            time.sleep(wait)


def notify_failure(persona_id, topic, error):
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
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        # Step 1: Generate script
        log.info(f"  Generating script...")
        result = retry(generate_script, persona, topic)
        script_text = result["script"]
        caption = result["caption"]
        hashtags = " ".join(result["hashtags"])
        full_caption = f"{caption}\n\n{hashtags}"
        log.info(f"  Script generated ({len(script_text.split())} words)")

        # Step 2: Generate avatar video (HeyGen handles TTS + avatar in one step)
        video_path = VIDEOS_DIR / f"{today}_{persona_id}.mp4"
        log.info(f"  Generating avatar video...")
        video_url = retry(
            generate_video,
            persona["heygen_avatar_id"],
            script_text,
            persona["heygen_voice_id"],
            str(video_path),
        )
        log.info(f"  Video saved to {video_path}")

        # Step 3: Post to Instagram (use HeyGen's hosted URL)
        log.info(f"  Posting to Instagram...")
        post_id = retry(post_reel, video_url, full_caption)
        log.info(f"  Posted! Instagram ID: {post_id}")

        # Step 4: Log success
        add_entry(persona_id, topic, script_text, str(video_path), post_id, "posted")
        log.info(f"  Logged to content history")

    except Exception as e:
        log.error(f"  FAILED for {persona_id}: {e}")
        add_entry(persona_id, topic, "", "", "", "failed")
        notify_failure(persona_id, topic, str(e))


def run_pipeline():
    log.info("=" * 60)
    log.info("Pipeline started")

    personas = get_todays_personas()
    if not personas:
        log.info("No personas scheduled for today. Exiting.")
        return

    log.info(f"Personas scheduled today: {[p['id'] for p in personas]}")

    for persona in personas:
        run_for_persona(persona)

    # Cleanup old videos
    removed = cleanup_old_videos(days=7)
    if removed:
        log.info(f"Cleaned up {removed} old video/audio files")

    log.info("Pipeline completed")
    log.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
