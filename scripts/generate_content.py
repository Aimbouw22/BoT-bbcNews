"""
Genera el contenido del short a partir de una noticia real de la BBC:
- guion en ingles explicando la noticia con palabras propias
- titulo, descripcion y hashtags
- query en ingles para buscar el clip de video en Pexels
"""
import json
import re
import time

from google import genai
from google.genai import errors as genai_errors

from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

_PROMPT_LINEAS = [
    "You are a scriptwriter for a short, punchy news bulletin made for YouTube",
    "Shorts. You are given the headline and summary of a real BBC news story.",
    "Your job is to explain it in ENGLISH, IN YOUR OWN WORDS, clearly and",
    "directly, like a serious but approachable news commentator. NEVER copy",
    "exact sentences from the headline or summary you are given, rewrite it",
    "completely in your own words.",
    "",
    "THE FIRST SENTENCE must grab attention immediately by making clear why",
    "this story matters, without being falsely sensational or alarmist.",
    "",
    "Always return ONLY a valid JSON object (no markdown, no backticks, no",
    "extra text) with exactly these keys:",
    "",
    "{",
    '  "topic": "2-4 word summary of the topic",',
    '  "title": "title in English, max 60 characters, informative with a hook,',
    'no quotation marks",',
    '  "script": "script in English, 65-85 words, explaining the news story in',
    'your own words, serious but approachable tone, no emojis, ready to be',
    'narrated aloud in about 28-32 seconds",',
    '  "description": "YouTube description, 2-3 sentences, in English",',
    '  "hashtags": ["#shorts", "#news", "#worldnews", "#tag4", "#tag5"],',
    '  "pexels_query": "2-4 words describing a generic image or video related to',
    'the news topic, e.g. city skyline, news studio, world map, government',
    'building"',
    "}",
    "",
    "Rules:",
    "- The script must be speakable in about 30 seconds, no more than 85 words.",
    "- Do not invent facts that are not in the headline/summary provided.",
    "- The pexels_query must describe something generic and easy to find in a",
    "stock footage library, not something too specific.",
]
SYSTEM_PROMPT = "\n".join(_PROMPT_LINEAS)


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE)
    return json.loads(text)


def _call_gemini(user_prompt, temperature=0.9):
    max_retries = 3
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_prompt,
                config={"system_instruction": SYSTEM_PROMPT, "temperature": temperature},
            )
        except genai_errors.ServerError as e:
            last_error = e
            wait = 15 * attempt
            print("Gemini overloaded (attempt " + str(attempt) + "/" + str(max_retries) + "), retrying in " + str(wait) + "s...")
            time.sleep(wait)
    raise last_error


def generate_content(noticia_titulo, noticia_resumen):
    user_prompt = (
        "BBC headline: " + noticia_titulo + "\n"
        "Summary: " + noticia_resumen + "\n\n"
        "Generate the short explaining this news story in your own words."
    )

    response = _call_gemini(user_prompt, temperature=0.9)
    data = _extract_json(response.text)
    return data


if __name__ == "__main__":
    from fetch_news import fetch_top_news
    noticia = fetch_top_news()
    content = generate_content(noticia["titulo"], noticia["resumen"])
    print(json.dumps(content, ensure_ascii=False, indent=2))
