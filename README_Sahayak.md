# Sahayak --- Visit Compass

**A voice-first field-visit assistant for frontline community health
workers**

Sahayak (Visit Compass) is a full-stack application designed to support
ASHA workers during maternal, newborn, and child-health home visits. It
combines a React-based interface with a Python FastAPI backend,
real-time voice interaction, structured information extraction,
danger-sign flagging, and visit/follow-up records.

> **Project status:** The project handoff documentation describes the
> frontend and backend as integrated, including REST-based
> dashboard/record workflows and a WebSocket-based live voice visit. Run
> the setup and test instructions below in your target environment
> before relying on a particular deployment or demo.

------------------------------------------------------------------------

## Contents

-   [Problem](#problem)
-   [Solution](#solution)
-   [Key capabilities](#key-capabilities)
-   [Architecture](#architecture)
-   [Technology stack](#technology-stack)
-   [Repository structure](#repository-structure)
-   [Prerequisites](#prerequisites)
-   [Getting started](#getting-started)
-   [Environment configuration](#environment-configuration)
-   [API and real-time communication](#api-and-real-time-communication)
-   [Testing](#testing)
-   [Example demo flows](#example-demo-flows)
-   [Security, privacy, and responsible
    use](#security-privacy-and-responsible-use)
-   [Known considerations](#known-considerations)
-   [Roadmap](#roadmap)
-   [Contributing](#contributing)
-   [License](#license)

------------------------------------------------------------------------

## Problem

Frontline community health workers often conduct visits in busy
household environments while collecting information about pregnant
mothers, postnatal mothers, newborns, and children. Paper-based records
and multi-step digital forms can interrupt conversations, increase
documentation effort, and make it harder to keep visit information and
follow-ups organized.

Sahayak is intended to reduce that operational burden by making visit
documentation more conversational and voice-oriented.

## Solution

Sahayak provides a guided visit workflow in which a health worker can
speak naturally, review the information captured by the system, and
confirm a record before it is saved. The application combines:

1.  A web dashboard for beneficiaries, visit records, and follow-ups.
2.  A real-time voice visit interface.
3.  Speech recognition and speech synthesis integrations.
4.  Structured field extraction, with a deterministic parser first and
    an LLM-assisted fallback for more complex utterances.
5.  Rule-based danger-sign checks that can interrupt the routine visit
    flow.
6.  A verbal/read-back confirmation step before saving visit
    information.

Sahayak is a workflow-support tool. It is not a substitute for a
qualified health professional, clinical judgement, or established
emergency referral procedures.

## Key capabilities

-   **Voice-first visit workflow:** Push-to-talk interaction with
    microphone controls and real-time audio handling.
-   **Speech processing:** Gnani streaming speech-to-text (STT) and
    text-to-speech (TTS) integrations.
-   **Structured extraction:** Captures visit information such as
    beneficiary ID, visit type, weight, vaccinations due, and next-visit
    date.
-   **Two-tier extraction:** Fast rule/regex parsing for straightforward
    values, with Gemini-assisted extraction as a fallback for more
    complex language.
-   **Danger-sign flagging:** Deterministic, rule-based checks for
    configured warning signs, including pregnancy bleeding, newborn high
    fever, convulsions, and breathing difficulty.
-   **Read-back and confirmation:** Presents captured information for
    worker verification before committing the visit.
-   **Visit and beneficiary records:** Backend-backed data for dashboard
    and record views.
-   **Follow-up management:** Retrieves follow-up tasks and supports
    status updates.
-   **Language handling:** Includes localized prompts and
    language/script handling for the languages configured in the
    backend.

> Danger-sign rules and language behaviour must be clinically reviewed
> and validated before use in real care settings. A rule-based alert is
> not a diagnosis.

## Architecture

``` text
┌──────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│                                                          │
│  Dashboard | Live Visit | Beneficiaries | Records        │
│  Follow-ups | Settings                                    │
└───────────────────────┬──────────────────────────────────┘
                        │
             REST API   │   WebSocket /ws
                        │   (live visit + audio)
┌───────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                       │
│                                                          │
│  REST endpoints       WebSocket session manager          │
│  Dialogue state       Field extraction                   │
│  Danger-sign rules    Validation                         │
│  Localization         Visit/follow-up persistence        │
└───────────┬───────────────────┬──────────────────────────┘
            │                   │
     ┌──────▼──────┐      ┌─────▼────────────────┐
     │ SQLite DB   │      │ AI / Voice Services │
     │ encrypted   │      │ Gemini extraction   │
     │ visit data  │      │ Gnani STT and TTS   │
     └─────────────┘      └──────────────────────┘
```

### Main interaction flow

1.  The frontend loads dashboard and record data from backend REST
    endpoints.
2.  A worker starts a visit from the Live Visit screen.
3.  The browser captures microphone audio and streams audio frames
    through the backend WebSocket.
4.  The backend processes speech, extracts fields, checks configured
    danger signs, and manages the dialogue state.
5.  The system reads back the captured details.
6.  The worker confirms or cancels the record.
7.  Confirmed visit information and associated follow-up data are stored
    by the backend.

## Technology stack

  -----------------------------------------------------------------------
  Layer                               Technologies
  ----------------------------------- -----------------------------------
  Frontend                            React 19, Vite, TanStack
                                      Start/Router, Tailwind CSS,
                                      shadcn/ui

  Backend                             Python, FastAPI, Uvicorn,
                                      WebSockets

  Database                            SQLite

  Data protection                     Fernet encryption for configured
                                      clinical payloads

  LLM extraction                      Google Gemini API

  Speech                              Gnani Prisma STT and Gnani Timbre
                                      TTS

  Browser audio                       Web Audio API, microphone capture,
                                      PCM audio streaming

  Testing                             Python test scripts and automated
                                      test suite
  -----------------------------------------------------------------------

## Repository structure

The handoff documentation describes the following layout. Exact
filenames may differ if the repository has since been refactored.

``` text
sahayak/
├── app/
│   ├── main.py
│   ├── dialogue.py
│   ├── extractor.py
│   ├── danger_signs.py
│   ├── gnani_stt.py
│   ├── gnani_tts.py
│   ├── db.py
│   ├── validation.py
│   └── i18n.py
├── tests/
│   ├── test_all.py
│   └── test_language_switch.py
├── static/
│   └── talk.html
├── frontend/
│   ├── package.json
│   └── src/
│       ├── services/
│       │   ├── api.js
│       │   ├── voiceClient.js
│       │   ├── voiceService.js
│       │   ├── visitService.js
│       │   ├── beneficiaryService.js
│       │   └── followupService.js
│       ├── context/
│       ├── pages/
│       └── mock/
├── requirements.txt
├── CONTRACT.md
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

Install the following before running the application:

-   Python (the project handoff was developed with Python 3.14; use a
    version compatible with the pinned backend dependencies).
-   Node.js and npm.
-   Git.
-   A Gnani API credential for the configured STT/TTS services.
-   A Google Gemini API key if Gemini-assisted extraction is enabled.

## Getting started

The commands below use Windows PowerShell and assume the backend is at
the repository root and the frontend is in `frontend/`.

### 1. Clone the repository

``` powershell
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

### 2. Configure the backend

Create and activate a virtual environment:

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

``` powershell
pip install -r requirements.txt
```

Create a local `.env` file in the backend root. See [Environment
configuration](#environment-configuration).

### 3. Start the backend

``` powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful local endpoints documented by the project:

-   Health check: `http://localhost:8000/health`
-   Interactive API documentation: `http://localhost:8000/docs`
-   Standalone voice test page: `http://localhost:8000/talk`

### 4. Install and start the frontend

Open a second PowerShell terminal:

``` powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in the terminal. The default
development URL may be `http://localhost:5173`, but use the actual URL
printed by your environment.

### 5. Build the frontend

From the frontend directory:

``` powershell
npm run build
```

## Environment configuration

Create `.env` locally in the backend root. Never commit real
credentials.

``` env
GNANI_API_KEY=your_gnani_api_key
LLM_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-lite-latest
ENCRYPTION_KEY=your_fernet_key
```

Notes:

-   Use the exact variable names expected by the backend configuration.
-   Generate and securely store a Fernet-compatible key for
    `ENCRYPTION_KEY`; do not use the placeholder above.
-   Keep `.env`, database files, encryption keys, virtual environments,
    and `node_modules` out of Git.
-   If the frontend API configuration currently points to `localhost`,
    update it to the correct backend origin for your environment. For
    production, use HTTPS and WSS endpoints.

## API and real-time communication

The frontend services described in the project handoff use these backend
routes:

  Method      Endpoint                     Purpose
  ----------- ---------------------------- -------------------------------------------
  GET         `/health`                    Backend health check
  GET         `/api/beneficiaries`         Retrieve beneficiaries
  GET         `/api/visits`                Retrieve visit records
  POST        `/api/visits/{id}/confirm`   Confirm a visit
  GET         `/api/followups`             Retrieve follow-up tasks
  PATCH       `/api/followups/{id}`        Update follow-up status
  WebSocket   `/ws`                        Live visit dialogue and voice interaction

Refer to [`CONTRACT.md`](CONTRACT.md) for the authoritative
request/response and WebSocket message contract. Confirm route names and
payloads against the running backend if the contract and implementation
differ.

## Testing

Run the backend tests from the repository root:

``` powershell
python tests/test_all.py
python tests/test_language_switch.py
python test_danger.py
```

The handoff documentation also identifies these additional test
utilities:

``` text
test_speech.py       Gnani STT/TTS connectivity checks
test_voice_ws.py     Simulated voice visit over WebSocket
test_ws.py           Text-based WebSocket dialogue test
```

Run the tests that are present in your checkout. External API tests may
require valid credentials, network access, and provider availability.

## Example demo flows

### Routine visit

1.  Open the Live Visit screen and start a new visit.
2.  Use push-to-talk or the microphone control.
3.  Provide the beneficiary ID, visit type, weight, vaccination
    information, and next-visit date.
4.  Review the system's read-back of the captured information.
5.  Confirm the visit to save it.
6.  Verify the saved record and any generated follow-up in the
    corresponding screens.

### Configured danger-sign scenario

1.  Start a new visit.
2.  Enter a configured warning-sign phrase, such as pregnancy bleeding
    or newborn high fever.
3.  Verify that the routine dialogue is interrupted and the configured
    alert/referral guidance is displayed.
4.  Verify that the event is flagged in the visit workflow.

Use synthetic/demo data only. Do not test emergency behaviour on real
patients or delay actual emergency care to interact with the
application.

## Security, privacy, and responsible use

The project handoff describes Fernet-based encryption for configured
clinical payloads stored in SQLite. This is one security control; it
does **not**, by itself, establish compliance with the Digital Personal
Data Protection Act or any healthcare regulation.

Before any real-world deployment:

-   Add and verify authentication for health workers.
-   Enforce role-based access and ensure workers can access only
    authorized records.
-   Restrict CORS to trusted frontend origins.
-   Authenticate and authorize WebSocket connections.
-   Use HTTPS/WSS in deployed environments.
-   Store secrets in a managed secret store or protected environment
    configuration.
-   Define consent, purpose limitation, retention, deletion, and
    breach-response procedures.
-   Add audit logging, backups, monitoring, and recovery procedures.
-   Review encryption key generation, rotation, backup, and access
    controls.
-   Obtain clinical review of danger-sign rules, referral wording, and
    language translations.
-   Test security, privacy, reliability, and accessibility before
    production use.

The application is intended to assist documentation and workflow
coordination. It must not autonomously diagnose, prescribe, or replace
clinical assessment and established referral protocols.

## Known considerations

-   Speech and LLM features depend on external provider credentials,
    quotas, network availability, and API compatibility.
-   Local development defaults such as `localhost:8000` must be changed
    for a deployed frontend/backend setup.
-   Browser microphone access generally requires a secure context
    (HTTPS) outside localhost.
-   Audio device permissions, browser support, sample rates, and network
    latency can affect live voice interaction.
-   SQLite is suitable for local/demo workflows; evaluate a managed
    database and operational backup strategy before multi-user
    production use.
-   The repository may include demo or fallback data. Verify that
    production screens are using live backend data and not silently
    falling back to mock data.
-   Do not commit real beneficiary or patient information.

## Roadmap

Potential next engineering steps:

-   Complete production authentication and role-based access control.
-   Harden WebSocket authorization, validation, rate limiting, and
    observability.
-   Add deployment-specific frontend/backend configuration.
-   Establish automated CI tests for REST and WebSocket integration.
-   Review data retention, consent, audit, backup, and key-management
    processes.
-   Conduct clinical validation and usability testing with qualified
    stakeholders.
-   Evaluate a production database and deployment architecture for
    expected scale.

## Contributing

1.  Create a feature branch.
2.  Keep changes focused and document API or schema changes.
3.  Add or update tests for changed behaviour.
4.  Run the relevant backend tests and frontend build.
5.  Never commit secrets, database files, encryption keys, or real
    beneficiary data.
6.  Open a pull request describing the change, test evidence, and any
    deployment/configuration impact.

## License

Add the license and copyright details selected by the project
maintainers before publishing or redistributing this repository.
