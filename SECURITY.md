# CineForge AI Pro — Security Policy

---

## 1. Overview

Security is a **first-class concern** in CineForge AI Pro. Scripts and creative assets are sensitive intellectual property. This document defines mandatory security practices for all contributors and AI agents.

---

## 2. Client-Side Encryption

### 2.1 Requirement
All script files and creative content **MUST be encrypted client-side before transmission**. No plaintext script data may be sent over the network.

### 2.2 Implementation
- **Algorithm**: AES-256-GCM
- **API**: WebCrypto API (`window.crypto.subtle`)
- **Key management**: Encryption keys are derived from a user passphrase + PBKDF2; keys never leave the browser
- **Implementation file**: `src/frontend/lib/crypto.ts`

### 2.3 Rules for Developers
```
✅ DO: Encrypt before sending to any API endpoint
✅ DO: Use AES-256-GCM with a random 96-bit IV per encryption
✅ DO: Use PBKDF2 with ≥ 100,000 iterations for key derivation
❌ DO NOT: Transmit plaintext scripts over HTTP or HTTPS
❌ DO NOT: Store raw script content in localStorage or sessionStorage
❌ DO NOT: Log decrypted content in browser console or server logs
```

---

## 3. C2PA-Inspired Watermarking

### 3.1 Requirement
Every AI-generated image and video frame **MUST carry a verifiable watermark** that encodes provenance information.

### 3.2 Implementation
- **Method**: Metadata embedding (EXIF/XMP) + perceptual hash stored in a manifest
- **Manifest content**: timestamp, Granite model version, project ID, user ID hash
- **Implementation file**: `src/backend/services/watermark.py`

### 3.3 Rules for Developers
```
✅ DO: Apply watermark to every image before returning it to the client
✅ DO: Include generation timestamp and model identifier in manifest
✅ DO: Verify watermark integrity on asset retrieval
❌ DO NOT: Return unwatermarked media to the client
❌ DO NOT: Allow watermark removal via any API endpoint
```

---

## 4. Secrets & Credentials Management

### 4.1 Environment Variables
- **ALL** credentials must be stored in environment variables
- Use `.env` locally (never committed to git)
- `.env.example` provides the template — no real values allowed in this file
- In production/CI, use secure secret stores (IBM Secrets Manager, GitHub Secrets)

### 4.2 .gitignore Rules
The `.gitignore` already excludes `.env` files. **Never remove these entries.**

### 4.3 Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `WATSONX_API_KEY` | IBM watsonx.ai API key | ✅ |
| `WATSONX_PROJECT_ID` | watsonx.ai project identifier | ✅ |
| `WATSONX_URL` | watsonx.ai endpoint URL | ✅ |
| `ENCRYPTION_SALT` | Server-side salt for key derivation (32+ bytes, hex) | ✅ |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | ✅ |
| `SECRET_KEY` | Application secret key (32+ bytes, random) | ✅ |
| `LOG_LEVEL` | Logging verbosity (info/warning/error) | ✅ |

---

## 5. API Security

### 5.1 CORS
- Strict allowlist configured in FastAPI CORS middleware
- Only allow origins listed in `ALLOWED_ORIGINS`
- Never use wildcard (`*`) in production

### 5.2 Input Validation
- All request bodies validated by Pydantic models
- File uploads: validate MIME type and file size
- Maximum file size: 50 MB for script uploads

### 5.3 Rate Limiting
- Implement rate limiting on `/api/generate/*` endpoints to prevent credit abuse
- Use `slowapi` (FastAPI compatible) for rate limiting

---

## 6. Data Handling Rules

| Data Type | Handling Rule |
|-----------|--------------|
| Raw script content | Encrypt client-side; never store plaintext server-side |
| Generated storyboard frames | Watermark before delivery; store with project ID |
| API keys | Environment variables only |
| User passphrases | Never transmitted; used only for local key derivation |
| Budget estimates | No PII; may be stored in project metadata |

---

## 7. Reporting Security Issues

If you discover a security vulnerability in this project:
1. **Do not** open a public GitHub issue
2. Contact the project team directly
3. Include a clear description and reproduction steps

---

## 8. Compliance

This project follows:
- OWASP Top 10 guidelines
- C2PA (Coalition for Content Provenance and Authenticity) principles
- IBM watsonx.ai terms of service and responsible AI guidelines
