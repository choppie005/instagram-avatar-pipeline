import json
from datetime import datetime
from pathlib import Path

PERSONAS_PATH = Path(__file__).parent.parent / "config" / "personas.json"


def load_personas():
    with open(PERSONAS_PATH, "r") as f:
        return json.load(f)["personas"]


def get_todays_personas():
    today = datetime.now().strftime("%A").lower()
    personas = load_personas()
    return [p for p in personas if today in p["posting_days"]]


def get_next_topic(persona, posted_topics):
    topics = persona["topics"]
    for topic in topics:
        if topic not in posted_topics:
            return topic
    # All topics posted — cycle back from the beginning
    cycle_count = len(posted_topics) // len(topics)
    cycle_offset = len(posted_topics) % len(topics)
    return topics[cycle_offset]
