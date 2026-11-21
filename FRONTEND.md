# Connecting your frontend to SAHAYAK

The backend is a single FastAPI process. It serves the reference voice client
at `/talk` and exposes everything your own frontend needs:

- **REST** for the dashboard, beneficiaries, visits, follow-ups and metadata.
- **WebSocket `/ws`** for the live voice conversation (speech in, speech out,
  live record updates, save).

CORS is open (`*`) so a frontend on another port can call it directly. For a
production deployment, narrow `allow_origins` in `app/main.py` to your origin.

```
Browser  ──PCM16 16 kHz──▶  /ws  ──▶  Gnani STT  ──▶  dialogue brain
   ▲                                                     │
   └──PCM16 24 kHz──────────────  Gnani TTS  ◀───────────┘
                                   │
                            SQLite (encrypted)
                                   │
                        GET /api/dashboard  ◀── your dashboard UI
```

Start it with:

```bash
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

Point your frontend's API base at `http://localhost:8000`.

---

## 1. REST endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Ready check, key/model status, 8 languages, TTS cache stats |
| GET | `/api/languages` | `{supported:[{code,name,locale}]}` |
| GET | `/api/beneficiaries?limit=100` | Registry |
| POST | `/api/beneficiaries` | `{beneficiary_id, name?, village?}` |
| GET | `/api/beneficiaries/{id}` | Beneficiary plus their recent visits |
| GET | `/api/visits?limit=50&beneficiary_id=&flagged=` | Saved visits |
| POST | `/api/visits` | Save a visit without voice. `422` with `problems` on invalid clinical values |
| GET | `/api/visits/{visit_id}` | One visit with field history and follow-ups |
| GET | `/api/follow-ups?status=pending` | `status=pending\|done\|all` |
| POST | `/api/follow-ups/{id}` | `{status:"done"}` |
| GET | `/api/dashboard` | Counters for the supervisor view |
| GET | `/api/danger-signs` | The red-flag list the rules use |

`GET /api/dashboard` returns:

```json
{
  "beneficiaries": 6,
  "total_visits": 12,
  "visits_today": 3,
  "flagged_visits": 1,
  "follow_ups_due": 2,
  "follow_ups_next_7_days": 5,
  "visits_by_type": {"ANC": 6, "newborn": 4, "PNC": 2}
}
```

A saved visit is immediately visible to every REST endpoint — no cache to
invalidate. After `record_saved` (below) just refetch `/api/dashboard` and
`/api/visits`, or use the `dashboard` object already included in the event.

---

## 2. WebSocket `/ws`

```
ws://localhost:8000/ws?lang=en
```

`lang` is the starting language (default `en`). After that the backend follows
the worker's speech and switches automatically among
`hi, ta, te, kn, ml, bn, mr, en`.

### Client → server

JSON text frames:

| `type` | Payload | Meaning |
|---|---|---|
| `ptt_start` | — | Mic pressed. Opens a Gnani STT stream |
| `ptt_end` | — | Mic released. Commits the utterance |
| `text_input` | `text` | Typed fallback, same pipeline as speech |
| `set_language` | `language` | Manual switch from a dropdown |
| `confirm_save` | — | Save button (same as saying yes) |
| `ping` | — | Keepalive |

Binary frames: raw **PCM16, mono, 16 kHz, little-endian** while
`ptt_start`…`ptt_end`. Send whatever buffer size your capture produces; the
server re-frames to the 1024 bytes Gnani requires.

```js
ws.send(pcm16.buffer);              // during push-to-talk
ws.send(JSON.stringify({ type: "ptt_end" }));
```

### Server → client

