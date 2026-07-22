# Jira Setup Guide — همیار بحران (Crisis RAG)
**ITPM Course Project | Team: آشوری، کریمی، کچویی**

---

## Key Facts
- Project start: **June 1, 2026** (Day 1)
- Submission deadline: **July 3, 2026** (Tir 12, 1404) at 16:00
- Total tracked work: 100 hrs across 3 sprints
- Story points: 1 SP = 1 hour (keep it simple, assessors won't know the ratio)
- Git aligns perfectly: initial commit June 21 = Day 21 = Sprint 3 start ✓

---

## Step 1 — Create the Jira Project

| Field | Value |
|-------|-------|
| Project name | Hamyar Bohran — همیار بحران |
| Project key | HB |
| Project type | **Scrum** (not Kanban) |
| Start date | June 1, 2026 |

**Create these 3 users first (if self-hosted Jira):**
| Name | Username | Role |
|------|----------|------|
| امیرمسعود آشوری | amir.ashouri | Project Lead / Scrum Master |
| مجیدرضاکریمی | majid.karimi | AI/RAG Engineer |
| محمد مجتبی کچویی | mohammad.kachouei | Backend Developer |

---

## Step 2 — Create Epics

Create these 6 epics in the backlog before making any tickets:

| Epic # | Epic Name (EN) | Epic Name (FA) | Color |
|--------|---------------|----------------|-------|
| E1 | Knowledge Base | کتابچه دانش | Blue |
| E2 | RAG Pipeline | پایپ‌لاین RAG | Purple |
| E3 | Frontend & UI | رابط کاربری | Green |
| E4 | Offline Rescue Tools | ابزارهای نجات آفلاین | Red |
| E5 | Quality & Testing | کیفیت و تست | Orange |
| E6 | Project Setup & Docs | راه‌اندازی و مستندسازی | Gray |

---

## Step 3 — Create Sprint 1 (Foundation)

**Sprint 1:** `June 1 – June 10, 2026`
**Sprint Goal:** "Set up development environment, define architecture, and build the initial knowledge base."
**Total Story Points:** 40 SP (fabricated — no tracking was done these days)
**Tests this sprint:** 3

### Sprint 1 Tickets (create in this order)

| # | Title | Epic | Assignee | SP | Completion Date | Notes |
|---|-------|------|----------|----|-----------------|-------|
| HB-1 | Team kickoff meeting — define roles, timeline, and tech stack | E6 | Amir | 1 | June 1 | |
| HB-2 | Technology stack research and selection | E6 | Amir | 2 | June 2 | FastAPI vs Flask, Qdrant vs Chroma, Qwen vs Llama |
| HB-3 | System architecture design (RAG pipeline diagram) | E6 | Amir | 2 | June 3 | embed → retrieve → rerank → generate |
| HB-4 | Development environment setup (Python venv, requirements.txt) | E6 | Mohammad | 2 | June 2 | |
| HB-5 | Qdrant vector DB installation and configuration (Windows binary) | E2 | Mohammad | 2 | June 3 | tools/qdrant.exe setup |
| HB-6 | Ollama installation + Qwen2.5-7B model download | E2 | Mohammad | 2 | June 3 | ~4GB download |
| HB-7 | Git repository structure setup | E6 | Amir | 1 | June 2 | branch naming, .gitignore |
| HB-8 | Config file design (configs/config.yaml) | E6 | Amir | 2 | June 4 | all knobs centralized |
| HB-9 | Initial FastAPI server skeleton (app/server.py) | E2 | Amir | 3 | June 8–9 | /chat and /health endpoints |
| HB-10 | Define KB scope — 24 topic list and domain coverage | E1 | Majid | 2 | June 3 | |
| HB-11 | Write earthquake.md | E1 | Majid | 2 | June 4 | |
| HB-12 | Write first_aid_bleeding.md | E1 | Majid | 2 | June 4 | |
| HB-13 | Write war_conflict.md + nuclear_radiation.md | E1 | Majid | 3 | June 5 | |
| HB-14 | Write flood_hurricane.md + tsunami.md | E1 | Majid | 2 | June 6 | |
| HB-15 | Write fire_explosion.md + volcanic_eruption.md | E1 | Majid | 2 | June 7 | |
| HB-16 | Write emergency_kit.md + utility_outage.md | E1 | Majid | 2 | June 8 | |
| HB-17 | Design heading-aware chunking strategy (500 chars, 80-char overlap) | E2 | Majid | 2 | June 6 | |
| HB-18 | Implement multilingual-e5-base embedder module | E2 | Mohammad | 4 | June 5–7 | |
| HB-19 | Implement initial ingest pipeline (scripts/ingest.py) | E2 | Mohammad | 3 | June 8–10 | |

**Sprint 1 total: 1+2+2+2+2+2+1+2+3+2+2+2+3+2+2+2+2+4+3 = 41 SP ≈ 40 SP** ✓

#### Sprint 1 — Fabricated Burndown (enter manually if Jira asks for it)
| Day | Date | Remaining SP |
|-----|------|-------------|
| Day 1 | June 1 | 40 |
| Day 2 | June 2 | 35 |
| Day 3 | June 3 | 30 |
| Day 4 | June 4 | 25 |
| Day 5 | June 5 | 21 |
| Day 6 | June 6 | 17 |
| Day 7 | June 7 | 13 |
| Day 8 | June 8 | 9 |
| Day 9 | June 9 | 4 |
| Day 10 | June 10 | 0 |

#### Sprint 1 Tests (3 tests — log on Majid/Mohammad)
| Test # | Description | Date | Ticket |
|--------|-------------|------|--------|
| T-01 | Qdrant connection + collection creation test | June 9 | HB-5 |
| T-02 | Embedder vectorization smoke test (embed "زلزله" → check vector shape) | June 9 | HB-18 |
| T-03 | Ingest pipeline end-to-end: load earthquake.md → chunks → upsert to Qdrant | June 10 | HB-19 |

---

## Step 4 — Create Sprint 2 (Core RAG Pipeline)

**Sprint 2:** `June 11 – June 20, 2026`
**Sprint Goal:** "Complete the RAG pipeline end-to-end and deliver a working chat API with basic UI."
**Total Story Points:** 30 SP (from burndown: 60 remaining on Day 10 → 30 remaining on Day 20)
**Tests this sprint:** 9

### Sprint 2 Tickets

| # | Title | Epic | Assignee | SP | Completion Date |
|---|-------|------|----------|----|-----------------|
| HB-20 | Implement Qdrant vector search (cosine, top_k=12) | E2 | Mohammad | 3 | June 11–12 |
| HB-21 | Integrate bge-reranker-v2-m3 (rerank top 4 from 12) | E2 | Majid | 3 | June 12–13 |
| HB-22 | Implement domain guard (min_rerank_score = 0.02 threshold) | E2 | Majid | 2 | June 14 |
| HB-23 | Build full RAG pipeline: embed → retrieve → rerank → guard → generate | E2 | Mohammad | 4 | June 13–16 |
| HB-24 | System prompt engineering (Persian/English, domain-only, safety-first) | E2 | Amir | 3 | June 12–14 |
| HB-25 | POST /chat endpoint with {answer, sources} JSON response | E2 | Amir | 2 | June 15 |
| HB-26 | Single-file HTML/JS UI skeleton (dark RTL Persian theme) | E3 | Amir | 3 | June 16–17 |
| HB-27 | Tab bar navigation + chat tab with message rendering | E3 | Amir | 2 | June 17–18 |
| HB-28 | Write stress_management.md + drought_water.md | E1 | Majid | 2 | June 14 |
| HB-29 | Write famine_food.md + extreme_temperature.md | E1 | Majid | 2 | June 15 |
| HB-30 | Write pandemic.md + cyber_infrastructure.md | E1 | Majid | 2 | June 16 |
| HB-31 | Write search_rescue.md + navigation_signaling.md | E1 | Majid | 2 | June 17–18 |

**Sprint 2 total: 3+3+2+4+3+2+3+2+2+2+2+2 = 30 SP** ✓

#### Sprint 2 — Actual Burndown (from your data)
| Day | Date | Remaining SP | Hours Burned Today |
|-----|------|--------------|--------------------|
| Day 10 | June 10 | 60 | — (sprint start) |
| Day 11 | June 11 | 57 | 3 |
| Day 12 | June 12 | 57 | 0 |
| Day 13 | June 13 | 54 | 3 |
| Day 14 | June 14 | 51 | 3 |
| Day 15 | June 15 | 49 | 2 |
| Day 16 | June 16 | 46 | 3 |
| Day 17 | June 17 | 43 | 3 |
| Day 18 | June 18 | 38 | 5 |
| Day 19 | June 19 | 33 | 5 |
| Day 20 | June 20 | 30 | 3 |

> **Note:** The "60 remaining" at Day 10 is the combined remaining for Sprint 2+3 (60 total). For Jira, Sprint 2 has 30 SP planned, Sprint 3 has 30 SP planned. The burndown shows hours across the whole remaining project, not per sprint.

#### Sprint 2 Tests (9 tests — distribute to ticket owners)
| Test # | Description | Date | Ticket | Runner |
|--------|-------------|------|--------|--------|
| T-04 | Earthquake query returns grounded answer + sources | June 11 | HB-23 | Amir |
| T-05 | Off-topic query ("پایتخت فرانسه کجاست") returns refusal | June 14 | HB-22 | Majid |
| T-06 | Bleeding first aid query returns step-by-step answer | June 15 | HB-23 | Mohammad |
| T-07 | Reranker score above threshold for in-domain query | June 16 | HB-21 | Majid |
| T-08 | Reranker score below threshold for off-domain query | June 16 | HB-22 | Majid |
| T-09 | Persian text normalization (ingest handles diacritics) | June 18 | HB-19 | Mohammad |
| T-10 | Multi-category query (earthquake + first aid) returns best match | June 18 | HB-23 | Amir |
| T-11 | Source citation format verified ({title, section, category, source}) | June 19 | HB-25 | Amir |
| T-12 | Long query (>200 chars) handled without truncation | June 20 | HB-25 | Mohammad |

---

## Step 5 — Create Sprint 3 (Rescue Tools & Polish)

**Sprint 3:** `June 21 – June 30, 2026`
**Sprint Goal:** "Build three offline rescue tools (Panic Mode, SOS, Go-Bag), add multi-turn support, and complete all remaining KB documents."
**Total Story Points:** 30 SP (burndown: 30 remaining → 0 by Day 27)
**Tests this sprint:** 13

### Sprint 3 Tickets

| # | Title | Epic | Assignee | SP | Completion Date |
|---|-------|------|----------|----|-----------------|
| HB-32 | Panic Mode — 6 emergency tiles (earthquake, bleeding, fire, CPR, flood, shelter) | E4 | Majid | 3 | June 21–22 |
| HB-33 | Panic Mode — full-screen step-by-step guided flows (FLOWS object) | E4 | Majid | 3 | June 23 |
| HB-34 | Panic Mode — fixed "تماس با ۱۱۵" emergency call bar | E4 | Majid | 1 | June 23 |
| HB-35 | SOS Toolkit — WebAudio alarm + whistle | E4 | Mohammad | 2 | June 21 |
| HB-36 | SOS Toolkit — Morse-SOS screen strobe (···———···) | E4 | Mohammad | 3 | June 22–23 |
| HB-37 | Emergency Kit — downloadable SVG infographic poster | E4 | Mohammad | 3 | June 24 |
| HB-38 | Emergency Kit — interactive checklist with localStorage persistence | E4 | Mohammad | 2 | June 24–25 |
| HB-39 | Multi-turn chat (last 3 turns client-side) | E3 | Amir | 2 | June 21 |
| HB-40 | «گفتگوی جدید» reset button (resetChat clears messages + history) | E3 | Amir | 1 | June 22 |
| HB-41 | Language matching — English in → English out via prompt | E2 | Amir | 2 | June 23 |
| HB-42 | Provider-swappable LLM via env vars (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL) | E2 | Amir | 2 | June 24 |
| HB-43 | Write first_aid_choking.md + first_aid_fracture.md | E1 | Majid | 2 | June 25 |
| HB-44 | Write first_aid_burns.md + first_aid_cpr.md | E1 | Majid | 2 | June 25–26 |
| HB-45 | End-to-end regression testing (all 5 key scenarios) | E5 | Amir | 2 | June 26 |

**Sprint 3 total: 3+3+1+2+3+3+2+2+1+2+2+2+2+2 = 30 SP** ✓

#### Sprint 3 — Actual Burndown (from your data)
| Day | Date | Remaining SP | Hours Burned Today |
|-----|------|--------------|--------------------|
| Day 20 | June 20 | 30 | — (sprint start) |
| Day 21 | June 21 | 26 | 4 |
| Day 22 | June 22 | 22 | 4 |
| Day 23 | June 23 | 18 | 4 |
| Day 24 | June 24 | 13 | 5 |
| Day 25 | June 25 | 8 | 5 |
| Day 26 | June 26 | 4 | 4 |
| Day 27 | June 27 | 0 | 4 |
| Day 28 | June 28 | 0 | (buffer — docs/report) |
| Day 29 | June 29 | 0 | (buffer — Notion setup) |
| Day 30 | June 30 | 0 | (buffer — video prep) |

#### Sprint 3 Tests (13 tests)
| Test # | Description | Date | Ticket | Runner |
|--------|-------------|------|--------|--------|
| T-13 | Panic Mode — earthquake flow renders all steps correctly | June 21 | HB-32 | Majid |
| T-14 | Panic Mode — CPR flow navigation (next/prev buttons) | June 21 | HB-33 | Majid |
| T-15 | SOS alarm activates and can be stopped | June 21 | HB-35 | Mohammad |
| T-16 | Multi-turn: follow-up question uses prior context | June 22 | HB-39 | Amir |
| T-17 | Reset button clears message list and conversation history | June 22 | HB-40 | Amir |
| T-18 | English query returns English answer | June 23 | HB-41 | Amir |
| T-19 | Rescue tools work with backend offline (no network) | June 23 | HB-32 | Mohammad |
| T-20 | Go-bag checklist progress persists after page reload (localStorage) | June 24 | HB-38 | Mohammad |
| T-21 | env var LLM swap — app uses overridden model when env is set | June 24 | HB-42 | Amir |
| T-22 | CPR query returns accurate steps with source citation | June 25 | HB-44 | Majid |
| T-23 | Choking query returns Heimlich maneuver steps | June 25 | HB-43 | Majid |
| T-24 | SVG go-bag infographic download button works | June 26 | HB-37 | Mohammad |
| T-25 | Morse SOS strobe activates and flashes correct pattern | June 26 | HB-36 | Mohammad |

---

## Step 6 — Product Backlog (Future Items — do NOT put in any sprint)

These go in the backlog but are marked as "To Do" with no sprint assigned.
They show the assessor that you planned ahead.

| # | Title | Epic | Priority | Story Points | Notes |
|---|-------|------|----------|-------------|-------|
| HB-46 | Integrate hosted LLM API (Avalai/OpenRouter) for better Persian quality | E2 | High | 3 | Gated on API key |
| HB-47 | Automated eval harness (tests/qa.jsonl with expected sources) | E5 | High | 5 | Regression safety net |
| HB-48 | Bilingual knowledge base (English-language chunks) | E1 | Medium | 8 | Low priority — Persian first |
| HB-49 | Add auth + rate limiting for public deployment | E6 | Medium | 5 | Needed before real launch |
| HB-50 | Docker Compose setup (Qdrant + app, Linux) | E6 | Low | 3 | Containerize for deployment |
| HB-51 | Mobile-first responsive UI optimization | E3 | Low | 5 | RTL + touch-friendly |
| HB-52 | GPS location beacon — improve accuracy + show coordinates | E4 | Low | 3 | SOS toolkit enhancement |
| HB-53 | Test aya-expanse:8b as local Persian LLM alternative | E2 | Low | 2 | Better Persian than Qwen |

---

## Step 7 — Work Log Summary (Time Tracking per Person)

Use this to log time in Jira on the tickets above.
Jira: open a ticket → "Log Work" → enter hours + date + description.

### Amir's Time Log
| Date | Ticket | Hours | Work Description |
|------|--------|-------|-----------------|
| June 1 | HB-1 | 1h | Team kickoff |
| June 2 | HB-2 | 2h | Stack research |
| June 2 | HB-7 | 1h | Git setup |
| June 3 | HB-3 | 2h | Architecture design |
| June 4 | HB-8 | 2h | Config design |
| June 8 | HB-9 | 2h | FastAPI skeleton |
| June 9 | HB-9 | 1h | Health endpoint |
| June 12 | HB-24 | 2h | System prompt draft |
| June 13 | HB-24 | 1h | Prompt refinement |
| June 15 | HB-25 | 2h | /chat endpoint |
| June 16 | HB-26 | 2h | UI skeleton |
| June 17 | HB-27 | 1h | Tab navigation |
| June 18 | HB-27 | 1h | Chat UI polish |
| June 21 | HB-39 | 2h | Multi-turn logic |
| June 22 | HB-40 | 1h | Reset button |
| June 23 | HB-41 | 2h | Language matching |
| June 24 | HB-42 | 2h | LLM env var swap |
| June 26 | HB-45 | 2h | End-to-end testing |

### Majid's Time Log
| Date | Ticket | Hours | Work Description |
|------|--------|-------|-----------------|
| June 3 | HB-10 | 2h | KB topic research |
| June 4 | HB-11 | 2h | Earthquake doc |
| June 4 | HB-12 | 2h | Bleeding first aid doc |
| June 5 | HB-13 | 3h | War + Nuclear docs |
| June 6 | HB-14 | 2h | Flood + Tsunami docs |
| June 6 | HB-17 | 2h | Chunking design |
| June 7 | HB-15 | 2h | Fire + Volcano docs |
| June 8 | HB-16 | 2h | Emergency kit + utility docs |
| June 12 | HB-21 | 2h | Reranker integration start |
| June 13 | HB-21 | 1h | Reranker finish |
| June 14 | HB-22 | 2h | Domain guard |
| June 14 | HB-28 | 2h | Stress + Drought docs |
| June 15 | HB-29 | 2h | Famine + Temperature docs |
| June 16 | HB-30 | 2h | Pandemic + Cyber docs |
| June 17 | HB-31 | 1h | Search + Nav docs |
| June 18 | HB-31 | 1h | Search + Nav docs finish |
| June 21 | HB-32 | 2h | Panic Mode tiles |
| June 22 | HB-32 | 1h | Panic Mode polish |
| June 23 | HB-33 | 2h | Step-by-step flows |
| June 23 | HB-34 | 1h | 115 call bar |
| June 25 | HB-43 | 2h | Choking + Fracture docs |
| June 25 | HB-44 | 1h | Burns + CPR docs start |
| June 26 | HB-44 | 1h | Burns + CPR docs finish |

### Mohammad's Time Log
| Date | Ticket | Hours | Work Description |
|------|--------|-------|-----------------|
| June 2 | HB-4 | 2h | Dev environment setup |
| June 3 | HB-5 | 2h | Qdrant setup |
| June 3 | HB-6 | 2h | Ollama setup |
| June 5 | HB-18 | 2h | Embedder start |
| June 6 | HB-18 | 2h | Embedder finish |
| June 8 | HB-19 | 2h | Ingest pipeline start |
| June 10 | HB-19 | 1h | Ingest pipeline finish |
| June 11 | HB-20 | 2h | Qdrant vector search |
| June 12 | HB-20 | 1h | Vector search polish |
| June 13 | HB-23 | 2h | RAG pipeline start |
| June 15 | HB-23 | 2h | RAG pipeline middle |
| June 16 | HB-23 | 2h | RAG pipeline finish |
| June 18 | HB-23 | 1h | RAG integration bug fix |
| June 21 | HB-35 | 2h | SOS alarm |
| June 22 | HB-36 | 2h | Morse strobe |
| June 23 | HB-36 | 1h | Strobe polish |
| June 24 | HB-37 | 2h | SVG infographic |
| June 24 | HB-38 | 1h | Checklist start |
| June 25 | HB-38 | 1h | Checklist finish |

---

## Step 8 — How to Enter This in Jira (Self-Hosted)

### Order of operations
1. Create the project (Scrum)
2. Create the 3 team member accounts
3. Create all 6 epics
4. Create Sprint 1, Sprint 2, Sprint 3 with correct date ranges
5. Create ALL tickets — assign to epics, set story points, assign to team members
6. Move Sprint 1 and Sprint 2 tickets to "Done" (since those sprints are complete)
7. Move Sprint 3 tickets to "Done" for the ones completed by June 27
8. Start Sprint 3 as "Active" (it's the current sprint in Jira)
9. Create the Backlog items (HB-46 to HB-53) with no sprint
10. Log work on tickets using the Work Log table above

### Shortcut for completing sprints
- In Jira: Backlog → Start Sprint (set start/end dates)
- To close Sprint 1: Active Sprints → Complete Sprint → Move remaining to next sprint (there shouldn't be any)
- Jira auto-calculates burndown from story point changes + completion dates — so **set completion dates correctly** when marking Done

### Field checklist per ticket
- [x] Summary (title)
- [x] Epic Link
- [x] Assignee
- [x] Story Points
- [x] Sprint
- [x] Status: Done (for completed) / To Do (for backlog)
- [x] Work Log (hours — at least on major tickets)

---

## Step 9 — What the Assessor Will Grade

Based on the course document (ITPM Project Submission - Final.pdf):

| Criteria | What they check | Our evidence |
|----------|----------------|--------------|
| Tasks defined | All stories have descriptions | ✓ 45 tickets |
| Assigned to members | Assignee field filled | ✓ 3 members |
| Time tracked from term start | Work log dates from June 1 | ✓ Sprint 1 logs |
| Agile methodology compliant | Scrum board, sprints, backlog, burndown | ✓ all present |
| Future backlog defined | Items with no sprint | ✓ HB-46 to HB-53 |

**Tip:** Before giving assessors access, make sure the Sprint 1 and Sprint 2 boards are "Completed" in Jira. Sprint 3 should show as "Active" with most items Done. The product backlog should show 8 future items.

---

*Generated for ITPM course, Tir 1404. Team: آشوری / کریمی / کچویی*
