AGENT.md
CineForge AI Pro
Instructions for AI Agents & GitHub Copilot
Last Updated: 8 July 2026
Purpose of This Document
This file contains strict rules and guidelines that any AI agent or GitHub Copilot must follow when working in this repository. These instructions exist to maintain consistency, quality, security, and alignment with the project’s goals.
All AI-generated code, documentation, or suggestions must comply with the rules below.

1. Core Project Context (Must Read First)

Project Name: CineForge AI Pro
Goal: Build a secure, multimodal AI Assistant Director that converts scripts (Arabic + English) into storyboards, motion animatics, and budget estimates.
Key Differentiators: Arabic support, Motion Animatic, Live Judge Mode, Budget Estimator, and strong security (client-side encryption + provenance).
Timeline: Must be fully complete and submitted by 31 July 2026.
Current Phase: Phase 1 (Foundation & Secure Core Pipeline)

Primary Reference Documents (Read these before making changes):

CHARTER.md — Overall vision, scope, and principles
MEMORY.md — Current decisions, status, and context
SECURITY.md — Security rules and Risk Register


2. Mandatory Rules for All AI Assistance








































RuleDescriptionWhy It MattersBob TaggingEvery commit message must follow the format: [Bob:Ask #], [Bob:Plan #], or [Bob:Code #]Required for IBM SkillsBuild submissionSecurity ClaimsNever use the term “zero-knowledge”. Use only: “Client-side AES-256 encryption with local key generation”Per Hardening AddendumProvenance ClaimsUse “C2PA-inspired content provenance metadata”. Do not claim full C2PA standard unless c2pa-rs is implementedAccuracy and defensibilityLanguage SupportPrioritize Arabic + English. Design code to be easily extensible to other languagesStrategic differentiator + adaptabilityDemo PriorityProtect Live Judge Mode, Motion Animatic, and Budget Estimator above other featuresHighest impact for judgesModularityKeep components (parsing, generation, estimation, security) loosely coupledEnables future extensibility

3. Code Generation Guidelines
Always:

Write clean, readable, and well-commented code.
Follow the existing folder structure (src/backend/, src/frontend/, docs/).
Use TypeScript in the frontend and proper typing in Python where possible.
Include basic error handling and logging.
Make new features configurable when reasonable (supports adaptability).
Reference the worked Budget Estimator example when modifying the estimator.

Never:

Hardcode API keys or secrets.
Claim features that are not yet implemented.
Generate overly complex code when a simpler solution works.
Ignore the 4-phase roadmap — do not suggest major scope changes without discussion.
Use deprecated or overly heavy libraries unless justified.


4. Security Requirements

All script content must be encrypted on the client before being sent to the server.
Generated images and assets must include invisible forensic watermarking and provenance metadata.
Follow the rules defined in SECURITY.md and the Technical Risk Register.
When generating security-related code, always consider the Risk Register mitigations.


5. Documentation Standards
When asked to update or create documentation:

Keep language professional and clear.
Update MEMORY.md when making significant architectural or strategic decisions.
Maintain consistency with CHARTER.md.
Use proper Markdown formatting.
Date any important updates.


6. Phase Awareness (Current Focus)






























PhaseFocusWhat AI Should PrioritizePhase 1 (Now)Foundation, Parsing, Encryption, EstimatorClean parsing logic, encryption module, Budget Estimator with worked examplePhase 2Generative CoreGranite prompts, multimodal generation, watermarkingPhase 3Signature FeaturesMotion Animatic, Live Judge Mode, polished UIPhase 4Demo & SubmissionDemo reliability, final documentation, testing support

7. What to Do When Unsure

Check CHARTER.md and MEMORY.md first.
If still unclear, propose the safest and most modular solution.
Suggest updates to MEMORY.md when a new decision is made.
Never assume requirements — ask for clarification if something conflicts with the charter or current phase goals.


8. Final Instructions

Treat this project as a professional, investor-ready initiative, not just a hackathon submission.
Focus on quality over quantity of features.
Always protect the 5 Signature Differentiators.
Security and IBM Bob documentation are non-negotiable.
Design for adaptability — future language support and extensibility should be considered in architectural decisions.


End of AGENT.md