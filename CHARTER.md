# CineForge AI Pro — Project Charter

> **IBM SkillsBuild AI Builders Challenge — July 2026**

---

## 1. Project Vision

CineForge AI Pro is a secure, multimodal AI pipeline that transforms Arabic and English film scripts into professional storyboards, motion animatics, and production budget estimates. It bridges creative vision and production reality by combining IBM Granite's language and vision capabilities with client-side encryption, C2PA-inspired watermarking, and an intuitive bilingual interface.

---

## 2. Goals

| # | Goal | KPI |
|---|------|-----|
| G1 | Parse Arabic & English scripts into scene breakdowns | ≥ 90% scene detection accuracy |
| G2 | Generate storyboard frames per scene using Granite multimodal | ≤ 15 s per frame generation |
| G3 | Produce motion animatic previews (slide-show + transition) | Smooth playback at 24 fps |
| G4 | Estimate production budgets (crew, equipment, locations) | Within ±15% of real-world estimates |
| G5 | Protect all assets with AES-256 client-side encryption | Zero plaintext transmission of scripts |
| G6 | Embed C2PA-inspired watermarks in generated media | Verifiable provenance on every asset |

---

## 3. Success Criteria

- **Demo-ready** prototype by **31 July 2026**
- All six goals met in the final demo environment
- Passes a basic security review (encryption + watermarking functional)
- Full Arabic RTL support across all UI screens
- IBM Bob (Ask / Plan / Code) used and documented for every major development session

---

## 4. Scope

### In Scope
- Script upload and parsing (`.pdf`, `.docx`, `.txt`, Arabic + English)
- AI scene segmentation and metadata extraction (characters, locations, mood)
- Storyboard frame generation via IBM Granite multimodal
- Motion animatic export (MP4 / GIF)
- Production budget estimator module
- Client-side AES-256 encryption of scripts and storyboards
- C2PA-inspired watermarking of generated images
- Live Judge Mode — real-time demo dashboard

### Out of Scope
- Full post-production editing suite
- Distribution / streaming platform integration
- Real-time collaboration (v2 feature)
- Mobile native apps

---

## 5. Team Roles & Responsibilities

| Role | Responsibility | Key Files |
|------|---------------|-----------|
| **Data Science Lead** | Script parsing, NLP pipeline, budget estimator model | `src/backend/services/script_parser.py`, `src/backend/services/budget_estimator.py` |
| **ML Engineer** | Granite integration, multimodal prompt engineering, animatic pipeline | `src/backend/services/granite_service.py`, `src/backend/services/animatic.py` |
| **Cybersecurity Specialist** | AES-256 client-side encryption, C2PA watermarking, secrets management | `src/frontend/lib/crypto.ts`, `src/backend/services/watermark.py` |
| **Full-Stack Developers** | Next.js frontend, FastAPI backend, API design, CI/CD | `src/frontend/`, `src/backend/` |

---

## 6. Key Constraints

- **Deadline**: 31 July 2026
- **Platform**: IBM watsonx.ai (Granite models only for AI generation)
- **Security**: No plaintext script data may leave the client without encryption
- **Tooling**: IBM Bob must be used and documented for all major AI-assisted development sessions
- **Budget**: IBM SkillsBuild compute credits — avoid waste through efficient prompt design

---

## 7. Stakeholders

- IBM SkillsBuild AI Builders Challenge judging panel
- Project team (4 members)
- End users: Film producers, directors, production houses (Arabic & English markets)
