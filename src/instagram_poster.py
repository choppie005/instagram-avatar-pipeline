import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
IG_USER_ID = os.getenv("INSTAGRAM_USER_ID")


def post_reel(video_url, caption, access_token=None, ig_user_id=None):
    """Post a video as an Instagram Reel.

    Args:
        video_url: Public URL where the video can be fetched by Instagram.
                   The video must be hosted at a publicly accessible URL.
        caption: The caption text including hashtags.
        access_token: Override the default access token.
        ig_user_id: Override the default Instagram user ID.

    Returns:
        The Instagram media ID of the published post.
    """
    token = access_token or ACCESS_TOKEN
    user_id = ig_user_id or IG_USER_ID

    # Step 1: Create media container
    container_resp = requests.post(
        f"{GRAPH_API_BASE}/{user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token,
        },
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    # Step 2: Wait for container to be ready
    _wait_for_container(container_id, token)

    # Step 3: Publish
    publish_resp = requests.post(
        f"{GRAPH_API_BASE}/{user_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": token,
        },
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]


def _wait_for_container(container_id, access_token, timeout=300, interval=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{GRAPH_API_BASE}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": access_token,
            },
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")

        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Instagram container failed: {resp.json()}")

        time.sleep(interval)

    raise TimeoutError(f"Instagram container not ready after {timeout}s")
