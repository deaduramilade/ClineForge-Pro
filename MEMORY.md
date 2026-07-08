# CineForge AI Pro — Memory File

> This file is the **living memory** of the project. Update it after every major session.
> Copilot and any AI agent working in this repo should read this file first.

---

## Current Status

**Phase**: Foundation / Scaffolding  
**Last Updated**: 2026-07-08  
**Overall Progress**: 🟡 In Progress — initial structure created, features not yet implemented

---

## Key Architectural Decisions

| Decision | Choice | Rationale | Date |
|----------|--------|-----------|------|
| AI Backend | IBM Granite via watsonx.ai | Challenge requirement; strong Arabic NLP | 2026-07 |
| Web Framework | FastAPI (Python) | Async support, auto-docs, easy ML integration | 2026-07 |
| Frontend | Next.js 14 + TypeScript + Tailwind | SSR, App Router, strong typing, rapid UI | 2026-07 |
| Encryption | AES-256 (client-side, WebCrypto API) | Scripts never transmitted in plaintext | 2026-07 |
| Watermarking | C2PA-inspired (custom metadata embedding) | Provenance tracking for generated assets | 2026-07 |
| Language Support | Arabic (RTL) + English (LTR) | Core requirement for target market | 2026-07 |
| Monorepo structure | `src/backend/` + `src/frontend/` | Shared repo, separate deployment | 2026-07 |

---

## IBM Bob Usage Log

| Session | Mode | What Was Done | Bob Log |
|---------|------|---------------|---------|
| 2026-07-08 | Plan | Initial project structure planning | `docs/bob-log/` |

---

## Current Architecture Summary

```
Browser (Next.js)
    │
    │  HTTPS + encrypted payloads
    ▼
FastAPI Backend (Python)
    │
    ├── /api/scripts   → Script upload & parsing
    ├── /api/generate  → Granite storyboard generation
    ├── /api/animatic  → Motion animatic pipeline
    ├── /api/budget    → Production budget estimator
    └── /api/health    → Health check
    │
    ▼
IBM watsonx.ai (Granite)
    + Local watermark service
```

---

## Important Context

- **Arabic support is critical** — all text processing must handle RTL and Unicode Arabic correctly
- **Client-side encryption is non-negotiable** — AES-256 encryption happens in the browser before any API call
- **IBM Bob must be documented** — every major dev session using Bob should be logged in `docs/bob-log/`
- **Tight deadline** — 31 July 2026; prioritize demo-critical paths (upload → storyboard → export)
- **watsonx.ai credentials** are stored in `.env` (never committed); see `.env.example`

---

## Known Issues / TODOs

- [ ] Implement script parser for Arabic PDF/DOCX
- [ ] Integrate Granite multimodal API
- [ ] Build client-side AES-256 encryption module
- [ ] Build C2PA watermarking service
- [ ] Implement budget estimator
- [ ] Build animatic export pipeline
- [ ] Add RTL support throughout Next.js UI
- [ ] Set up CI/CD pipeline

---

## Completed Milestones

- [x] Project charter defined
- [x] Architecture decided
- [x] Initial folder structure and scaffolding created
- [x] Documentation files created
