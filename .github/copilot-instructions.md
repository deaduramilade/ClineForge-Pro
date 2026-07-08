# CineForge AI Pro — GitHub Copilot Instructions

You are working on **CineForge AI Pro** — a secure multimodal AI pipeline that turns Arabic and English film scripts into storyboards, motion animatics, and production budget estimates.

---

## Always Read First

Before generating any code or documentation, read these files:
- `MEMORY.md` — current project state and architectural decisions
- `AGENT.md` — strict rules for how you must behave in this repo
- `ARCHITECTURE.md` — system design and component map
- `SECURITY.md` — mandatory security rules (encryption + watermarking)

---

## Project Context

- **Tech stack**: FastAPI (Python 3.11) + Next.js 14 (TypeScript + Tailwind CSS)
- **AI provider**: IBM Granite via watsonx.ai (only AI provider allowed)
- **Languages supported**: Arabic (RTL) + English (LTR) — both are first-class
- **Security**: AES-256 client-side encryption (WebCrypto API) + C2PA watermarking
- **Deadline**: 31 July 2026 (IBM SkillsBuild AI Builders Challenge)

---

## Security Rules (Non-Negotiable)

- NEVER generate code that transmits plaintext scripts over the network
- NEVER hardcode credentials, API keys, or secrets
- ALWAYS use environment variables for all credentials (see `.env.example`)
- ALWAYS apply AES-256-GCM encryption before any script leaves the browser
- ALWAYS embed C2PA watermarks in generated media before delivery

---

## Code Style

- **Python**: PEP 8, type hints required, async/await for all I/O
- **TypeScript**: strict mode, no `any`, functional components in React
- **API**: RESTful, Pydantic schemas for all request/response models
- **Commits**: `feat(scope): description` format (Conventional Commits)

---

## Arabic Support

- All UI components MUST support both Arabic (RTL) and English (LTR)
- Use `dir` attributes appropriately on all containers
- Use Arabic-compatible fonts (Noto Naskh Arabic, Cairo)
- Test all text inputs with Arabic Unicode strings

---

## IBM Bob Usage

- Every major dev session MUST use IBM Bob (Ask → Plan → Code)
- Log sessions in `MEMORY.md` and save screenshots to `docs/bob-log/`
- Reference the Bob session in every PR description

---

## Project Structure

```
src/backend/     ← FastAPI application
src/frontend/    ← Next.js application
docs/            ← All documentation
docs/bob-log/    ← IBM Bob session screenshots
.github/         ← GitHub configuration
```

---

## Team Roles

| Role | Area |
|------|------|
| Data Science Lead | `services/script_parser.py`, `services/budget_estimator.py` |
| ML Engineer | `services/granite_service.py`, `services/animatic.py` |
| Cybersecurity Specialist | `lib/crypto.ts`, `services/watermark.py` |
| Full-Stack Developers | `routers/`, `app/`, `components/` |
