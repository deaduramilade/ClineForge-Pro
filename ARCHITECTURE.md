# CineForge AI Pro — Architecture

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (Next.js 14)                      │
│                                                              │
│  ┌──────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │ Script Upload │  │ Storyboard Canvas│  │ Live Judge    │  │
│  │ (AES-256 enc) │  │ (frame viewer)  │  │ Mode Dashboard│  │
│  └──────┬───────┘  └────────┬────────┘  └───────────────┘  │
│         │ WebCrypto          │                               │
└─────────┼────────────────────┼───────────────────────────────┘
          │ HTTPS (encrypted)  │ HTTPS
          ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Python 3.11)               │
│                                                              │
│  /api/health    → Health check & system status              │
│  /api/scripts   → Script upload, decrypt, parse             │
│  /api/generate  → Storyboard generation (Granite)           │
│  /api/animatic  → Motion animatic export pipeline           │
│  /api/budget    → Production budget estimator               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Services Layer                    │   │
│  │  script_parser | granite_service | watermark        │   │
│  │  budget_estimator | animatic | encryption_utils     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│ IBM watsonx  │   │ Local Watermark   │
│ (Granite LLM │   │ Service (C2PA-    │
│  + Vision)   │   │  inspired)        │
└──────────────┘   └──────────────────┘
```

---

## 2. Component Responsibilities

### Frontend (`src/frontend/`)

| Component | Responsibility |
|-----------|---------------|
| `app/upload/` | Script file upload with client-side AES-256 encryption |
| `app/storyboard/` | Storyboard canvas — display generated frames |
| `app/judge/` | Live Judge Mode — real-time demo dashboard |
| `components/` | Shared UI components (bilingual, RTL-aware) |
| `lib/crypto.ts` | WebCrypto API wrapper for AES-256 encryption |
| `lib/api.ts` | Typed API client for backend communication |
| `lib/i18n.ts` | Internationalisation (Arabic / English) |

### Backend (`src/backend/`)

| Module | Responsibility |
|--------|---------------|
| `main.py` | FastAPI app factory, middleware, CORS |
| `routers/scripts.py` | Script upload, storage, retrieval endpoints |
| `routers/generate.py` | Storyboard generation endpoints |
| `routers/animatic.py` | Motion animatic export endpoints |
| `routers/budget.py` | Budget estimator endpoints |
| `services/script_parser.py` | Arabic/English script parsing & scene segmentation |
| `services/granite_service.py` | IBM Granite API client & prompt engineering |
| `services/watermark.py` | C2PA-inspired watermark embedding |
| `services/budget_estimator.py` | Production cost estimation logic |
| `services/animatic.py` | Frame sequencing & video export |
| `models/` | Pydantic schemas for all request/response types |

---

## 3. Data Flow — Script to Storyboard

```
1. User uploads script file (browser)
   ↓
2. Client-side AES-256 encryption (WebCrypto)
   ↓
3. Encrypted payload sent to POST /api/scripts/upload
   ↓
4. Backend decrypts payload (with user key)
   ↓
5. script_parser.py segments scenes (NLP, bilingual)
   ↓
6. For each scene → POST /api/generate/storyboard
   ↓
7. granite_service.py calls IBM Granite multimodal
   ↓
8. Generated frames → watermark.py embeds C2PA watermark
   ↓
9. Watermarked frames returned to browser
   ↓
10. Storyboard canvas displays frames
    ↓
11. Optional: animatic export (MP4/GIF)
```

---

## 4. Security Architecture

- **Client-side encryption**: AES-256-GCM via WebCrypto API; key never leaves browser
- **Transport**: HTTPS/TLS for all API communication
- **Watermarking**: C2PA-inspired metadata + steganographic hash embedded in every generated image
- **Secrets**: All credentials in environment variables, never in source code
- **CORS**: Strict origin allowlist configured in FastAPI middleware

---

## 5. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend framework | Next.js | 14.x |
| Frontend language | TypeScript | 5.x |
| Frontend styling | Tailwind CSS | 3.x |
| Backend framework | FastAPI | 0.111.x |
| Backend language | Python | 3.11 |
| AI provider | IBM Granite (watsonx.ai) | latest |
| Encryption | WebCrypto (browser) + cryptography (Python) | — |
| Package manager | npm (frontend), pip (backend) | — |

---

## 6. Environment Variables

See `.env.example` for all required environment variables. Critical ones:

| Variable | Purpose |
|----------|---------|
| `WATSONX_API_KEY` | IBM watsonx.ai API key |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID |
| `WATSONX_URL` | watsonx.ai endpoint URL |
| `ENCRYPTION_SALT` | Server-side salt for key derivation |
| `ALLOWED_ORIGINS` | CORS allowed origins list |
