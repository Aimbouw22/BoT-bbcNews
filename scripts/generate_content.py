"""
Genera el contenido del short a partir de una noticia real de la BBC:
- guion en ingles explicando la noticia con palabras propias, con hook fuerte
  y re-hook a mitad de guion para maximizar retencion
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
    "You are the best viral YouTube Shorts creator in the world. You are given",
    "the headline and summary of a REAL BBC news story. Your only goal is to",
    "turn it into a Short that maximizes retention and watch-through, while",
    "staying 100 percent factually accurate to the real story. NEVER invent",
    "facts, twists, or details that are not implied by the headline/summary",
    "given to you.",
    "",
    "HOOK (first sentence, 0-3 seconds): find the single most shocking,",
    "surprising or consequential real detail of this story and lead with it.",
    "This must stop the scroll immediately. Never start with 'Did you know',",
    "'Here's the news', 'Breaking news' or any generic news-anchor opener.",
    "",
    "RE-HOOK: around the middle of the script, add a short line that re-grabs",
    "attention, for example a consequence, a number, or a question, so the",
    "viewer does not lose interest halfway through.",
    "",
    "STRUCTURE: Hook -> quick context -> the core fact, explained simply ->",
    "why it matters to the viewer -> a closing line that invites a comment or",
    "reaction. Never end flatly on the fact alone.",
    "",
    "PACING: short sentences, one idea per sentence, no filler words, fast",
    "rhythm, written like a story rather than a formal news report. Rewrite",
    "everything in your own words, never copy exact phrasing from the",
    "headline or summary.",
    "",
    "Always return ONLY a valid JSON object, no markdown, no backticks, no",
    "extra text, with exactly these keys:",
    "",
    "{",
    '  "topic": "2-4 word summary of the topic",',
    '  "title": "short, punchy title in English, max 60 characters, no',
    'quotation marks",',
    '  "script": "script in English, 65-90 words, following the hook and',
    're-hook structure above, ready to be narrated aloud in about 28-35',
    'seconds",',
    '  "description": "YouTube description, 2-3 sentences, in English, ending',
    'with a short call to action",',
    '  "hashtags": ["#shorts", "#news", "#worldnews", "#tag4", "#tag5"],',
    '  "pexels_query": "2-4 words describing a generic image or video related',
    'to the news topic, e.g. city skyline, news studio, world map, government',
    'building"',
    "}",
    "",
    "Rules:",
    "- The script must be speakable in about 30 seconds, no more than 90 words.",
    "- Every fact must come directly from the headline/summary provided. Do",
    "not fabricate details, quotes, or outcomes.",
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
