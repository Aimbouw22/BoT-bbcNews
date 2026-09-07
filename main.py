"""
Punto de entrada. Ejecuta el pipeline completo para UN short de noticias:
1. Obtiene la noticia mas importante de la BBC
2. Genera guion, titulo y hashtags en ingles (Gemini)
3. Descarga clip de video libre de derechos (Pexels)
4. Genera la voz narrada
5. Monta el video final (moviepy)
6. Sube a YouTube Shorts
7. Notifica por Telegram

Este script lo dispara GitHub Actions varias veces al dia.
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from config import WORKDIR  # noqa: E402
from fetch_news import fetch_top_news  # noqa: E402
from generate_content import generate_content  # noqa: E402
from fetch_clip import fetch_clip  # noqa: E402
from generate_voice import generate_voice  # noqa: E402
from build_video import build_video  # noqa: E402
from upload_youtube import upload_short  # noqa: E402
from telegram_notify import send_telegram_message  # noqa: E402


def run():
    os.makedirs(WORKDIR, exist_ok=True)

    print("0/6 Fetching the top BBC News story...")
    noticia = fetch_top_news()
    print("   Headline:", noticia["titulo"])

    print("1/6 Generating script, title and hashtags with Gemini...")
    content = generate_content(noticia["titulo"], noticia["resumen"])
    print("   Topic:", content["topic"])
    print("   Title:", content["title"])

    print("2/6 Downloading clip from Pexels...")
    clip_path = fetch_clip(content["pexels_query"])

    print("3/6 Generating narrated voice...")
    voice_path = generate_voice(content["script"])

    print("4/6 Building the final video...")
    video_path = build_video(
        clip_path=clip_path,
        voice_path=voice_path,
        title=content["title"],
        script_text=content["script"],
    )

    print("5/6 Uploading to YouTube...")
    url = upload_short(
        video_path=video_path,
        title=content["title"],
        description=content["description"],
        hashtags=content["hashtags"],
    )

    print("Uploaded successfully:", url)

    try:
        send_telegram_message(
            f"✅ <b>New short published</b>\n\n"
            f"📌 {content['title']}\n"
            f"🔗 {url}\n"
            f"🏷️ {' '.join(content['hashtags'])}"
        )
    except Exception as e:
        print(f"⚠️ Warning: could not notify via Telegram ({e}). The video was uploaded successfully.")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        error_text = f"❌ <b>Error generating the short</b>\n\n{type(e).__name__}: {e}"
        print(error_text)
        traceback.print_exc()
        try:
            send_telegram_message(error_text)
        except Exception:
            pass
        sys.exit(1)
