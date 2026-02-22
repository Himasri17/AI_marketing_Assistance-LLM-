import json
import re
import ollama
from PIL import Image
from typing import Literal

# -----------------------------------------------------
# Helpers
# -----------------------------------------------------

def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(cleaned)


def _call_ollama(prompt: str, image_path: str) -> str:
    """
    Vision call using Ollama + LLaVA (local & free).
    """

    response = ollama.chat(
        model="llava",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_path],  # <-- local image file path
            }
        ],
    )

    return response["message"]["content"]


# -----------------------------------------------------
# CREATOR MODE
# -----------------------------------------------------

def generate_description(
    image_path: str,
    length: Literal["short", "medium", "detailed"] = "medium",
    audience: Literal["general", "buyer", "student", "children"] = "general",
    tone: Literal["poetic", "informative", "storytelling", "academic"] = "poetic",
) -> dict:

    aud_map = {
        "general": "for the general public",
        "buyer": "for an art buyer",
        "student": "for a student or researcher",
        "children": "for children aged 8–12",
    }

    len_map = {
        "short": "2–3 sentences",
        "medium": "one well-crafted paragraph",
        "detailed": "2–3 rich paragraphs",
    }

    prompt = f"""
You are an expert on Indian tribal and folk art traditions.

Analyze the tribal artwork in the image.

Return ONLY valid JSON with exactly these fields:

{{
  "art_name": "Specific name of the artwork",
  "art_style": "Tribal art tradition identified",
  "region": "Indian state or region of origin",
  "english": "A {len_map[length]} description written in a {tone} tone, {aud_map[audience]}. Include motifs, cultural significance, symbolism."
}}
"""

    raw = _call_ollama(prompt, image_path)
    return _parse_json(raw)


# -----------------------------------------------------
# SCHOLAR MODE
# -----------------------------------------------------

def generate_history(
    image_path: str,
    question: str = "Tell me the history and origins of this art form.",
) -> dict:

    safe_q = question.replace('"', "'")

    prompt = f"""
You are a renowned scholar of Indian tribal art.

Look at this artwork and answer:

"{safe_q}"

Return ONLY valid JSON:

{{
  "art_name": "Artwork name",
  "art_style": "Art tradition",
  "region": "Region of origin",
  "question": "{safe_q}",
  "english": "A scholarly answer in 2–3 detailed paragraphs."
}}
"""

    raw = _call_ollama(prompt, image_path)

    data = _parse_json(raw)
    data["question"] = question
    return data