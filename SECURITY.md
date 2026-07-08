SECURITY.md
CineForge AI Pro
Security Architecture, Risk Register & Hardening Guidelines
Last Updated: 8 July 2026
1. Security Philosophy
CineForge AI Pro treats intellectual property protection as a core feature, not an afterthought. Every script and generated asset must be handled with care because creators often work with sensitive or valuable creative material.
Our approach follows the principle of "Secure by Default":

Encrypt sensitive data as early as possible (on the client).
Apply provenance and watermarking to all generated outputs.
Maintain transparent and defensible security claims.

2. Corrected Security Claims (Hardening Addendum)
The following claims have been officially updated to reflect what the system can actually deliver and defend:























AreaCorrected ClaimPrevious (Incorrect) ClaimReason for ChangeEncryptionClient-side AES-256 encryption with local key generationZero-knowledge client-side script encryptionServer processes the script content, so true zero-knowledge is not achievedContent ProvenanceC2PA-inspired content provenance metadataC2PA-standard content credentialsFull C2PA compliance requires the official library. Current implementation follows the same principles
Note: Full C2PA support via the c2pa-rs library remains a low-effort future upgrade and is documented as such.
3. Technical Risk Register
This register is a living document. It must be reviewed and updated at the end of every phase.





























































RiskLikelihoodImpactMitigation / Fallback StrategyOwnerStatusArabic NLP parsing fails on non-standard formatting or mixed Arabic/English scriptsMediumHighImplement rule-based tokenization fallback (regex + keyword scene markers) so the pipeline degrades gracefullyData Science LeadPhase 1watsonx.ai rate limit or latency spike during live demoMediumHighMaintain a cached run of the exact judge-line demo scenario as an instant backupMachine Learning EngineerPhase 2Diffusion model output quality inconsistent for a judge’s improvised lineLow-MediumMediumConstrain Live Judge Mode to short single-sentence inputs and pre-tune prompt templates for common shot typesMachine Learning EngineerPhase 2Animatic audio-visual sync drifts under time pressureLowMediumCap animatic length to 15–20 seconds per scene; perform manual sync check before demoMachine Learning EngineerPhase 3Unauthorized access to uploaded scriptsMediumHighEnforce client-side encryption before upload + strict API authentication and rate limitingCybersecurity SpecialistPhase 1Generated assets being misused or leakedMediumHighApply invisible forensic watermarking + C2PA-inspired provenance metadata on every outputCybersecurity SpecialistPhase 2
4. Encryption Implementation

All scripts must be encrypted on the client side using AES-256 before being transmitted to the server.
Encryption keys must be generated locally on the user’s device and never sent to the server.
The server should only ever receive encrypted data.
Temporary files on the server must be automatically deleted after processing (recommended: within 1 hour).

5. Content Provenance & Watermarking

Every generated storyboard frame and animatic must include:
Invisible forensic watermarking
C2PA-inspired provenance metadata (embedded or attached)

Watermarking must survive common image transformations (compression, resizing, format conversion).
The watermark should allow traceability back to the original generation request without exposing user data.

6. Data Handling & Privacy Principles

Data Minimization: Only collect and process the minimum data required.
Ephemeral Storage: Scripts and generated assets should not be stored longer than necessary.
No Training on User Data: User scripts and generations must not be used to train or improve models.
Auditability: All security-related decisions and implementations must be documented.

7. API & Endpoint Security

All API endpoints must implement proper authentication and rate limiting.
Input validation is mandatory on all endpoints that accept scripts or generation requests.
Sensitive operations (especially generation) should be protected against abuse.
Error messages should not leak internal system details.

8. Demo & Production Security Considerations

For the Live Judge Mode, input sanitization is critical.
A cached “safe” demo scenario must always be available as a fallback.
In production (future), consider adding usage quotas and abuse detection.

9. Responsibilities

























RoleSecurity ResponsibilitiesCybersecurity SpecialistOverall security architecture, encryption, watermarking, Risk Register, API hardeningData Science LeadSecure parsing logic and fallback mechanismsMachine Learning EngineerSecure model inference, prompt safety, and generation pipeline hardeningFull-Stack DevelopersSecure frontend-backend communication, client-side encryption implementation, and UI-level protections
10. Living Document Instructions
This file must be updated whenever:

A new risk is identified
A mitigation is implemented or changed
Security-related architectural decisions are made

All team members and AI agents should treat this document as authoritative for security matters.

End of SECURITY.md