| `type` | Payload | Use |
|---|---|---|
| `session_ready` | `language, languages, disclosure_text, auto_language` | Initial state; do not render `disclosure_text` as well as the greeting `agent_text` or it appears twice |
| `agent_text` | `text` | Render the assistant turn |
| `transcript_partial` | `text` | Optional live caption |
| `transcript_final` | `text` | Render the worker's turn |
| `field_update` | `field, value, status` | Update a record chip. Fields: `beneficiary_id, visit_type, weight_kg, vaccinations_due, next_visit_date` |
| `danger_alert` | `sign, quote, message` | Show the red referral banner |
| `readback_start` | — | Show the confirm card |
| `record_saved` | `record, follow_ups, dashboard` | Success state; `dashboard` is the refreshed counters |
| `language_set` | `language, name, auto` | Sync your language selector; `auto:true` means detected from speech |
| `audio_start` | `format:"pcm16", sample_rate:24000` | Create/reset the playback queue |
| `audio` | `data` (base64 PCM16) | Append to the queue |
| `audio_end` | — | Flush |
| `processing` | — | STT is finishing the utterance |
| `speech_start` | — | Voice activity detected |
| `ptt_ready` | — | STT connected; start streaming |
| `stt_error`, `tts_error`, `error` | `message` | Surface, keep the socket open |
| `pong` | — | Reply to `ping` |

Audio playback: decode base64 to `Int16Array`, convert `/32768` to float, queue
into an `AudioBuffer` at 24 kHz, play sequentially. `talk.html` has a working
implementation (~40 lines) you can copy.

---

## 3. Minimal integration

```js
const ws = new WebSocket(`ws://localhost:8000/ws?lang=en`);
ws.binaryType = "arraybuffer";
let mic = null, proc = null;

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "ping" }));
};

ws.onmessage = (event) => {
  const m = JSON.parse(event.data);
  switch (m.type) {
    case "agent_text":        chat.push({ role: "assistant", text: m.text }); break;
    case "transcript_final":  chat.push({ role: "worker", text: m.text }); break;
    case "field_update":      record[m.field] = m.value; break;
    case "danger_alert":      banner.show(m.message); break;
    case "readback_start":    saveCard.show(); break;
    case "record_saved":
      saveCard.hide();
      refreshDashboard(m.dashboard);   // or refetch /api/dashboard
      break;
    case "language_set":
      languageSelect.value = m.language;
      break;
    case "audio":
      enqueuePcm16(atobToInt16(m.data), m.sample_rate || 24000);
      break;
  }
};

// Push to talk
async function startTalking() {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
  });
  const ctx = new AudioContext();
  const src = ctx.createMediaStreamSource(stream);
  proc = ctx.createScriptProcessor(4096, 1, 1);
  proc.onaudioprocess = (e) => {
    const float = e.inputBuffer.getChannelData(0);
    const pcm = downsampleTo16kInt16(float, ctx.sampleRate);
    ws.send(pcm.buffer);
  };
  src.connect(proc);
  proc.connect(ctx.destination);   // keep alive with a muted gain node
  ws.send(JSON.stringify({ type: "ptt_start" }));
}

function stopTalking() {
  ws.send(JSON.stringify({ type: "ptt_end" }));
  proc?.disconnect();
  proc = null;
}
```

If you cannot capture PCM (some browsers/iframes), use `text_input` — the
whole conversation, validation, danger signs, save and dashboard still work.

---

## 4. Language handling

1. Session starts in the `lang` you pass (default English) and greets there.
2. Every utterance is language-identified server-side from its script.
3. On a change the server emits `language_set {auto:true}`, answers in the new
   language from that turn on, and keeps the record already collected.
4. Your selector can still send `set_language` at any time; that wins until the
   worker speaks a different language again.

Set `SAHAYAK_AUTO_LANGUAGE=0` to disable detection and stay on the selected
language. In auto mode the STT stream is opened with all eight locales,
which costs some per-language accuracy — narrow it once you know your users.

---

## 5. Operational notes

- `SAHAYAK_PRECACHE=1` (default) pre-synthesises the fixed turns at boot; set
  `0` to avoid spending Gnani credits while developing.
- Every saved visit creates follow-ups (`next_visit`, `immunisation`,
  `phc_referral`) — show them from `record_saved.follow_ups` or
  `/api/follow-ups`.
- The transcript and record payload are encrypted at rest; only IDs, visit
  type, weight, due date and flags are plaintext for dashboard queries.
- `python scripts/purge_data.py --yes` wipes all clinical data.
