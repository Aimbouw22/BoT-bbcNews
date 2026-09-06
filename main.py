"""
Punto de entrada. Ejecuta el pipeline completo para UN short:
1. Genera tema + guion + título + hashtags (Gemini)
2. Descarga clip de vídeo libre de derechos (Pexels)
3. Genera la voz narrada (edge-tts)
4. Monta el vídeo final (moviepy)
5. Sube a YouTube Shorts
6. Notifica por Telegram

Este script lo dispara GitHub Actions varias veces al día.
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from config import WORKDIR  # noqa: E402
from generate_content import generate_content  # noqa: E402
from fetch_clip import fetch_clip  # noqa: E402
from generate_voice import generate_voice  # noqa: E402
from build_video import build_video  # noqa: E402
from upload_youtube import upload_short  # noqa: E402
from telegram_notify import send_telegram_message  # noqa: E402


def run():
    os.makedirs(WORKDIR, exist_ok=True)

    print("1/5 Generando guion, título y hashtags con Gemini...")
    content = generate_content()
    print("   Tema:", content["topic"])
    print("   Título:", content["title"])

    print("2/5 Descargando clip de Pexels...")
    clip_path = fetch_clip(content["pexels_query"])

    print("3/5 Generando voz narrada...")
    voice_path = generate_voice(content["script"])

    print("4/5 Montando el vídeo final...")
    video_path = build_video(
        clip_path=clip_path,
        voice_path=voice_path,
        title=content["title"],
        script_text=content["script"],
    )

    print("5/5 Subiendo a YouTube...")
    url = upload_short(
        video_path=video_path,
        title=content["title"],
        description=content["description"],
        hashtags=content["hashtags"],
    )

    print("Subido correctamente:", url)

    send_telegram_message(
        f"✅ <b>Nuevo short publicado</b>\n\n"
        f"📌 {content['title']}\n"
        f"🔗 {url}\n"
        f"🏷️ {' '.join(content['hashtags'])}"
    )


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        error_text = f"❌ <b>Error generando el short</b>\n\n{type(e).__name__}: {e}"
        print(error_text)
        traceback.print_exc()
        try:
            send_telegram_message(error_text)
        except Exception:
            pass
        sys.exit(1)
