import json
import os

from dotenv import load_dotenv
from app.ws_client import ws_connect

load_dotenv()

STT_URL = "wss://api.vachana.ai/stt/v3/stream"
FRAME_BYTES = 1024  # the server needs exactly 1024-byte frames of 16-bit mono PCM

# Healthcare vocabulary biasing, per the Gnani Prisma v3.0 contract.
KEYTERMS = [
    "ANC",
    "PNC",
    "PHC",
    "TT injection",
    "IFA",
    "Anganwadi",
    "BCG",
    "OPV",
    "Pentavalent",
    "ASHA",
]
TOPIC = (
    "ASHA community health worker home visit register for maternal, "
    "newborn and child healthcare"
)


class STTStream:
    def __init__(self, language_code: str = "indic-auto", sample_rate: int = 16000,
                 min_silence_ms: int = 800):
        key = os.getenv("GNANI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GNANI_API_KEY is empty. Check your .env file.")
        self.headers = {
            "x-api-key-id": key,
            "model": "prisma-v3.0",
            "language_code": language_code,
            "x-sample-rate": str(sample_rate),
            "x-min-silence-ms": str(min_silence_ms),
            "x-idle-timeout-sec": "300",
            "keyterms": json.dumps(KEYTERMS),
            "topic": TOPIC,
        }
        self.ws = None
        self._buf = b""

    async def __aenter__(self):
        self.ws = await ws_connect(
            STT_URL, headers=self.headers, max_size=None
        )
        return self

    async def __aexit__(self, *exc):
        if self.ws:
            await self.ws.close()

    async def send_pcm(self, pcm: bytes):
        """Accepts any amount of PCM and sends it as exact 1024-byte frames."""
        self._buf += pcm
        while len(self._buf) >= FRAME_BYTES:
            await self.ws.send(self._buf[:FRAME_BYTES])
            self._buf = self._buf[FRAME_BYTES:]

    async def flush(self):
        """Zero-pad the tail so no captured audio is left unsent."""
        if self._buf:
            padded = self._buf + bytes(FRAME_BYTES - len(self._buf))
            await self.ws.send(padded[:FRAME_BYTES])
            self._buf = b""

    async def commit(self):
        """Close the current utterance now (use when she releases push-to-talk)."""
        await self.flush()
        await self.ws.send(json.dumps({"type": "commit"}))

    async def events(self):
        """Yields server messages: connected, speech_start, processing, transcript, error."""
        async for raw in self.ws:
            if isinstance(raw, bytes):
                continue
            yield json.loads(raw)
