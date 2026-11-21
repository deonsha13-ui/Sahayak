import json
import os
from datetime import date

import httpx
from dotenv import load_dotenv

load_dotenv()

EMPTY_RECORD = {
    "beneficiary_id": None,
    "visit_type": None,
    "weight_kg": None,
    "vaccinations_due": [],
    "next_visit_date": None,
    "danger_signs": [],
}

SYSTEM_PROMPT = """You are SAHAYAK, a warm, natural, human-like AI field assistant for ASHA community health workers in India.
You speak like a helpful human colleague on a voice call, NOT like a recorded automated form reader.
Converse in the exact language the worker speaks (Hindi, Hinglish, English, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi).

Extract clinical visit fields from the conversation:
- beneficiary_id: Beneficiary ID (e.g. "RCH-2026-000101", "1234") OR beneficiary name (e.g. "Sunita Devi", "Meena Kumari", "Priya") if spoken, else null
- visit_type: one of "ANC", "PNC", "newborn", "immunisation", or null
- weight_kg: number (convert spoken numbers like "do point aath" to 2.8, "pachpan" to 55), or null
- vaccinations_due: list of short vaccine names (e.g. ["TT", "BCG", "Pentavalent"]), or []
- next_visit_date: ISO date YYYY-MM-DD if mentioned, else null. Today's date is {today}.
- danger_signs: list of danger signs in English (e.g. "bleeding", "newborn fever"), else []

Rules:
- If a person's name or mother/child name is spoken, extract it into beneficiary_id.
- If the utterance is a correction ("no, weight is 2.8"), update only that field.
- In "reply", write a warm, concise (1-2 short sentences), natural human spoken response in her language:
  * Acknowledge what was just shared warmly.
  * If a name or ID was given, acknowledge it (e.g., "Got it, Sunita Devi.").
  * Naturally ask for the next missing detail (visit type, weight, vaccines, or next visit).
  * If all details are present, read them back concisely and ask to confirm save.
  * Strict clinical boundary: Never prescribe medications or diagnose diseases.

Return JSON only:
{
  "beneficiary_id": ...,
  "visit_type": ...,
  "weight_kg": ...,
  "vaccinations_due": [...],
  "next_visit_date": ...,
  "danger_signs": [...],
  "reply": "..."
}"""


async def _extract_groq(groq_key: str, system_prompt: str, user_content: str) -> dict:
    model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=body, headers=headers)
        if r.status_code != 200:
            print("GROQ ERROR:", r.status_code, r.text)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
    return json.loads(text)


async def _extract_gemini(api_key: str, system_prompt: str, user_content: str) -> dict:
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
    prompt = f"{system_prompt}\n\n{user_content}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }
    headers = {"x-goog-api-key": api_key}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, json=body, headers=headers)
        if r.status_code != 200:
            print("GEMINI ERROR:", r.status_code, r.text)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


async def extract(utterance: str, current: dict | None = None) -> dict:
    current = current or dict(EMPTY_RECORD)
    today = date.today().isoformat()
    system_prompt = SYSTEM_PROMPT.replace("{today}", today)
    user_content = f"CURRENT record:\n{json.dumps(current)}\n\nNEW utterance:\n{utterance}"

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()

    if groq_key and (provider == "groq" or not os.getenv("LLM_API_KEY")):
        return await _extract_groq(groq_key, system_prompt, user_content)

    gemini_key = os.getenv("LLM_API_KEY", "").strip()
    if gemini_key and provider != "groq":
        return await _extract_gemini(gemini_key, system_prompt, user_content)

    if groq_key:
        return await _extract_groq(groq_key, system_prompt, user_content)

    raise RuntimeError("No LLM key configured. Set GROQ_API_KEY or LLM_API_KEY in .env.")
