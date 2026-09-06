"""
Genera el contenido del short usando Gemini:
- tema de curiosidad (evitando repetir temas usados recientemente)
- guion narrado (~28-32s hablado)
- titulo llamativo para YouTube Shorts
- descripcion + hashtags
- query en ingles para buscar el clip de video en Pexels
"""
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timedelta

from google import genai
from google.genai import errors as genai_errors

from config import GEMINI_API_KEY, TOPICS_FILE

client = genai.Client(api_key=GEMINI_API_KEY)

DIAS_ENFRIAMIENTO = 30

_PROMPT_LINEAS = [
    "Eres un guionista experto en YouTube Shorts de curiosidades y datos random",
    "(ciencia, historia, animales, espacio, cuerpo humano, tecnologia, etc.).",
    "",
    "Devuelve SIEMPRE y UNICAMENTE un JSON valido (sin markdown, sin backticks,",
    "sin texto extra) con estas claves exactas:",
    "",
    "{",
    '  "topic": "tema corto en 2-4 palabras, usado para no repetir temas",',
    '  "title": "titulo en espanol, maximo 60 caracteres, con gancho o curiosidad, sin comillas",',
    '  "script": "guion en espanol, 65-85 palabras, tono cercano y sorprendente,',
    "empieza con un gancho fuerte en la primera frase, sin emojis, listo para",
    'ser narrado en voz alta en unos 28-32 segundos",',
    '  "description": "descripcion para YouTube de 2-3 frases, en espanol",',
    '  "hashtags": ["#shorts", "#curiosidades", "#dato3", "#dato4", "#dato5"],',
    '  "pexels_query": "2-4 palabras en ingles que describan una imagen o video',
    "generico relacionado con el tema, ej. ocean waves, brain neurons, ancient ruins\"",
    "}",
    "",
    "Reglas:",
    "- El guion debe caber hablado en 30 segundos aproximadamente, no mas de 85 palabras.",
    "- No repitas ninguno de los temas ya usados que se te pasan.",
    "- El pexels_query debe describir algo visual generico y facil de encontrar en",
    "un banco de stock, paisajes, naturaleza, ciudad, laboratorio, espacio, animales,",
    "no algo demasiado especifico.",
]
SYSTEM_PROMPT = "\n".join(_PROMPT_LINEAS)


def _normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return texto


def _load_used_topics():
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_used_topic(topic):
    used = _load_used_topics()
    used.append({"topic": topic, "date": datetime.utcnow().isoformat()})
    used = used[-200:]
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def _temas_en_enfriamiento(dias=DIAS_ENFRIAMIENTO):
    used = _load_used_topics()
    limite = datetime.utcnow() - timedelta(days=dias)
    recientes = []
    for t in used:
        try:
            fecha = datetime.fromisoformat(t["date"])
        except (KeyError, ValueError):
            fecha = datetime.utcnow()
        if fecha >= limite:
            recientes.append(_normalizar(t["topic"]))
    return set(recientes)


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE)
    return json.loads(text)


def _call_gemini(user_prompt, temperature=1.0):
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
            print("Gemini sobrecargado (intento " + str(attempt) + "/" + str(max_retries) + "), reintentando en " + str(wait) + "s...")
            time.sleep(wait)
    raise last_error


def generate_content():
    used_normalizados = _temas_en_enfriamiento()
    used_topics_str = ", ".join(t["topic"] for t in _load_used_topics()[-40:]) or "ninguno todavia"

    max_intentos_tema = 4
    data = None

    for intento in range(1, max_intentos_tema + 1):
        user_prompt = (
            "Temas usados recientemente (NO los repitas, ni nada muy parecido): "
            + used_topics_str + "\n\nGenera un short nuevo."
        )
        response = _call_gemini(user_prompt, temperature=1.0 + intento * 0.1)
        data = _extract_json(response.text)

        if _normalizar(data["topic"]) not in used_normalizados:
            _save_used_topic(data["topic"])
            return data

        print("Tema en enfriamiento ('" + data["topic"] + "'), reintentando (" + str(intento) + "/" + str(max_intentos_tema) + ")...")

    data["topic"] = data["topic"] + " (variante " + str(len(used_normalizados) + 1) + ")"
    print("Forzando variante tras agotar reintentos: " + data["topic"])
    _save_used_topic(data["topic"])
    return data


if __name__ == "__main__":
    content = generate_content()
    print(json.dumps(content, ensure_ascii=False, indent=2))
