MEMORY.md
CineForge AI Pro
Living Project Memory & Context Document
Last Updated: 8 July 2026
1. Current Project Status
Date: 8 July 2026
Current Phase: Phase 1 – Foundation & Secure Core Pipeline (8–15 July)
Days Remaining to Submission: 23 days (Deadline: 31 July 2026, 11:59 PM ET)
We are operating under a compressed 4-phase plan to ensure full delivery by the end of the month.
2. Core Decisions & Rationale








































DecisionRationaleDateUse 4-phase roadmap instead of original 6 phasesTight timeline (23 days). Merging phases reduces overhead while protecting all critical deliverables8 July 2026Client-side AES-256 with local key generation (not zero-knowledge)Matches what the architecture can actually deliver and defend to judges (per Hardening Addendum)8 July 2026C2PA-inspired provenance (not C2PA-standard)Honest and defensible claim. Full C2PA via c2pa-rs is noted as a future low-effort upgrade8 July 2026Prioritize Live Judge Mode and Motion Animatic in Phase 3These are the highest-impact items for judges and future users8 July 2026Include concrete worked example in Budget EstimatorMakes the feature verifiable and impressive (required by Hardening Addendum)8 July 2026Strong focus on IBM Bob documentation from Day 1Mandatory for submission and demonstrates engineering maturity8 July 2026
3. Technical Architecture Notes

Backend: FastAPI (Python)
Frontend: Next.js + TypeScript + Tailwind CSS
AI Stack: IBM Granite via watsonx.ai (primary) + Hugging Face for supplementary models
Security Layer: Client-side encryption before upload + server-side watermarking/provenance on generated assets
Data Flow: Script → Encryption (client) → Parsing → Scene JSON → Generation → Watermarking → UI
Demo Strategy: Maintain a cached “happy path” judge-line scenario as backup for live demo reliability

4. Security & Hardening Decisions

All security claims have been corrected per the Technical Hardening Addendum.
A Technical Risk Register is maintained in docs/SECURITY.md.
Encryption must happen on the client with keys generated locally.
Every generated asset must carry C2PA-inspired provenance metadata and invisible forensic watermarking.
Arabic NLP fallback strategy: Rule-based tokenization if advanced parsing fails.

5. Key Risks & Mitigations (Summary)






























RiskCurrent StatusMitigationLive demo latency or failureHigh priorityCached demo scenario ready as fallbackArabic parsing edge casesMediumRule-based fallback implemented in Phase 1Animatic sync issuesLowLimit animatic length to 15–20 secondsScope creepMediumStrictly follow the 4-phase plan and protect Phase 3 & 4 deliverables
6. Demo & Submission Priorities
Must-Have for Submission (Non-Negotiable):

Working Live Judge Mode
Motion Animatic with synced audio
Budget Estimator with visible worked example
3-minute public demo video
Complete IBM Bob documentation with tagged commits and screenshots in /docs/bob-log/
All corrected security claims reflected in README and documentation

Nice-to-Have (if time permits):

Full C2PA implementation using c2pa-rs
Export options to common editing formats

7. Team Coordination Notes

Use the Bob tagging convention on every meaningful commit: [Bob:Ask #], [Bob:Plan #], or [Bob:Code #]
All major decisions should be recorded in this MEMORY.md file
Daily async updates are recommended via GitHub Issues or a shared channel
The CHARTER.md is the source of truth for scope and direction

8. Open Items / Questions

Final decision on whether to attempt full c2pa-rs integration (currently leaning toward “inspired” approach due to time)
Exact prompt templates for Live Judge Mode (to be finalized in Phase 2/3)
Hosting strategy for the 3-minute demo video (YouTube unlisted or GitHub)

9. Living Document Instructions
This file should be updated at the end of every phase and whenever a significant decision is made.
Keep entries clear, dated, and actionable.
Copilot and new team members should read this file before starting any substantial work.