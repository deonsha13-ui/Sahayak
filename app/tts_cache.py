"""In-memory TTS cache for the fixed dialogue turns.

The greeting, the five follow-up questions, the confirmation and the save
acknowledgement never change, so they are synthesised once at startup per
language and held as raw 24 kHz PCM. A cached turn starts speaking in <50 ms
instead of waiting for a Gnani round trip; anything not cached is synthesised
live and stored on the way through.
"""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator

from app import i18n

# (language, exact text) -> raw 16-bit mono 24 kHz PCM
_CACHE: dict[tuple[str, str], bytes] = {}
_sem = asyncio.Semaphore(4)
STATS = {"phrases": 0, "languages": 0, "failed": 0, "enabled": True}

# ~100 ms of audio per websocket frame.
CHUNK_BYTES = 4800


def enabled() -> bool:
    return os.getenv("SAHAYAK_PRECACHE", "1").strip() not in ("0", "false", "off")


def cached(lang: str, text: str) -> bytes | None:
    return _CACHE.get((i18n.normalize_lang(lang), text))


def put(lang: str, text: str, pcm: bytes) -> None:
    if pcm:
        _CACHE[(i18n.normalize_lang(lang), text)] = pcm


def stats() -> dict:
    langs = {lang for lang, _ in _CACHE}
    return {
        "phrases": len(_CACHE),
        "languages": len(langs),
        "failed": STATS["failed"],
        "enabled": enabled(),
    }


async def _synthesize(text: str, lang: str, timeout: float) -> bytes | None:
    from app.gnani_tts import synthesize

    try:
        async with asyncio.timeout(timeout):
            chunks = []
            async for chunk in synthesize(text, language=i18n.locale_for(lang)):
                chunks.append(chunk)
            return b"".join(chunks) or None
    except Exception as exc:  # noqa: BLE001 - startup must never crash on TTS
        STATS["failed"] += 1
        print(f"[cache] skip {i18n.normalize_lang(lang)}: {type(exc).__name__}: {exc}")
        return None


async def _guarded(text: str, lang: str, timeout: float) -> None:
    async with _sem:
        pcm = await _synthesize(text, lang, timeout)
    if pcm:
        put(lang, text, pcm)


async def prewarm(languages: list[str] | None = None, timeout: float = 15) -> dict:
    """Synthesise every fixed phrase for every language, in parallel."""
    if not enabled():
        STATS["enabled"] = False
        print("[cache] Disabled by SAHAYAK_PRECACHE")
        return stats()

    languages = [i18n.normalize_lang(code) for code in (languages or i18n.SUPPORTED)]
    jobs = []
    for lang in languages:
        for _key, text in i18n.fixed_phrases(lang):
            if cached(lang, text):
                continue
            jobs.append(_guarded(text, lang, timeout))

    if jobs:
        loop = asyncio.get_running_loop()
        budget = float(os.getenv("SAHAYAK_PRECACHE_BUDGET", "25"))
        started = loop.time()
        try:
            await asyncio.wait_for(asyncio.gather(*jobs), timeout=budget)
        except (asyncio.TimeoutError, TimeoutError):
            print(f"[cache] Startup budget of {budget:.0f}s reached; keeping partial cache")
        elapsed = loop.time() - started
    else:
        elapsed = 0.0

    info = stats()
    if info["phrases"]:
        print(f"[cache] Ready: {info['phrases']} phrases cached "
              f"across {info['languages']} languages in {elapsed:.1f}s")
    else:
        print("[cache] Ready: 0 phrases cached "
              "(TTS unavailable - live synthesis will be used)")
    return info


async def speak(text: str, lang: str) -> AsyncIterator[bytes]:
    """Yield PCM for a phrase, from cache when possible, else live."""
    lang = i18n.normalize_lang(lang)
    hit = cached(lang, text)
    if hit:
        for i in range(0, len(hit), CHUNK_BYTES):
            yield hit[i:i + CHUNK_BYTES]
        return

    from app.gnani_tts import synthesize

    collected = []
    async for chunk in synthesize(text, language=i18n.locale_for(lang)):
        if not chunk:
            continue
        collected.append(chunk)
        yield chunk
    if collected:
        put(lang, text, b"".join(collected))
