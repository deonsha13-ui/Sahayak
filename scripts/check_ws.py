"""End-to-end check through the running server: greeting audio out, PCM in, transcript back.

Run with:  PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe scripts/check_ws.py
"""

import asyncio
import base64
import json
import wave

import websockets

WS = "ws://127.0.0.1:8000/ws?lang=en"
AUDIO = "test_audio/roundtrip.wav"


async def main() -> int:
    with wave.open(AUDIO, "rb") as w:
        pcm = w.readframes(w.getnframes())
    print(f"input audio: {len(pcm)} bytes")

    async with websockets.connect(WS, max_size=None) as ws:

        async def until(kinds, timeout=40):
            seen, audio, deadline = [], 0, asyncio.get_event_loop().time() + timeout
            while True:
                left = deadline - asyncio.get_event_loop().time()
                if left <= 0:
                    raise TimeoutError(f"waiting for {kinds}, got {seen}")
                raw = await asyncio.wait_for(ws.recv(), left)
                msg = json.loads(raw)
                seen.append(msg.get("type"))
                if msg.get("type") == "audio":
                    audio += len(base64.b64decode(msg["data"]))
                if msg.get("type") in ("agent_text", "transcript_final"):
                    print(f"   {msg['type']}: {msg.get('text')}")
                if msg.get("type") in ("tts_error", "stt_error"):
                    print(f"   {msg['type']}: {msg.get('message')}")
                if msg.get("type") in kinds:
                    return msg, audio, seen
                if msg.get("type") == "audio_end" and "audio_end" in kinds:
                    return msg, audio, seen

        msg, audio, seen = await until({"audio_end"})
        print(f"1) greeting: {audio} bytes of speech ({audio / 48000:.2f}s) types={sorted(set(seen))}")

        await ws.send(json.dumps({"type": "ptt_start"}))
        await until({"ptt_ready"})
        print("2) ptt_ready, streaming mic audio")
        for i in range(0, len(pcm), 1024):
            await ws.send(pcm[i:i + 1024])
            await asyncio.sleep(0.03)
        await ws.send(json.dumps({"type": "ptt_end"}))

        print("3) waiting for transcript ...")
        found = None
        audio = 0
        deadline = asyncio.get_event_loop().time() + 45
        while found is None:
            left = deadline - asyncio.get_event_loop().time()
            if left <= 0:
                print("   FAIL: no transcript within 45 s")
                return 1
            raw = await asyncio.wait_for(ws.recv(), left)
            m = json.loads(raw)
            if m.get("type") == "transcript_final":
                found = m["text"]
            elif m.get("type") in ("stt_error", "tts_error"):
                print(f"   FAIL {m['type']}: {m.get('message')}")
                return 1

        # consume the spoken reply for the same utterance
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), 30)
                m = json.loads(raw)
                if m.get("type") == "audio":
                    audio += len(base64.b64decode(m["data"]))
                if m.get("type") == "agent_text":
                    print(f"   agent_text: {m['text']}")
                if m.get("type") == "audio_end":
                    break
        except TimeoutError:
            print("   no audio_end after transcript")

    print(f"4) transcript: {found}")
    print(f"   reply speech: {audio} bytes ({audio / 48000:.2f}s)")
    ok = bool(found and found.strip()) and audio > 0
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
