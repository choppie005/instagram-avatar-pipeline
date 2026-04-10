"""One-time persona setup script.

Walks through each persona and helps you:
1. Generate face images using Flux via fal.ai
2. Create a HeyGen photo avatar from the generated face
3. Select/create an ElevenLabs voice
4. Save all IDs back to personas.json
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / "config" / ".env")

PERSONAS_PATH = PROJECT_ROOT / "config" / "personas.json"
FACES_DIR = PROJECT_ROOT / "data" / "faces"
FACES_DIR.mkdir(exist_ok=True)

FAL_API_KEY = os.getenv("FAL_API_KEY")
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


def generate_face_image(persona_name, persona_niche, index=0):
    """Generate a photorealistic face using Flux via fal.ai."""
    print(f"\n  Generating face image {index + 1} for {persona_name}...")

    prompt = (
        f"Professional headshot portrait photo of a {persona_name}, "
        f"an Indian content creator who covers {persona_niche}. "
        f"Looking directly at camera, friendly expression, neutral background, "
        f"studio lighting, high resolution, photorealistic"
    )

    resp = requests.post(
        "https://queue.fal.run/fal-ai/flux/dev",
        headers={
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "image_size": "square_hd",
            "num_images": 1,
        },
    )
    resp.raise_for_status()
    result = resp.json()

    image_url = result["images"][0]["url"]
    image_path = FACES_DIR / f"{persona_name.replace(' ', '_')}_{index}.png"

    # Download the image
    img_resp = requests.get(image_url)
    img_resp.raise_for_status()
    with open(image_path, "wb") as f:
        f.write(img_resp.content)

    print(f"  Saved to: {image_path}")
    return str(image_path)


def create_heygen_avatar(image_path, persona_name):
    """Create a HeyGen photo avatar from an image."""
    print(f"\n  Creating HeyGen avatar for {persona_name}...")

    headers = {"X-Api-Key": HEYGEN_API_KEY}

    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://api.heygen.com/v1/photo_avatar",
            headers=headers,
            files={"file": (f"avatar_{persona_name}.png", f, "image/png")},
        )

    resp.raise_for_status()
    avatar_id = resp.json()["data"]["photo_avatar_id"]
    print(f"  HeyGen avatar ID: {avatar_id}")
    return avatar_id


def list_elevenlabs_voices():
    """List available ElevenLabs voices."""
    resp = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
    )
    resp.raise_for_status()
    voices = resp.json()["voices"]
    return [(v["voice_id"], v["name"]) for v in voices]


def setup_persona(persona):
    """Set up a single persona interactively."""
    persona_id = persona["id"]
    persona_name = persona["name"]
    persona_niche = persona["niche"]

    print(f"\n{'='*50}")
    print(f"Setting up: {persona_name} ({persona_id})")
    print(f"Niche: {persona_niche}")
    print(f"{'='*50}")

    # Step 1: Generate face images
    print("\n--- Step 1: Generate Face Images ---")
    num_images = int(input("How many face variations to generate? [5]: ") or "5")
    image_paths = []
    for i in range(num_images):
        path = generate_face_image(persona_name, persona_niche, i)
        image_paths.append(path)

    print(f"\nGenerated {len(image_paths)} images in {FACES_DIR}/")
    print("Please review the images and select the best one.")
    selected = int(input(f"Enter the image number (0-{num_images - 1}): "))
    selected_path = image_paths[selected]

    # Step 2: Create HeyGen avatar
    print("\n--- Step 2: Create HeyGen Avatar ---")
    avatar_id = create_heygen_avatar(selected_path, persona_name)

    # Step 3: Select ElevenLabs voice
    print("\n--- Step 3: Select ElevenLabs Voice ---")
    voices = list_elevenlabs_voices()
    print("\nAvailable voices:")
    for i, (vid, vname) in enumerate(voices):
        print(f"  [{i}] {vname} (ID: {vid})")

    voice_choice = int(input("\nSelect a voice number: "))
    voice_id = voices[voice_choice][0]
    print(f"Selected voice: {voices[voice_choice][1]} ({voice_id})")

    return avatar_id, voice_id


def main():
    with open(PERSONAS_PATH, "r") as f:
        config = json.load(f)

    print("Instagram Avatar Pipeline — Persona Setup")
    print("This script will set up face images, avatars, and voices for each persona.\n")
    print("Make sure you have set up your API keys in config/.env first!")

    for persona in config["personas"]:
        if "<REPLACE" not in persona["heygen_avatar_id"]:
            skip = input(f"\n{persona['name']} already has an avatar ID. Reconfigure? [y/N]: ")
            if skip.lower() != "y":
                continue

        avatar_id, voice_id = setup_persona(persona)
        persona["heygen_avatar_id"] = avatar_id
        persona["elevenlabs_voice_id"] = voice_id

        # Save after each persona (in case of interruption)
        with open(PERSONAS_PATH, "w") as f:
            json.dump(config, f, indent=2)
        print(f"\nSaved {persona['name']}'s IDs to personas.json")

    print("\n" + "=" * 50)
    print("All personas configured!")
    print("You can now run the pipeline: python src/pipeline.py")


if __name__ == "__main__":
    main()
