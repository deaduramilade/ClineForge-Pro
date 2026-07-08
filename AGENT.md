# CineForge AI Pro — Agent & Copilot Rules

> **MANDATORY**: Any AI agent, GitHub Copilot instance, or automated tool working in this repository **MUST** read and follow the rules in this file before generating any code, documentation, or configuration.

---

## 1. Always Read First

Before generating any code or documentation:
1. Read `MEMORY.md` — understand current project state and past decisions
2. Read `CHARTER.md` — understand scope, goals, and team roles
3. Read `ARCHITECTURE.md` — understand system design
4. Read `SECURITY.md` — understand mandatory security rules
5. Read the relevant file you are about to modify

---

## 2. IBM Bob Usage Rules

- **Tag every IBM Bob session** in `MEMORY.md` under the "IBM Bob Usage Log" table
- Save screenshots of Bob sessions to `docs/bob-log/` using format: `YYYY-MM-DD_<topic>.png`
- Use the correct Bob mode:
  - **Ask mode** — for questions, explanations, research
  - **Plan mode** — for architecture, approach planning before coding
  - **Code mode** — for actual code generation and implementation

---

## 3. Security Rules (Non-Negotiable)

- **NEVER** generate code that transmits plaintext script content over the network
- **NEVER** hardcode secrets, API keys, or credentials in source files
- **ALWAYS** use environment variables for credentials (see `.env.example`)
- **ALWAYS** apply AES-256 encryption before any script data leaves the browser
- **ALWAYS** embed C2PA watermarks in generated media before delivering to the client
- **NEVER** commit `.env` files — only `.env.example` is allowed in git

---

## 4. Language & Localization Rules

- **ALWAYS** support both Arabic (RTL) and English (LTR) in any UI component
- Use `dir="rtl"` and `dir="ltr"` attributes appropriately
- All Arabic text must use Unicode-safe string handling
- Font choices must support Arabic script (e.g., Noto Naskh Arabic, Cairo)
- Date/number formatting must respect locale settings

---

## 5. Code Quality Rules

- **Python** (backend): Follow PEP 8, use type hints, use async/await for I/O
- **TypeScript** (frontend): Strict mode enabled, no `any` types unless unavoidable
- **API design**: Follow RESTful conventions, use Pydantic models for all request/response schemas
- **Error handling**: Never swallow exceptions silently; log all errors with context
- **Tests**: Write tests for every new service or utility function

---

## 6. File & Structure Rules

- Backend code → `src/backend/`
- Frontend code → `src/frontend/`
- Documentation → `docs/`
- IBM Bob session logs → `docs/bob-log/`
- Environment config → `.env.example` (template only)
- Do **not** create files outside this structure without updating `ARCHITECTURE.md`

---

## 7. PR & Commit Rules

- Every PR must reference the IBM Bob session used to generate the code
- Commit messages must follow: `<type>(<scope>): <short description>`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
  - Example: `feat(backend): add script upload endpoint`
- Every PR must fill out the PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
- No PR may be merged without at least one human review

---

## 8. What NOT to Do

- Do **not** install new dependencies without updating `requirements.txt` or `package.json`
- Do **not** modify `CHARTER.md` scope without team agreement
- Do **not** use AI models other than IBM Granite via watsonx.ai for generation tasks
- Do **not** generate placeholder code with `TODO` comments and leave it untracked — add it to `MEMORY.md` known issues
- Do **not** add unnecessary complexity — keep it demo-ready, not production-perfect
