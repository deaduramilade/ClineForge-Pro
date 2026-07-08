# CineForge AI Pro — Project Charter

**Secure & Intelligent Script-to-Storyboard Copilot**
*IBM SkillsBuild AI Builders Challenge – July 2026*

---

## 1. Project Title & Overview

**Project Name:** CineForge AI Pro
**Tagline:** A secure, multilingual AI Assistant Director that transforms written scripts into production-ready visual storyboards, motion animatics, and data-driven budget estimates.

CineForge AI Pro is a multimodal generative AI pipeline designed for film, commercial, and digital content creators. It ingests scripts (with strong native support for Arabic and English), performs intelligent scene breakdown, recommends cinematic choices, generates visual storyboards and timed motion animatics with guide audio, and produces realistic shoot-day and budget forecasts — all while protecting intellectual property through encryption and content provenance mechanisms.

The project is built under the IBM SkillsBuild AI Builders Challenge with heavy utilization of IBM Bob (Ask, Plan, and Code modes), IBM Granite models via watsonx.ai, and enterprise-grade security practices.

---

## 2. Vision & Mission

### Vision
To become the most trusted AI co-pilot for pre-production in the creative industries by combining powerful generative capabilities with rigorous security, explainability, and real production value.

### Mission
Deliver a production-grade tool that dramatically reduces the time and cost of turning a script into a visual and financial plan, while giving independent creators and small teams enterprise-level protection for their intellectual property.

---

## 3. Goals & Success Criteria

### Primary Goals
- Automate and accelerate script-to-storyboard workflows.
- Provide accurate, data-driven production budgeting and scheduling insights.
- Deliver a compelling, live-demo-ready experience for judges.
- Demonstrate responsible AI development through security, provenance, and IBM Bob usage.

### Success Criteria (by 31 July 2026)
- End-to-end working pipeline: Script upload → Scene breakdown → Storyboard + Motion Animatic + Budget estimate.
- Functional Live Judge Mode that generates output from a judge's single line of script in real time.
- Clear, documented use of IBM Bob (Ask/Plan/Code) with tagged commits and screenshots.
- Strong security implementation (client-side AES-256 encryption + C2PA-inspired provenance/watermarking).
- High-quality 3-minute public demo video.
- All mandatory IBM SkillsBuild submission requirements completed.

---

## 4. Scope

### In Scope
- Bilingual (Arabic + English) script parsing and scene extraction.
- Cinematography recommendation engine (camera angles, lighting, mood, audio tone).
- Storyboard image generation and motion animatic assembly with synced guide audio.
- Rules-based Production Budget & Shoot-Day Estimator.
- Client-side encryption and forensic watermarking/provenance.
- Interactive web interface with Live Judge Mode.
- IBM Bob-driven development process with proper documentation.

### Out of Scope (for this challenge)
- Full video generation or lip-sync.
- Advanced 3D scene reconstruction.
- Integration with professional production software (Celtx, Movie Magic, etc.) beyond basic export.
- Multi-user real-time collaboration.
- Mobile application.

---

## 5. Key Deliverables

| Deliverable | Owner(s) | Priority |
|---|---|---|
| Bilingual Script Parser | Data Science Lead | High |
| Cinematography Prompt Engine | Machine Learning Engineer | High |
| Motion Animatic Generator | Machine Learning Engineer + Full-Stack | High |
| Budget & Shoot-Day Estimator | Data Science Lead | High |
| Live Judge Mode | Full-Stack Developers | High |
| Client-side Encryption + Watermarking | Cybersecurity Specialist | High |
| Polished Next.js + FastAPI UI | Full-Stack Developers | High |
| Complete Documentation & Demo | All | High |

---

## 6. Team Structure & Roles

- **Data Science Lead** — Script parsing, JSON schema design, linguistic processing, and Budget Estimator.
- **Machine Learning Engineer** — IBM Granite integration, multimodal generation (image + audio), agentic orchestration, and model tuning.
- **Cybersecurity Specialist** — Encryption, API hardening, watermarking, provenance, and risk management.
- **Full-Stack Developers** — Frontend (Next.js/React), backend (FastAPI), interactive canvas, job queues, and user experience.

