CONTRIBUTING.md
CineForge AI Pro
How to Contribute & Development Workflow
Last Updated: 8 July 2026
Thank you for contributing to CineForge AI Pro! This document explains how our team works together to deliver a high-quality project on a tight timeline.
1. Project Principles
Before contributing, please read and understand the following documents:

CHARTER.md — Vision, scope, goals, and success criteria
MEMORY.md — Current decisions and project context
AGENT.md — Rules for AI-assisted development
SECURITY.md — Security requirements and Risk Register

All contributions must align with these documents.
2. Development Workflow
We follow a simple and efficient workflow suited for a small team with a hard deadline.
Branching Strategy

main branch is protected and always represents the latest stable state.
Create a new branch for every task or feature:
Use descriptive names, e.g.:
feature/secure-encryption
feature/budget-estimator
fix/arabic-parsing-edge-case
docs/update-risk-register



Commit Message Standard (Mandatory)
Every commit must follow the IBM Bob tagging convention:
text[Bob:Ask #NN] Description of what was asked/analyzed
[Bob:Plan #NN] Description of the plan or architecture decision
[Bob:Code #NN] Description of the implementation or fix
Examples:

[Bob:Plan #3] Designed client-side encryption flow with local key generation
[Bob:Code #7] Implemented AES-256 encryption module in backend
[Bob:Ask #12] Reviewed Arabic tokenization fallback strategy

Screenshots of Bob usage should be placed in /docs/bob-log/ and referenced in the commit when relevant.
3. Pull Request Process

Create a feature branch from main.
Make your changes and commit using the Bob tagging format.
Push your branch and open a Pull Request.
In the PR description, include:
What was done
Which Bob tags were used
Any risks or decisions that should be recorded in MEMORY.md

Request review from at least one other team member.
Once approved and CI passes (if applicable), merge into main.

Note: Small documentation fixes or typo corrections can be merged directly by the author after pushing.
4. Local Development Setup

Clone the repository:Bashgit clone https://github.com/your-org/cineforge-ai-pro.git
cd cineforge-ai-pro
Set up the backend (FastAPI):Bashcd src/backend
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
pip install -r requirements.txt
Set up the frontend (Next.js):Bashcd src/frontend
npm install
npm run dev
Create a .env file based on .env.example (never commit real secrets).

5. Code Quality Guidelines

Write clean, readable, and well-documented code.
Follow existing code style in the repository.
Use TypeScript in the frontend.
Add basic error handling and input validation.
Keep components modular (especially parsing, generation, and security layers).
Update relevant documentation (MEMORY.md, SECURITY.md, etc.) when making significant changes.

6. Security When Contributing

Never commit API keys, tokens, or sensitive credentials.
Follow the security rules defined in SECURITY.md.
If you discover a potential security issue, report it privately to the Cybersecurity Specialist instead of opening a public issue.

7. Using AI Tools (Copilot, etc.)

Follow the rules in AGENT.md when using GitHub Copilot or any other AI assistant.
Always review AI-generated code carefully before committing.
Major AI-generated features should be discussed with the team.

8. Documentation Contributions
We maintain high-quality documentation. When updating docs:

Keep language clear and professional.
Update MEMORY.md for any important decisions.
Use consistent formatting.

9. Getting Help

For technical questions: Open a GitHub Issue or discuss in the team channel.
For scope or direction questions: Refer to CHARTER.md first.
For urgent blockers: Tag the relevant role owner directly.

10. Recognition
All meaningful contributions will be acknowledged. This includes code, documentation, security improvements, and demo preparation.

Thank you for helping build CineForge AI Pro!
By following these guidelines, we can maintain quality, move quickly, and deliver a strong submission by 31 July 2026.