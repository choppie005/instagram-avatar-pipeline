import json
import os

from google import genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are a scriptwriter for short-form Instagram Reels about finance and business.
You write scripts that are spoken aloud by an AI avatar — conversational, engaging, and concise.

Rules:
- Script MUST be 150-180 words (60 seconds spoken)
- Start with a hook in the first sentence (question, bold claim, or surprising fact)
- Use simple language, short sentences
- End with a clear call-to-action (follow, comment, save)
- No stage directions, emojis, or formatting — just the spoken words

Also generate:
- A short Instagram caption (1-2 sentences + relevant emojis)
- 5-8 relevant hashtags

Return your response as JSON only, no markdown fences:
{
  "script": "the spoken script...",
  "caption": "the Instagram caption...",
  "hashtags": ["#tag1", "#tag2"]
}"""


def generate_script(persona, topic):
    user_prompt = (
        f"Persona: {persona['name']}\n"
        f"Tone: {persona['tone']}\n"
        f"Niche: {persona['niche']}\n"
        f"Topic: {topic}\n\n"
        f"Write a 60-second Instagram Reel script about '{topic}'."
    )

    models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]
    last_error = None

    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "max_output_tokens": 1024,
                    "response_mime_type": "application/json",
                },
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = e
            continue

    raise last_error