---

## 7. Technical Architecture & Constraints

### Core Technology Stack
- **Backend:** Python + FastAPI
- **Frontend:** Next.js (TypeScript) + Tailwind CSS + React
- **AI Models:** IBM Granite via watsonx.ai + Hugging Face for supplementary generation
- **Orchestration:** LangChain / LangFlow (optional)
- **Security:** Client-side AES-256 encryption with local key generation + C2PA-inspired content credentials and forensic watermarking

### Key Constraints
- Must complete full development and submission by 31 July 2026.
- Strong emphasis on security and IP protection.
- Must demonstrate meaningful use of IBM Bob throughout development.
- The system should be designed for easy adaptability (see Section 9).

---

## 8. Development Methodology & Tools

- **Primary Driver:** IBM Bob (Ask, Plan, and Code modes) — mandatory and documented.
- **Version Control:** Public GitHub repository with clear commit tagging convention.
- **Project Management:** GitHub Issues + Projects board.
- **Documentation:** Living documents in `/docs/` folder (`CHARTER.md`, `MEMORY.md`, `AGENT.md`, etc.).
- **Demo & Validation:** Live Judge Mode + recorded 3-minute video.

---

## 9. Adaptability & Extensibility (Key Strategic Principle)

CineForge AI Pro is intentionally designed with modularity and future extensibility in mind, even within the constraints of a short hackathon timeline.

### Core Adaptability Principles

- **Language-Agnostic Architecture:** While Arabic receives first-class support, the parsing, tokenization, and prompt layers are built to allow additional languages (French, Spanish, Hindi, etc.) with minimal code changes. Language-specific components are isolated rather than hardcoded.
- **Modular Pipeline Design:** Each major stage (Parsing → Scene Structuring → Cinematography Recommendation → Generation → Estimator) is designed as an independent, replaceable module.
- **Config-Driven Behavior:** Key behaviors (generation models, watermarking strength, budget calculation rules, supported languages) should be configurable via files or environment variables rather than hard-coded logic.
- **Extensible Estimator:** The Budget & Shoot-Day Estimator uses a rules-based engine that can be easily extended with new parameters (location difficulty, union rules, seasonal factors, etc.).
- **Future-Proof Security Layer:** Encryption and provenance mechanisms are implemented in a way that can evolve toward full C2PA compliance or additional forensic techniques without major refactoring.

This adaptability approach ensures that CineForge can grow beyond the initial Arabic + English scope without requiring a complete rewrite.

---

## 10. Risk Management & Security

- A living Risk Register is maintained in the repository (see `docs/SECURITY.md` and `MEMORY.md`).
- All creative assets are protected by client-side encryption before leaving the user's device.
- Generated content carries invisible forensic watermarking and provenance metadata.
- The project follows responsible disclosure practices for any security findings.

---

## 11. Timeline & Milestones

The project follows the six-phase development plan (detailed separately in the team's Development Plan document):

| Phase | Description | Dates |
|---|---|---|
| Phase 1 | Foundation & Architecture | 8–11 July |
| Phase 2 | Secure Parsing & Data Pipeline | 12–18 July |
| Phase 3 | Generative Core & Orchestration | 19–24 July |
| Phase 4 | Signature Features | 25–27 July |
| Phase 5 | Dashboard Polish & Demo Preparation | 28–30 July |
| Phase 6 | Final Testing & Submission | 31 July |

---

## 12. Governance & Decision Making

- Major architectural or scope decisions require agreement from at least three team roles.
- Security-related decisions are led by the Cybersecurity Specialist with input from the full team.
- The project charter can be updated by consensus, with changes recorded in `MEMORY.md`.

---

## Document Control

| Field | Value |
|---|---|
| Version | 1.0 |
| Last Updated | 8 July 2026 |
| Maintained By | All team members |
| Next Review | After completion of Phase 2 |

*This charter serves as the single source of truth for the project's purpose, boundaries, and guiding principles. All future work and Copilot interactions should align with this document.*
