from __future__ import annotations

import os
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_KEY: str = os.environ["GEMINI_KEY"]


with open("src/utils/prompt.txt") as file:
    prompt = file.read()


def is_gibberish(phrase, threshold: float = 0.7):
    return False


client = genai.Client(api_key=GEMINI_KEY)


def get_doctor_id(symptom: str, doctors: str) -> str | None:
    if is_gibberish(symptom):
        return None

    uuid_v4_pattern = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt.replace("{0}", symptom).replace("{1}", doctors),
    )

    try:
        doctor_id = response.candidates[0].content.parts[0].text.strip()

        if uuid_v4_pattern.fullmatch(doctor_id):
            return doctor_id
    except Exception:
        return None

    return None
