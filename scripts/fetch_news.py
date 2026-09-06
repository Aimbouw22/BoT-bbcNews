"""
Obtiene un titular de noticia del feed RSS publico de la BBC, evitando repetir
el mismo titular usado en las ultimas horas. No usamos el texto literal en el
video: solo sirve como base para que Gemini redacte su propio guion.
"""
import json
import os
import unicodedata
import difflib
from datetime import datetime, timedelta

import feedparser

from config import TOPICS_FILE

BBC_FEED_URL = "http://feeds.bbci.co.uk/news/rss.xml"
HORAS_ENFRIAMIENTO = 5
UMBRAL_SIMILITUD = 0.6


def _normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return texto


def _load_used_headlines():
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_used_headline(titulo):
    used = _load_used_headlines()
    used.append({"topic": titulo, "date": datetime.utcnow().isoformat()})
    used = used[-100:]
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def _recientes(horas=HORAS_ENFRIAMIENTO):
    used = _load_used_headlines()
    limite = datetime.utcnow() - timedelta(hours=horas)
    recientes = []
    for t in used:
        try:
            fecha = datetime.fromisoformat(t["date"])
        except (KeyError, ValueError):
            fecha = datetime.utcnow()
        if fecha >= limite:
            recientes.append(_normalizar(t["topic"]))
    return recientes


def _es_similar(titulo, recientes):
    titulo_norm = _normalizar(titulo)
    for previo in recientes:
        ratio = difflib.SequenceMatcher(None, titulo_norm, previo).ratio()
        if ratio >= UMBRAL_SIMILITUD:
            return True
    return False


def fetch_top_news():
    feed = feedparser.parse(BBC_FEED_URL)
    if not feed.entries:
        raise RuntimeError("No se pudo obtener ninguna noticia del feed de la BBC.")

    recientes = _recientes()

    for entrada in feed.entries[:10]:
        titulo = entrada.get("title", "").strip()
        resumen = entrada.get("summary", "").strip()

        if not _es_similar(titulo, recientes):
            _save_used_headline(titulo)
            return {"titulo": titulo, "resumen": resumen}

    # si las 10 primeras estan todas repetidas, usamos la primera igualmente
    entrada = feed.entries[0]
    titulo = entrada.get("title", "").strip()
    resumen = entrada.get("summary", "").strip()
    _save_used_headline(titulo)
    return {"titulo": titulo, "resumen": resumen}


if __name__ == "__main__":
    noticia = fetch_top_news()
    print("Titular:", noticia["titulo"])
    print("Resumen:", noticia["resumen"])
