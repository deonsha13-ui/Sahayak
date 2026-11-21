"""Deterministic language identification for the eight supported languages.

The STT layer returns the worker's words in the script she spoke, so the
Unicode block is enough to pick a language without spending an LLM call.
Devanagari is shared by Hindi and Marathi, so a small set of Marathi function
words decides between them. A Latin-script mention of a language name next to
a switch cue ("speak in Tamil") is honoured as an explicit request.
"""

from __future__ import annotations

import re

# script -> (language code, first code point, last code point)
_SCRIPTS = {
    "bengali": ("bn", 0x0980, 0x09FF),
    "tamil": ("ta", 0x0B80, 0x0BFF),
    "telugu": ("te", 0x0C00, 0x0C7F),
    "kannada": ("kn", 0x0C80, 0x0CFF),
    "malayalam": ("ml", 0x0D00, 0x0D7F),
}

_DEVANAGARI = (0x0900, 0x097F)

# Function words that only Marathi uses; Hindi shares the script but not these.
_MARATHI_MARKERS = (
    "आहे",
    "आहेत",
    "आणि",
    "नाही",
    "मला",
    "माझ",
    "तुम्ही",
    "काय",
    "करा",
    "झाले",
    "मध्ये",
    "पण",
    "सांगा",
    "ठेवा",
)

_LATIN_LANGUAGE_NAMES = {
    "tamil": "ta",
    "telugu": "te",
    "kannada": "kn",
    "malayalam": "ml",
    "bengali": "bn",
    "bangla": "bn",
    "marathi": "mr",
    "hindi": "hi",
    "english": "en",
}

# "speak in tamil", "tamil me bolo", "switch to telugu"
_SWITCH_CUE_RE = re.compile(
    r"\b(?:speak|talk|say|switch|change|continue|answer|reply|in|me|mein|lo|la)\b",
    re.IGNORECASE,
)

# Require at least 8 script characters so a stray background whisper doesn't trigger a language jump.
MIN_SCRIPT_CHARS = 8


def _count_in_range(text: str, low: int, high: int) -> int:
    return sum(1 for ch in text if low <= ord(ch) <= high)


def script_language(text: str) -> str | None:
    """Language inferred from the script of ``text``, or None."""
    text = text or ""
    counts = {
        code: _count_in_range(text, low, high)
        for code, low, high in _SCRIPTS.values()
    }
    best_code, best_count = max(counts.items(), key=lambda item: item[1])
    devanagari = _count_in_range(text, *_DEVANAGARI)

    if best_count >= MIN_SCRIPT_CHARS and best_count >= devanagari:
        return best_code
    if devanagari >= MIN_SCRIPT_CHARS:
        if any(marker in text for marker in _MARATHI_MARKERS):
            return "mr"
        return "hi"
    return None


def detect_language(text: str) -> str | None:
    """Return a supported language code for an utterance, or None.

    None means "no evidence of a different language" - the caller keeps the
    language it is already speaking.
    """
    text = (text or "").strip()
    if not text:
        return None

    by_script = script_language(text)
    if by_script:
        return by_script

    lowered = text.lower()
    if not _SWITCH_CUE_RE.search(lowered):
        return None
    for name, code in _LATIN_LANGUAGE_NAMES.items():
        if re.search(rf"\b{re.escape(name)}\b", lowered):
            return code
    return None
