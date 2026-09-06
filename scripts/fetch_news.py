"""
Obtiene el titular de noticia mas importante del feed RSS publico de la BBC.
No usamos el texto literal en el video: solo sirve como base para que Gemini
redacte su propio guion explicando la noticia.
"""
import feedparser

BBC_FEED_URL = "http://feeds.bbci.co.uk/news/rss.xml"


def fetch_top_news():
    feed = feedparser.parse(BBC_FEED_URL)
    if not feed.entries:
        raise RuntimeError("No se pudo obtener ninguna noticia del feed de la BBC.")

    entrada = feed.entries[0]
    titulo = entrada.get("title", "").strip()
    resumen = entrada.get("summary", "").strip()

    return {"titulo": titulo, "resumen": resumen}


if __name__ == "__main__":
    noticia = fetch_top_news()
    print("Titular:", noticia["titulo"])
    print("Resumen:", noticia["resumen"])
