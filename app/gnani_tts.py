import base64
import json
import os

from dotenv import load_dotenv
from app.ws_client import ws_connect

load_dotenv()

TTS_URL = "wss://api.vachana.ai/api/v1/tts"


async def synthesize(text: str, language: str = "auto", voice: str = "Shivani",
                     sample_rate: int = 24000, model: str = "timbre-v3.0"):
    """Async generator that yields raw 16-bit mono PCM chunks as they arrive."""
    key = os.getenv("GNANI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GNANI_API_KEY is empty. Check your .env file.")

    request = {
        "text": text,
        "voice": voice,
        "model": model,
        "language": language,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": sample_rate,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "raw",
        },
    }
    async with ws_connect(
        TTS_URL, headers={"X-API-Key-ID": key}, max_size=None
    ) as ws:
        await ws.send(json.dumps(request))
        async for raw in ws:
            msg = json.loads(raw)
            kind = msg.get("type")
            if kind == "audio":
                audio = msg.get("data", {}).get("audio")
                if audio:
                    yield base64.b64decode(audio)
            elif kind == "complete":
                break
            elif kind == "error":
                raise RuntimeError(f"TTS error: {msg.get('message')}")
            