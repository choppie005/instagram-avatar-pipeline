import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
HEYGEN_BASE_URL = "https://api.heygen.com"


def generate_video(avatar_id, script_text, heygen_voice_id, output_path):
    """Generate an avatar video using HeyGen's text-to-video with built-in TTS.

    Uses standing/full-body avatars with natural gestures and expressions.
    HeyGen handles TTS + avatar animation in one step.
    """
    headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                },
                "voice": {
                    "type": "text",
                    "input_text": script_text,
                    "voice_id": heygen_voice_id,
                    "speed": 1.0,
                },
            }
        ],
        "dimension": {"width": 1080, "height": 1920},
    }

    resp = requests.post(
        f"{HEYGEN_BASE_URL}/v2/video/generate",
        headers=headers,
        json=payload,
    )
    resp.raise_for_status()
    video_id = resp.json()["data"]["video_id"]

    # Poll for completion
    video_url = _poll_heygen_status(video_id, headers)

    # Download
    _download_file(video_url, output_path)
    return video_url


def _poll_heygen_status(video_id, headers, timeout=900, interval=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{HEYGEN_BASE_URL}/v1/video_status.get",
            headers=headers,
            params={"video_id": video_id},
        )
        resp.raise_for_status()
        data = resp.json()["data"]

        if data["status"] == "completed":
            return data["video_url"]
        if data["status"] == "failed":
            raise RuntimeError(f"HeyGen video generation failed: {data.get('error')}")

        time.sleep(interval)

    raise TimeoutError(f"HeyGen video generation timed out after {timeout}s")


def _download_file(url, output_path):
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
