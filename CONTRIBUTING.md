# Contributing to CineForge AI Pro

Welcome to the team! Please read this guide before making your first contribution.

---

## 1. Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- IBM watsonx.ai account with Granite access
- IBM Bob access (SkillsBuild)

---

## 2. Getting Started

### Backend Setup
```bash
cd src/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example ../../.env
# Fill in your credentials in .env
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd src/frontend
npm install
cp ../../.env.example .env.local
# Fill in your NEXT_PUBLIC_* variables
npm run dev
```

---

## 3. IBM Bob Workflow (Required)

Every major development task **must** use IBM Bob and document the session.

### Workflow
1. **Ask Mode** — Research the problem, ask questions, understand requirements
2. **Plan Mode** — Create a plan/architecture for your solution
3. **Code Mode** — Generate and iterate on the implementation

### Documentation
- Save screenshots of your Bob sessions to `docs/bob-log/`
- Filename format: `YYYY-MM-DD_<short-topic>.png`
- Log the session in `MEMORY.md` under "IBM Bob Usage Log"

### Bob Tag in PRs
Every PR must include a `## IBM Bob Session` section in the PR description (see PR template).

---

## 4. Branching Strategy

```
main                  ← Protected; requires PR + review
├── develop           ← Integration branch
│   ├── feat/<name>   ← New features
│   ├── fix/<name>    ← Bug fixes
│   └── docs/<name>   ← Documentation updates
```

- Branch from `develop` for features
- Name branches: `feat/script-parser`, `fix/rtl-layout`, `docs/architecture`
- Open PRs to `develop` (not `main` directly)

---

## 5. Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer: Bob session reference]
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`  
**Scopes**: `backend`, `frontend`, `security`, `ml`, `docs`, `ci`

**Examples:**
```
feat(backend): add script upload endpoint with AES decryption
fix(frontend): correct RTL layout on storyboard canvas
docs(agent): update Bob session log for animatic pipeline
chore(deps): update ibm-watsonx-ai to 0.2.6
```

---

## 6. Pull Request Process

1. Create a branch from `develop`
2. Make your changes following the code quality rules in `AGENT.md`
3. Write/update tests for any new functionality
4. Fill in the PR template (`.github/PULL_REQUEST_TEMPLATE.md`) completely
5. Ensure all CI checks pass
6. Request review from at least one team member
7. Merge only after approval

---

## 7. Code Quality

### Python (backend)
- Follow PEP 8
- Use type hints everywhere
- Maximum line length: 100 characters
- Docstrings for all public functions/classes
- Run: `ruff check src/backend/` before committing

### TypeScript (frontend)
- Strict TypeScript (`strict: true` in tsconfig)
- No `any` types unless absolutely necessary
- Run: `npm run lint` before committing

---

## 8. Testing

### Backend
```bash
cd src/backend
pytest
```

### Frontend
```bash
cd src/frontend
npm run test
```

---

## 9. Team Role Ownership

| Area | Owner Role | Key Files |
|------|-----------|-----------|
| Script parsing & NLP | Data Science Lead | `src/backend/services/script_parser.py` |
| Budget estimator | Data Science Lead | `src/backend/services/budget_estimator.py` |
| Granite integration | ML Engineer | `src/backend/services/granite_service.py` |
| Animatic pipeline | ML Engineer | `src/backend/services/animatic.py` |
| Client-side encryption | Cybersecurity Specialist | `src/frontend/lib/crypto.ts` |
| Watermarking service | Cybersecurity Specialist | `src/backend/services/watermark.py` |
| Frontend UI | Full-Stack Devs | `src/frontend/app/`, `src/frontend/components/` |
| FastAPI routers | Full-Stack Devs | `src/backend/routers/` |

---

## 10. Questions?

Update `MEMORY.md` with any architectural decisions you make so the team (and Copilot) stays in sync.
