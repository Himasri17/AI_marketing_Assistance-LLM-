import os
import base64
import json
import re
from io import BytesIO
from typing import Literal
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------------------------------
# Load API key
# -----------------------------------------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------------------------------
# Helpers
# -----------------------------------------------------

def _image_to_base64(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _parse_json(raw: str) -> dict:
    """
    Clean markdown fences and safely parse JSON.
    """
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(cleaned)


def _call_openai(prompt: str, b64_image: str) -> str:
    """
    Vision call using Chat Completions (stable API).
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Vision-capable + cheaper
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=800,
    )

    return response.choices[0].message.content


# -----------------------------------------------------
# CREATOR MODE
# -----------------------------------------------------

def generate_description(
    image: Image.Image,
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

    b64 = _image_to_base64(image)
    raw = _call_openai(prompt, b64)
    return _parse_json(raw)


# -----------------------------------------------------
# SCHOLAR MODE
# -----------------------------------------------------

def generate_history(
    image: Image.Image,
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

    b64 = _image_to_base64(image)
    raw = _call_openai(prompt, b64)

    data = _parse_json(raw)
    data["question"] = question  # preserve original formatting
    return data