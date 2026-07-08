# CineForge AI Pro — Roadmap

> Target: **IBM SkillsBuild AI Builders Challenge Demo — 31 July 2026**

---

## Timeline Overview

```
Week 1 (Jul 7–13)   │ Foundation: structure, scaffolding, auth, basic upload
Week 2 (Jul 14–20)  │ Core AI: script parsing, Granite integration, storyboard gen
Week 3 (Jul 21–27)  │ Security + Polish: encryption, watermarking, animatic export
Week 4 (Jul 28–31)  │ Demo prep: Judge Mode, testing, documentation, submission
```

---

## Phase 1 — Foundation (Week 1)

- [x] Project structure and documentation
- [x] FastAPI skeleton with health check
- [x] Next.js skeleton with basic pages
- [ ] Backend: Script upload endpoint (with AES decryption)
- [ ] Frontend: Upload page with client-side AES-256 encryption
- [ ] CI/CD pipeline setup
- [ ] Environment configuration finalized

---

## Phase 2 — Core AI Pipeline (Week 2)

- [ ] Script parser — Arabic & English scene segmentation
- [ ] IBM Granite integration (watsonx.ai client)
- [ ] Storyboard frame generation endpoint
- [ ] Storyboard canvas frontend component
- [ ] Basic budget estimator model

---

## Phase 3 — Security & Polish (Week 3)

- [ ] Client-side AES-256-GCM encryption (WebCrypto)
- [ ] C2PA-inspired watermarking service
- [ ] Motion animatic export (MP4/GIF)
- [ ] RTL Arabic UI refinement
- [ ] Error handling and loading states throughout

---

## Phase 4 — Demo Preparation (Week 4)

- [ ] Live Judge Mode dashboard
- [ ] End-to-end demo flow: upload → storyboard → animatic → budget
- [ ] Performance testing and optimization
- [ ] Final documentation update
- [ ] IBM Bob session logs complete
- [ ] Demo video / slides prepared
- [ ] Submission

---

## Key Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Project structure complete | 2026-07-09 | 🟡 In Progress |
| Script upload + parsing working | 2026-07-13 | ⬜ Pending |
| Granite storyboard generation working | 2026-07-20 | ⬜ Pending |
| Encryption + watermarking complete | 2026-07-25 | ⬜ Pending |
| Animatic export working | 2026-07-27 | ⬜ Pending |
| Demo-ready (end-to-end) | 2026-07-30 | ⬜ Pending |
| **Final submission** | **2026-07-31** | ⬜ Pending |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Granite API latency > 15s | Medium | High | Implement async polling + progress indicators |
| Arabic NLP accuracy | Medium | High | Use Granite's native Arabic support; test early |
| watsonx.ai credit exhaustion | Low | High | Efficient prompt design; cache results |
| AES key management complexity | Low | Medium | Use well-tested WebCrypto patterns |
| Time pressure on animatic | High | Medium | Treat as stretch goal if time-constrained |
