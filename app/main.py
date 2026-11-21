"""SAHAYAK FastAPI backend.

Serves the voice-first field register: the browser client at /talk, a
streaming voice WebSocket at /ws (Gnani Prisma STT in, Gnani Timbre TTS out)
and the supervisor REST API under /api.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field

from app import i18n, storage, tts_cache, validation
from app.danger_signs import DANGER_SIGNS
from app.dialogue import Session
from app.gnani_stt import STTStream

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
TALK_HTML = ROOT / "talk.html"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    storage.init_db()
    seeded = storage.seed_beneficiaries()
    if seeded:
        print(f"[db] Seeded {seeded} synthetic beneficiaries")
    demo_seeded = storage.seed_demo_beneficiaries()
    if demo_seeded:
        print(f"[db] Seeded {demo_seeded} demo beneficiaries")
    await tts_cache.prewarm()
    yield


app = FastAPI(title="SAHAYAK", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# models
# --------------------------------------------------------------------------- #
class BeneficiaryIn(BaseModel):
    beneficiary_id: str = Field(min_length=1, max_length=64)
    name: str | None = None
    village: str | None = None


class VisitIn(BaseModel):
    beneficiary_id: str
    visit_type: str
    weight_kg: float
    vaccinations_due: list[str] = []
    next_visit_date: str
    danger_signs: list[str] = []


class FollowUpStatusIn(BaseModel):
    status: str = "done"


# --------------------------------------------------------------------------- #
# pages and health
# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    return {
        "ok": True,
        "gnani_key_loaded": bool(os.getenv("GNANI_API_KEY")),
        "llm_key_loaded": bool(os.getenv("LLM_API_KEY")),
        "model": os.getenv("GEMINI_MODEL", ""),
        "languages": list(i18n.SUPPORTED),
        "tts_cache": tts_cache.stats(),
        "encryption_key": storage.key_fingerprint(),
    }


FRONTEND_DIST = ROOT / "frontend" / ".output" / "public"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = ROOT / "frontend" / "dist"


@app.get("/")
def index():
    if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    return RedirectResponse("/talk")


@app.get("/talk")
def talk():
    if not TALK_HTML.exists():
        raise HTTPException(status_code=500, detail="talk.html is missing")
    return FileResponse(TALK_HTML, media_type="text/html")


@app.get("/api/languages")
def languages():
    return {
        "supported": [
            {"code": code, "name": i18n.LANGUAGE_NAMES[code], "locale": i18n.locale_for(code)}
            for code in i18n.SUPPORTED
        ]
    }


# --------------------------------------------------------------------------- #
# beneficiaries
# --------------------------------------------------------------------------- #
@app.get("/api/beneficiaries")
def api_beneficiaries(limit: int = Query(100, ge=1, le=500)):
    return {"items": storage.list_beneficiaries(limit=limit)}


@app.post("/api/beneficiaries", status_code=201)
def api_create_beneficiary(payload: BeneficiaryIn):
    return storage.upsert_beneficiary(payload.beneficiary_id, payload.name, payload.village)


@app.get("/api/beneficiaries/{beneficiary_id}")
def api_beneficiary(beneficiary_id: str):
    found = storage.get_beneficiary(beneficiary_id)
    if not found:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    found["visits"] = storage.list_visits(limit=50, beneficiary_id=beneficiary_id)
    return found


# --------------------------------------------------------------------------- #
# visits
# --------------------------------------------------------------------------- #
@app.get("/api/visits")
def api_visits(
    limit: int = Query(50, ge=1, le=500),
    beneficiary_id: str | None = None,
    flagged: bool = False,
):
    return {"items": storage.list_visits(limit, beneficiary_id, flagged)}


@app.get("/api/visits/{visit_id}")
def api_visit(visit_id: str):
    found = storage.get_visit(visit_id)
    if not found:
        raise HTTPException(status_code=404, detail="Visit not found")
    return found


@app.post("/api/visits", status_code=201)
def api_create_visit(payload: VisitIn):
    raw = payload.model_dump()
    cleaned, problems = validation.validate_record(raw)
    if problems:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Clinical validation failed",
                "problems": {field: args.get("code") for field, args in problems.items()},
            },
        )
    cleaned["danger_signs"] = raw.get("danger_signs") or []
    cleaned["flagged"] = bool(cleaned["danger_signs"])
    return storage.save_visit(cleaned, transcript=None, language="en")


# --------------------------------------------------------------------------- #
# follow-ups and dashboard
# --------------------------------------------------------------------------- #
@app.get("/api/follow-ups")
@app.get("/api/followups")
def api_follow_ups(
    status: str | None = Query("pending"),
    limit: int = Query(100, ge=1, le=500),
):
    return {"items": storage.list_follow_ups(status=status, limit=limit)}


@app.post("/api/follow-ups/{follow_up_id}")
@app.post("/api/followups/{follow_up_id}")
@app.patch("/api/follow-ups/{follow_up_id}")
@app.patch("/api/followups/{follow_up_id}")
def api_complete_follow_up(follow_up_id: str, payload: FollowUpStatusIn):
    status = "completed" if payload.status.lower() in ("completed", "done") else payload.status
    updated = storage.complete_follow_up(follow_up_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return updated


@app.post("/api/visits/{visit_id}/confirm")
def api_confirm_visit(visit_id: str):
    return {"ok": True, "visit_id": visit_id, "status": "confirmed"}


@app.get("/api/dashboard")
def api_dashboard():
    return storage.dashboard()


@app.get("/api/danger-signs")
def api_danger_signs():
    return {
        "items": [
            {
                "id": sign["id"],
                "label": sign["label"],
                "context": sign["context"],
                "phrases": sign["phrases"],
            }
            for sign in DANGER_SIGNS
        ]
    }


# --------------------------------------------------------------------------- #
# websocket
# --------------------------------------------------------------------------- #
async def send(ws: WebSocket, **data):
    await ws.send_text(json.dumps(data, ensure_ascii=False))


async def speak(ws: WebSocket, session: Session, text: str):
    """Stream 24 kHz PCM16 for a reply, from cache when available."""
    if not text.strip():
        return
    await send(ws, type="audio_start", format="pcm16", sample_rate=24000)
    await send(ws, type="agent_speaking", active=True)
    try:
        async for chunk in tts_cache.speak(text, session.language):
            b64_data = base64.b64encode(chunk).decode("ascii")
            await send(
                ws,
                type="audio",
                format="pcm16",
                sample_rate=24000,
                data=b64_data,
            )
            await send(
                ws,
                type="agent_audio_chunk",
                format="pcm16",
                sample_rate=24000,
                data=b64_data,
            )
    except Exception as exc:  # noqa: BLE001 - the text reply is already delivered
        print("tts error:", exc)
        await send(ws, type="tts_error", message=str(exc))
    finally:
        await send(ws, type="audio_end")
        await send(ws, type="agent_speaking", active=False)


async def handle_text(ws: WebSocket, session: Session, text: str, session_id: str | None):
    state_before = session.state
    record_before = dict(session.record)
    flags_before = set(session.flags)
    saved_before = len(session.saved_records)

    await send(ws, type="transcript_final", text=text, entities=[])
    reply = await session.handle(text)

    if session.language_changed:
        await send(
            ws,
            type="language_set",
            language=session.language_changed,
            name=i18n.LANGUAGE_NAMES[session.language_changed],
            auto=True,
        )

    for field, value in session.record.items():
        if field != "danger_signs" and value != record_before.get(field):
            await send(ws, type="field_update", field=field, value=value, status="heard")

    for sign_id, label in session.flags.items():
        if sign_id not in flags_before:
            await send(ws, type="danger_alert", sign=sign_id, quote=text, message=label)

    if session.state == "readback" and state_before != "readback":
        await send(ws, type="readback_start", record=session.record)

    await send(ws, type="agent_text", text=reply)
    await speak(ws, session, reply)

    if len(session.saved_records) > saved_before:
        await announce_saved(ws, session, session_id)


async def announce_saved(ws: WebSocket, session: Session, session_id: str | None):
    """Persist the confirmed record and push the refreshed dashboard totals."""
    saved = await asyncio.to_thread(
        storage.save_visit,
        session.saved_records[-1],
        session.transcript_text(),
        session.language,
        session_id,
    )
    dashboard = await asyncio.to_thread(storage.dashboard)
    await send(
        ws,
        type="record_saved",
        record=saved,
        follow_ups=saved["follow_ups"],
        dashboard=dashboard,
    )


async def stt_reader(ws: WebSocket, session: Session, stt: STTStream, session_id: str | None):
    try:
        async for event in stt.events():
            kind = event.get("type")
            if kind == "transcript":
                text = (event.get("text") or event.get("transcript") or "").strip()
                if not text:
                    continue
                final = event.get("is_final", event.get("final", True))
                if final is False:
                    await send(ws, type="transcript_partial", text=text)
                    continue
                await handle_text(ws, session, text, session_id)
            elif kind == "error":
                await send(ws, type="stt_error", message=event.get("message", "STT error"))
            elif kind == "speech_start":
                await send(ws, type="speech_start")
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface it, keep the socket alive
        print("stt reader error:", exc)
        try:
            await send(ws, type="stt_error", message=str(exc))
        except Exception:  # noqa: BLE001
            pass


async def close_stt(stt, task):
    if task:
        task.cancel()
        try:
            await task
        except BaseException:  # noqa: BLE001 - cancellation and transport errors
            pass
    if stt:
        try:
            await stt.__aexit__(None, None, None)
        except Exception:  # noqa: BLE001
            pass


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    lang = i18n.normalize_lang(ws.query_params.get("lang") or "en")
    auto_language = os.getenv("SAHAYAK_AUTO_LANGUAGE", "1").strip().lower() not in (
        "0", "false", "off",
    )
    session = Session(lang, auto_language=auto_language)
    session_id = storage.start_session(session.language)

    stt = None
    reader = None
    speak_task: asyncio.Task | None = None
    is_ptt = False
    pending_transcripts: list[str] = []

    async def speak_guarded(text: str):
        nonlocal speak_task
        if speak_task and not speak_task.done():
            speak_task.cancel()
            try:
                await speak_task
            except (asyncio.CancelledError, BaseException):
                pass
        speak_task = asyncio.create_task(speak(ws, session, text))

    async def handle_guarded(text: str):
        state_before = session.state
        record_before = dict(session.record)
        flags_before = set(session.flags)
        saved_before = len(session.saved_records)

        await send(ws, type="transcript_final", text=text, entities=[])
        reply = await session.handle(text)

        if session.language_changed:
            await send(
                ws,
                type="language_set",
                language=session.language_changed,
                name=i18n.LANGUAGE_NAMES[session.language_changed],
                auto=True,
            )

        for field, value in session.record.items():
            if field != "danger_signs" and value != record_before.get(field):
                await send(ws, type="field_update", field=field, value=value, status="heard")

        for sign_id, label in session.flags.items():
            if sign_id not in flags_before:
                await send(ws, type="danger_alert", sign=sign_id, quote=text, message=label)

        if session.state == "readback" and state_before != "readback":
            await send(ws, type="readback_start", record=session.record)

        await send(ws, type="agent_text", text=reply)
        await speak_guarded(reply)

        if len(session.saved_records) > saved_before:
            await announce_saved(ws, session, session_id)

    async def stt_reader_loop(stt_instance: STTStream):
        nonlocal pending_transcripts
        try:
            async for event in stt_instance.events():
                kind = event.get("type")
                if kind == "transcript":
                    text = (event.get("text") or event.get("transcript") or "").strip()
                    if not text:
                        continue
                    final = event.get("is_final", event.get("final", True))
                    if is_ptt:
                        # While PTT is held, only stream partial updates to UI and buffer text
                        pending_transcripts.append(text)
                        await send(ws, type="transcript_partial", text=text)
                    else:
                        if final is False:
                            await send(ws, type="transcript_partial", text=text)
                            continue
                        await handle_guarded(text)
                elif kind == "error":
                    await send(ws, type="stt_error", message=event.get("message", "STT error"))
                elif kind == "speech_start":
                    await send(ws, type="speech_start")
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            print("stt reader error:", exc)
            try:
                await send(ws, type="stt_error", message=str(exc))
            except Exception:
                pass

    greeting = session.greeting()
    await send(ws, type="session_ready", language=session.language,
               languages=list(i18n.SUPPORTED), disclosure_text=greeting,
               auto_language=session.auto_language)
    await send(ws, type="agent_text", text=greeting)
    await speak_guarded(greeting)

    try:
        while True:
            message = await ws.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                if stt is not None:
                    try:
                        await stt.send_pcm(message["bytes"])
                    except Exception as exc:  # noqa: BLE001
                        await send(ws, type="stt_error", message=str(exc))
                continue

            raw = message.get("text") or ""
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await send(ws, type="error", message="Invalid JSON")
                continue

            kind = payload.get("type")

            if kind == "text_input":
                await handle_guarded(payload.get("text", ""))

            elif kind == "ptt_start":
                is_ptt = True
                pending_transcripts.clear()
                # Cancel any ongoing speech immediately so voices never overlap
                if speak_task and not speak_task.done():
                    speak_task.cancel()
                await send(ws, type="flush_audio")
                await close_stt(stt, reader)
                stt, reader = None, None
                try:
                    header = (
                        i18n.stt_multilingual_header()
                        if session.auto_language
                        else i18n.stt_language_header(session.language)
                    )
                    stt = STTStream(language_code=header, min_silence_ms=800)
                    await stt.__aenter__()
                    reader = asyncio.create_task(stt_reader_loop(stt))
                    await send(ws, type="ptt_ready")
                except Exception as exc:  # noqa: BLE001
                    print("stt connect error:", exc)
                    await send(ws, type="stt_error", message=str(exc))
                    stt, reader = None, None

            elif kind == "ptt_end":
                is_ptt = False
                if stt is not None:
                    try:
                        await stt.commit()
                        await send(ws, type="processing")
                        # Allow Gnani commit frame to arrive and flush
                        await asyncio.sleep(0.4)
                        if pending_transcripts:
                            best_text = max(pending_transcripts, key=len).strip()
                            pending_transcripts.clear()
                            if best_text:
                                await handle_guarded(best_text)
                    except Exception as exc:  # noqa: BLE001
                        await send(ws, type="stt_error", message=str(exc))

            elif kind == "set_language":
                new_lang = session.set_language(payload.get("language"))
                if payload.get("manual"):
                    session.auto_language = False  # Lock to the user's explicit manual selection
                name = i18n.LANGUAGE_NAMES[new_lang]
                await send(ws, type="language_set", language=new_lang, name=name)
                ack = i18n.t(new_lang, "language_set", language=name)
                await send(ws, type="agent_text", text=ack)
                await speak_guarded(ack)

            elif kind == "confirm_save":
                reply = session.save_now()
                if reply is None:
                    reply = session.pending_prompt()
                    await send(ws, type="agent_text", text=reply)
                    await speak_guarded(reply)
                else:
                    await send(ws, type="agent_text", text=reply)
                    await speak_guarded(reply)
                    await announce_saved(ws, session, session_id)

            elif kind == "audio_chunk":
                raw_b64 = payload.get("data")
                if raw_b64 and stt is not None:
                    try:
                        pcm_bytes = base64.b64decode(raw_b64)
                        await stt.send_pcm(pcm_bytes)
                    except Exception as exc:  # noqa: BLE001
                        await send(ws, type="stt_error", message=str(exc))

            elif kind == "start_visit":
                v_type = payload.get("visit_type")
                if v_type:
                    norm_type = validation.normalize_visit_type(v_type)
                    if norm_type:
                        session.record["visit_type"] = norm_type
                b_id = payload.get("beneficiary_id")
                if b_id:
                    session.record["beneficiary_id"] = str(b_id).strip()
                if payload.get("language"):
                    session.set_language(payload.get("language"))
                await send(ws, type="session_started", language=session.language)
                if payload.get("speak"):
                    prompt = session.pending_prompt()
                    await send(ws, type="agent_text", text=prompt)
                    await speak_guarded(prompt)

            elif kind == "correct_field":
                f_name = payload.get("field")
                f_val = payload.get("value")
                rev_map = {
                    "beneficiary": "beneficiary_id",
                    "name": "beneficiary_id",
                    "type": "visit_type",
                    "weight": "weight_kg",
                    "vaccinations": "vaccinations_due",
                    "next": "next_visit_date",
                }
                canonical_field = rev_map.get(f_name, f_name)
                if canonical_field in session.record:
                    session.record[canonical_field] = f_val
                    await send(ws, type="field_updated", field=canonical_field, value=f_val)

            elif kind == "ping":
                await send(ws, type="pong")

    except WebSocketDisconnect:
        print("client disconnected")
    finally:
        if speak_task and not speak_task.done():
            speak_task.cancel()
        await close_stt(stt, reader)


# --------------------------------------------------------------------------- #
# Frontend SPA static serving
# --------------------------------------------------------------------------- #
if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles

    for sub in ("_build", "assets"):
        sub_dir = FRONTEND_DIST / sub
        if sub_dir.exists():
            app.mount(f"/{sub}", StaticFiles(directory=sub_dir), name=f"frontend_{sub}")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not found")
