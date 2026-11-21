"""Comprehensive unit and integration tests for SAHAYAK.

Run from the project root:
    venv\\Scripts\\python.exe tests/test_all.py

No network calls are made: the Gnani key is blanked so the TTS client fails
fast, and the extractor is stubbed with scripted Gemini responses.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- isolate state before importing the app ------------------------------- #
TMP = Path(tempfile.mkdtemp(prefix="sahayak-test-"))
os.environ["SAHAYAK_DB"] = str(TMP / "test.db")
os.environ["SAHAYAK_KEY_FILE"] = str(TMP / "test.key")
os.environ["SAHAYAK_PRECACHE"] = "0"
os.environ.pop("SAHAYAK_ENCRYPTION_KEY", None)
# Blank key => STT/TTS raise immediately instead of reaching the network.
os.environ["GNANI_API_KEY"] = ""
os.environ["LLM_API_KEY"] = ""

from app import dialogue, i18n, storage, validation  # noqa: E402
from app.danger_signs import check_danger_signs  # noqa: E402

PASSED = 0
FAILED: list[str] = []


def check(name: str, condition, detail: str = "") -> None:
    global PASSED
    if condition:
        PASSED += 1
    else:
        FAILED.append(f"{name}{(' :: ' + detail) if detail else ''}")
        print(f"  FAIL  {name} {detail}")


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- #
section("validation: clinical envelopes")
# --------------------------------------------------------------------------- #
today = date.today()

check("visit type canonical", validation.normalize_visit_type("ANC visit") == "ANC")
check("visit type alias", validation.normalize_visit_type("postnatal checkup") == "PNC")
check("visit type vaccine", validation.normalize_visit_type("Tika") == "immunisation")
check("visit type unknown", validation.normalize_visit_type("hello") is None)

check("weight spoken decimal", validation.coerce_weight("do point aath") == 2.8)
check("weight with unit", validation.coerce_weight("52 kilo") == 52.0)
check("weight numeric", validation.coerce_weight(47.5) == 47.5)
check("newborn 52kg rejected", validation.check_weight(52, "newborn") is None)
check("newborn 2.8kg accepted", validation.check_weight(2.8, "newborn") == 2.8)
check("ANC 52kg accepted", validation.check_weight(52, "ANC") == 52.0)
check("ANC 2.8kg rejected", validation.check_weight(2.8, "ANC") is None)
check("weight 900kg rejected", validation.check_weight(900, "ANC") is None)

check("relative date kal", validation.parse_date("kal", today=today) ==
      (today + timedelta(days=1)).isoformat())
check("relative week", validation.parse_date("agle hafte", today=today) ==
      (today + timedelta(days=7)).isoformat())
check("numeric date", validation.parse_date("05/12/2026", today=today) == "2026-12-05")
check("past date rejected", validation.check_next_visit_date(
    (today - timedelta(days=1)).isoformat(), today=today) is None)
check("today rejected", validation.check_next_visit_date(today.isoformat(), today=today) is None)
check("future date accepted", validation.check_next_visit_date(
    (today + timedelta(days=3)).isoformat(), today=today) ==
    (today + timedelta(days=3)).isoformat())

check("vaccines canonicalised",
      validation.normalize_vaccinations("TT, BCG and none") == ["TT", "BCG"])
check("vaccine alias", validation.normalize_vaccinations(["TT injection"]) == ["TT"])
check("vaccine empty", validation.normalize_vaccinations(None) == [])

check("beneficiary id accepted",
      validation.normalize_beneficiary_id("RCH 2026 000101") == "RCH2026000101")
check("beneficiary id rejected", validation.normalize_beneficiary_id("!!") is None)

cleaned, problems = validation.validate_record(
    {"beneficiary_id": "RCH-2026-000101", "visit_type": "newborn",
     "weight_kg": 52, "vaccinations_due": ["BCG"],
     "next_visit_date": (today - timedelta(days=2)).isoformat()}
)
check("invalid weight cleared", cleaned["weight_kg"] is None)
check("weight problem raised", problems.get("weight_kg", {}).get("code") == "fix_weight")
check("past date problem raised", problems.get("next_visit_date", {}).get("code") == "fix_date")
check("valid visit type kept", cleaned["visit_type"] == "newborn")

# --------------------------------------------------------------------------- #
section("danger signs: deterministic rules")
# --------------------------------------------------------------------------- #
danger_cases = [
    ("Sita ko bleeding ho rahi hai", "ANC", True),
    ("Sita ko bleeding nahi hai, weight 52 kilo", "ANC", False),
    ("bleeding hai, fever nahi hai", "ANC", True),
    ("no bleeding today", "ANC", False),
    ("bacche ko tez bukhar hai", "newborn", True),
    ("bacche ko bukhar nahi hai", "newborn", False),
    ("mujhe bukhar hai", "ANC", False),
    ("us ko daura pada", None, True),
    ("ब्लीडिंग हो रही है", "ANC", True),
    ("खून नहीं आ रहा", "ANC", False),
    ("newborn has fever", "newborn", True),
]
for text, visit_type, expected in danger_cases:
    hits = check_danger_signs(text, visit_type)
    check(f"danger '{text[:26]}'", bool(hits) == expected, f"got {[h['id'] for h in hits]}")

check("newborn fever ignored for ANC",
      not check_danger_signs("fever", "ANC"))
check("pregnancy bleeding ignored for newborn",
      not check_danger_signs("bleeding", "newborn"))

# --------------------------------------------------------------------------- #
section("i18n: eight languages fully covered")
# --------------------------------------------------------------------------- #
english_keys = set(i18n.STRINGS["en"].keys())
check("english key set is complete", len(english_keys) >= 32, str(len(english_keys)))
for code in i18n.SUPPORTED:
    table = i18n.STRINGS.get(code, {})
    missing = english_keys - set(table.keys())
    check(f"{code} has every key", not missing, f"missing {sorted(missing)[:5]}")
    if code != "en":
        check(f"{code} greeting localised",
              bool(table.get("greeting"))
              and table.get("greeting") != i18n.STRINGS["en"]["greeting"])
    check(f"{code} locale code", i18n.locale_for(code).endswith("-IN"))
    check(f"{code} fixed phrases", len(i18n.fixed_phrases(code)) == len(i18n.FIXED_KEYS))

check("normalize hi-IN", i18n.normalize_lang("hi-IN") == "hi")
check("normalize code-mixed", i18n.normalize_lang("hi-IN,en-IN") == "hi")
check("normalize unknown", i18n.normalize_lang("xx") == "en")
check("stt header single locale", i18n.stt_language_header("hi") == "hi-IN")
check("stt header english", i18n.stt_language_header("en") == "en-IN")
check("stt header auto", i18n.stt_multilingual_header() == "indic-auto")
check("template interpolation", "52" in i18n.t("hi", "fix_weight", value=52, visit="नवजात"))
check("danger label localised", i18n.danger_label("ta", "bleeding_pregnancy", "x") != "x")

# --------------------------------------------------------------------------- #
section("storage: SQLite + Fernet encryption at rest")
# --------------------------------------------------------------------------- #
storage.init_db()
seeded = storage.seed_beneficiaries()
check("synthetic beneficiaries seeded", seeded == 6, f"seeded {seeded}")
check("seed is idempotent", storage.seed_beneficiaries() == 0)
check("beneficiary registry", len(storage.list_beneficiaries()) == 6)

visit_record = {
    "beneficiary_id": "RCH-2026-000101",
    "visit_type": "ANC",
    "weight_kg": 52.0,
    "vaccinations_due": ["TT"],
    "next_visit_date": (today + timedelta(days=7)).isoformat(),
    "danger_signs": [],
    "flagged": False,
}
saved = storage.save_visit(visit_record, transcript="secret transcript text",
                           language="hi", session_id="sess-1")
check("visit persisted", saved["visit_id"] and len(saved["follow_ups"]) >= 2,
      str(saved.get("follow_ups")))

fetched = storage.get_visit(saved["visit_id"])
check("visit round-trip", fetched and fetched["record"]["beneficiary_id"] == "RCH-2026-000101")
check("transcript round-trip", fetched and fetched["transcript"] == "secret transcript text")
check("field history recorded", fetched and len(fetched["field_history"]) >= 5)
check("follow-up kinds", {f["kind"] for f in fetched["follow_ups"]} >= {"next_visit", "immunisation"})

with storage.connect() as conn:
    raw_payload = conn.execute("SELECT payload_enc FROM visits WHERE id = ?",
                               (saved["visit_id"],)).fetchone()[0]
    raw_transcript = conn.execute("SELECT transcript_enc FROM visits WHERE id = ?",
                                  (saved["visit_id"],)).fetchone()[0]
check("payload encrypted", b"next_visit_date" not in raw_payload)
check("transcript encrypted", b"secret" not in raw_transcript)
check("decrypt rejects garbage", storage.decrypt(b"not-a-token") is None)

flagged_record = dict(visit_record, beneficiary_id="RCH-2026-000102",
                      danger_signs=["Bleeding in pregnancy"], flagged=True)
flagged_saved = storage.save_visit(flagged_record, transcript="bleeding")
check("flagged visit stored", flagged_saved["flagged"] is True)
check("referral follow-up created",
      any(f["kind"] == "phc_referral" for f in flagged_saved["follow_ups"]))

dashboard = storage.dashboard()
check("dashboard totals", dashboard["total_visits"] >= 2, str(dashboard))
check("dashboard flagged", dashboard["flagged_visits"] >= 1)
check("dashboard by type", dashboard["visits_by_type"].get("ANC", 0) >= 2)

pending = storage.list_follow_ups(status="pending")
check("follow-ups listed", len(pending) >= 3, str(len(pending)))
done = storage.complete_follow_up(pending[0]["id"])
check("follow-up completion", done and done["status"] == "done")

check("beneficiary upsert", storage.upsert_beneficiary("RCH-2026-000199", "Test", "Village")["name"] == "Test")
check("beneficiary visits", len(storage.list_visits(beneficiary_id="RCH-2026-000101")) >= 1)

# --------------------------------------------------------------------------- #
section("dialogue: full visit, validation re-ask, danger interruption")
# --------------------------------------------------------------------------- #
SCRIPT: list[dict] = []


async def fake_extract(utterance, current=None):
    return SCRIPT.pop(0) if SCRIPT else {}


dialogue.extract = fake_extract


async def full_visit_english():
    SCRIPT[:] = [
        {"beneficiary_id": "RCH-2026-000101", "visit_type": "ANC", "weight_kg": 52},
        {"vaccinations_due": ["TT"]},
        {"next_visit_date": (date.today() + timedelta(days=7)).isoformat()},
    ]
    session = dialogue.Session("en")
    first = await session.handle("Sita ka ID RCH-2026-000101, ANC visit, weight 52 kilo")
    second = await session.handle("TT injection due hai")
    third = await session.handle("agle hafte aana hai")
    fourth = await session.handle("yes")
    return session, first, second, third, fourth


session_en, r1, r2, r3, r4 = run(full_visit_english())
check("asks vaccinations", "vaccination" in r1.lower(), r1)
check("asks next visit", "next visit" in r2.lower(), r2)
check("reaches readback", session_en.state in ("readback", "saved"), session_en.state)
check("readback includes weight", "52.0" in r3 or "52" in r3, r3)
check("readback asks confirmation", "correct" in r3.lower(), r3)
check("saves on confirmation", session_en.state == "saved", session_en.state)
check("save summary lists follow-ups", "Follow-ups" in r4, r4)
check("payload flagged false", session_en.to_visit_payload()["flagged"] is False)
check("transcript captured", len(session_en.transcript) == 4)


async def newborn_weight_rejected():
    SCRIPT[:] = [
        {"beneficiary_id": "RCH-2026-000103"},
        {"visit_type": "newborn", "weight_kg": 52},
    ]
    session = dialogue.Session("en")
    await session.handle("baby ka ID RCH-2026-000103")
    reply = await session.handle("newborn, weight 52 kilo")
    return session, reply


session_bw, reply_bw = run(newborn_weight_rejected())
check("impossible newborn weight rejected", "not possible" in reply_bw.lower(), reply_bw)
check("rejected weight cleared", session_bw.record["weight_kg"] is None)


async def danger_interrupt_hindi():
    SCRIPT[:] = [
        {"beneficiary_id": "RCH-2026-000102", "visit_type": "ANC", "weight_kg": 50},
        {"vaccinations_due": []},
        {"next_visit_date": (date.today() + timedelta(days=5)).isoformat()},
    ]
    session = dialogue.Session("hi")
    first = await session.handle("RCH-2026-000102, ANC, वज़न 50 किलो, खून आ रहा है")
    await session.handle("कोई टीका नहीं")
    await session.handle("पांच दिन बाद")
    last = await session.handle("हाँ")
    return session, first, last


session_hi, hi_first, hi_last = run(danger_interrupt_hindi())
check("hindi greeting localised", "सहायक" in dialogue.Session("hi").greeting())
check("danger referral localised", "खतरे" in hi_first, hi_first)
check("danger flag set", "bleeding_pregnancy" in session_hi.flags, str(session_hi.flags))
check("hindi readback/save completes", session_hi.state == "saved", session_hi.state)
check("hindi save message", "सेव" in hi_last, hi_last)
check("flagged payload", session_hi.to_visit_payload()["flagged"] is True)

negative_session = dialogue.Session("en")
negative_session.state = "readback"
negative_reply = run(negative_session.handle("no"))
check("plain no asks what to change", "change" in negative_reply.lower(), negative_reply)
check("plain no reopens collection", negative_session.state == "collecting")

saved_session = dialogue.Session("en")
saved_session.state = "saved"
check("already saved guard",
      "saved" in run(saved_session.handle("hello")).lower())

# --------------------------------------------------------------------------- #
section("assistant voice: auto language and acknowledgement")
# --------------------------------------------------------------------------- #
from app import lang_detect  # noqa: E402

check("detects hindi script", lang_detect.detect_language("मेरा नाम सीता है") == "hi")
check("detects marathi script", lang_detect.detect_language("हे बरोबर आहे का") == "mr")
check("detects tamil script", lang_detect.detect_language("எடை ஐம்பத்தி இரண்டு கிலோ") == "ta")
check("detects telugu script", lang_detect.detect_language("బరువు యాభై రెండు కిలోలు") == "te")
check("detects kannada script", lang_detect.detect_language("ತೂಕ ಐವತ್ತೆರಡು ಕಿಲೋ") == "kn")
check("detects malayalam script", lang_detect.detect_language("ഭാരം അമ്പത്തിരണ്ട് കിലോ") == "ml")
check("detects bengali script", lang_detect.detect_language("ওজন বায়ান্ন কেজি") == "bn")
check("latin english is not a switch", lang_detect.detect_language("weight is 52 kilos") is None)
check("explicit switch request", lang_detect.detect_language("please speak in tamil") == "ta")


async def assistant_greeting_and_ack():
    SCRIPT[:] = [{"beneficiary_id": "RCH-2026-000104", "visit_type": "ANC", "weight_kg": 55}]
    session = dialogue.Session("en")
    reply = await session.handle("RCH-2026-000104, ANC, 55 kilo")
    return session, reply


auto_session, ack_reply = run(assistant_greeting_and_ack())
check("assistant greets like an assistant",
      "welcome" in dialogue.Session("en").greeting().lower())
check("acknowledges heard fields", ack_reply.lower().startswith("got it"), ack_reply)
check("acknowledgement names the weight", "55" in ack_reply, ack_reply)
check("still asks the next field", "vaccination" in ack_reply.lower(), ack_reply)


async def auto_switch_on_speech():
    SCRIPT[:] = [{"beneficiary_id": "RCH-2026-000105", "visit_type": "PNC", "weight_kg": 48}]
    session = dialogue.Session("en")
    reply = await session.handle("मेरी आईडी RCH-2026-000105 है, पीएनसी, वज़न 48 किलो")
    return session, reply


switched_session, switched_reply = run(auto_switch_on_speech())
check("speech drives the language", switched_session.language == "hi",
      switched_session.language)
check("switch is announced", "हिन्दी" in switched_reply, switched_reply)
check("switch reported to transport", switched_session.language_changed == "hi")

readback_ask = dialogue.Session("en")
readback_ask.record.update({
    "beneficiary_id": "RCH-2026-000101",
    "visit_type": "ANC",
    "weight_kg": 52.0,
    "vaccinations_due": ["TT"],
    "next_visit_date": "2099-01-01",
})
readback_text = readback_ask._readback()
check("readback asks to save", "save" in readback_text.lower(), readback_text)

partial = dialogue.Session("en")
check("explicit save refused while incomplete", partial.save_now() is None)

# --------------------------------------------------------------------------- #
section("REST API and WebSocket")
# --------------------------------------------------------------------------- #
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

with TestClient(app) as client:
    health = client.get("/health")
    check("health ok", health.status_code == 200 and health.json()["ok"] is True)
    check("health lists 8 languages", len(health.json()["languages"]) == 8)
    check("health cache stats", "phrases" in health.json()["tts_cache"])
    check("health key fingerprint", len(health.json()["encryption_key"]) == 12)

    check("root redirects", client.get("/", follow_redirects=False).status_code in (302, 307))
    talk = client.get("/talk")
    check("talk page served", talk.status_code == 200 and "SAHAYAK" in talk.text)
    check("talk page has ptt", "id=\"ptt\"" in talk.text)

    langs = client.get("/api/languages").json()
    check("languages endpoint", len(langs["supported"]) == 8)

    bens = client.get("/api/beneficiaries").json()["items"]
    check("beneficiaries endpoint", len(bens) >= 6, str(len(bens)))
    created = client.post("/api/beneficiaries",
                          json={"beneficiary_id": "RCH-2026-000777", "name": "API Test"})
    check("create beneficiary", created.status_code == 201)

    bad = client.post("/api/visits", json={
        "beneficiary_id": "RCH-2026-000777", "visit_type": "newborn",
        "weight_kg": 52, "next_visit_date": (date.today() + timedelta(days=4)).isoformat(),
    })
    check("API rejects impossible weight", bad.status_code == 422, str(bad.status_code))

    good = client.post("/api/visits", json={
        "beneficiary_id": "RCH-2026-000777", "visit_type": "ANC",
        "weight_kg": 51.5, "vaccinations_due": ["TT"],
        "next_visit_date": (date.today() + timedelta(days=4)).isoformat(),
    })
    check("API creates visit", good.status_code == 201, good.text[:120])
    visit_id = good.json()["visit_id"]
    check("visit fetched by id", client.get(f"/api/visits/{visit_id}").status_code == 200)
    check("missing visit is 404", client.get("/api/visits/nope").status_code == 404)
    check("visits list", len(client.get("/api/visits").json()["items"]) >= 3)
    check("flagged filter", isinstance(client.get("/api/visits?flagged=true").json()["items"], list))
    check("follow-ups endpoint", "items" in client.get("/api/follow-ups").json())
    check("danger signs endpoint", len(client.get("/api/danger-signs").json()["items"]) >= 2)
    check("dashboard endpoint", client.get("/api/dashboard").json()["total_visits"] >= 3)

    with client.websocket_connect("/ws?lang=hi") as ws:
        types = []
        for _ in range(5):
            types.append(ws.receive_json()["type"])
        check("ws session_ready", "session_ready" in types, str(types))
        check("ws greeting", "agent_text" in types, str(types))
        ws.send_json({"type": "ping"})
        while True:
            msg = ws.receive_json()
            if msg["type"] == "pong":
                break
        check("ws ping/pong", True)
        ws.send_json({"type": "set_language", "language": "ta"})
        while True:
            msg = ws.receive_json()
            if msg["type"] == "language_set":
                check("ws language switch", msg["language"] == "ta")
                break

# --------------------------------------------------------------------------- #
section("DPDP purge utility")
# --------------------------------------------------------------------------- #
before = storage.dashboard()["total_visits"]
check("data present before purge", before > 0, str(before))
counts = storage.purge_all()
check("purge reports visit rows", counts["visits"] >= 1, str(counts))
after = storage.dashboard()
check("visits purged", after["total_visits"] == 0, str(after["total_visits"]))
check("beneficiaries purged", after["beneficiaries"] == 0, str(after["beneficiaries"]))
check("follow-ups purged", storage.list_follow_ups(status=None) == [])
check("key file exists", (TMP / "test.key").exists())

# --------------------------------------------------------------------------- #
print("\n" + "=" * 60)
if FAILED:
    print(f"FAILED {len(FAILED)} / {len(FAILED) + PASSED} checks")
    for item in FAILED:
        print("  -", item)
    print("=" * 60)
    sys.exit(1)

print(f"PASSED {PASSED} checks")
print("=" * 60)
