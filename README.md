# Silent Witness — Testimony Consistency Reconstructor
### Capstone Project Proposal & System Design Document

---

## 1. Executive Summary

Silent Witness is a system that ingests multiple free-text eyewitness statements describing the same real-world incident (a road accident, a robbery, a fire, etc.), extracts the factual claims each witness makes (who, what, where, when), reconstructs those claims onto a shared timeline and map, and automatically flags where witnesses **agree** and where they **contradict** each other — without ever judging who is telling the truth. It is built for journalists and legal reviewers who currently do this cross-referencing by hand on whiteboards and spreadsheets. The system deliberately stays in an evidentiary, non-adjudicative role: it surfaces structured, traceable discrepancies for a human expert to interpret, rather than scoring credibility itself.

---

## 2. Purpose & Scope

### 2.1 Problem Statement
When multiple people witness the same event, their accounts inevitably diverge — in detail, in confidence, in vantage point. Today, reconciling these accounts (for a journalist building a story or a legal reviewer building a case) is a manual process: printing statements, highlighting claims, and manually cross-referencing them on a whiteboard or spreadsheet. This is slow, error-prone, and does not scale past a handful of statements.

### 2.2 Purpose
Silent Witness automates the *extraction and comparison* layer of this process. It does not replace the human reviewer's judgment — it gives them a structured, visual, and traceable representation of exactly where accounts align and where they conflict, so their own review time goes toward interpretation rather than manual cross-referencing.

### 2.3 Target Users
- Investigative journalists cross-referencing multiple sources for a story.
- Legal reviewers/paralegals preparing witness statement comparisons for a case.
- Insurance claim reviewers reconciling multiple accounts of an accident (a strong secondary use case worth mentioning to a supervisor as evidence of real-world applicability).

### 2.4 In-Scope (MVP)
- Text-based witness statement ingestion (typed or pasted; bulk upload via CSV/JSON).
- Entity, event, time, and location extraction from statements.
- Cross-witness claim alignment and contradiction/agreement detection.
- Timeline and map visualization of the reconstructed incident.
- Export of a consolidated findings report.
- Coverage limited to three incident categories at MVP stage: road accidents, robberies/assaults, fires — chosen because they have well-defined entity types (vehicles, people, locations) and clear temporal sequences, making them tractable to model well in the available time.

### 2.5 Explicitly Out-of-Scope
- **No credibility or deception scoring.** The system never labels a witness as lying or reliable — only surfaces factual (in)consistency. This is a deliberate ethical boundary, not a limitation to apologize for.
- No audio/video statement ingestion (transcription could be a documented future extension, not part of the MVP).
- No real-time/live incident monitoring — the system operates on statements collected after the fact.
- No legal-admissibility claims — the tool is a review aid, not a certified evidentiary instrument.

---

## 3. Unique Selling Points (USPs)

1. **Non-adjudicative by design.** The system never decides who is lying — a deliberate, defensible ethical stance that differentiates it from "AI lie detector" framings and avoids the liability and bias risks that come with credibility scoring.
2. **Full traceability.** Every contradiction or agreement the system flags links back to the *exact source sentence* in the *exact statement* it came from — critical for any legal or journalistic use where "the AI said so" is never an acceptable justification on its own.
3. **Unified spatio-temporal view.** Combines a timeline *and* a map in one interface — the two dimensions (when, where) that manual whiteboard methods struggle to reconcile simultaneously.
4. **Reproducible synthetic evaluation methodology.** Real-world datasets with multiple witnesses describing the same incident are scarce and often legally restricted. Silent Witness is evaluated against a purpose-built synthetic dataset with full ground truth (see Section 10), a methodology that is itself a defensible contribution given the well-documented scarcity of real multi-witness corpora.
5. **Modular, swappable detection pipeline.** Contradiction detection combines rule-based comparison (for structured attributes like color, plate fragments) with embedding/NLI-based semantic comparison (for claims phrased differently) — each module can be improved independently without touching the rest of the pipeline.

---

## 4. System Overview

At a high level, Silent Witness is a five-stage pipeline:

1. **Ingestion** — witness statements are submitted (individually or in bulk) and associated with a single incident.
2. **Extraction** — each statement is run through an NLP pipeline that pulls out named entities, temporal expressions (normalized to timestamps), spatial references (resolved to coordinates where possible), and event/action tuples (subject–action–object, with time and location context).
3. **Alignment** — extracted claims from different witnesses that refer to the same underlying entity or event are clustered together (e.g., "the red sedan" and "the car" across two statements, if context supports it being the same vehicle).
4. **Contradiction & Agreement Detection** — aligned claim clusters are compared pairwise; mismatches (color, direction, time, location, or even whether an event occurred at all) are flagged as contradictions, and matching claims across ≥2 witnesses are flagged as corroborations.
5. **Visualization** — the reconstructed incident is rendered as a shared timeline and map, with every claim attributed to its witness and every contradiction/agreement clickable back to source text.

---

## 5. Proposed System Architecture

Silent Witness is proposed as a **three-tier, service-separated architecture** rather than a single monolithic backend — this is deliberate, and directly serves the scalability requirements in Section 9.

**Components:**
- **Frontend (React SPA):** statement entry/upload, interactive timeline (custom or library-based, e.g. `vis-timeline`), interactive map (Leaflet + OpenStreetMap), contradiction/agreement panel, report export trigger.
- **Web/API Backend:** handles authentication, incident and statement CRUD, request orchestration, and serves the frontend. Lightweight, I/O-bound.
- **ML/NLP Service:** a separate, independently deployable service that performs all NLP extraction, claim alignment, and contradiction detection. Compute-bound, and the component most likely to need scaling or model upgrades over time.
- **Task Queue (Celery + Redis):** extraction and detection jobs are dispatched asynchronously from the web backend to the ML service, so statement submission never blocks on NLP processing time.
- **Database:** a graph database (Neo4j recommended — see Section 11) storing entities, events, claims, witnesses, and their relationships, since the domain is natively graph-shaped (who said what, about what, linked to whom).
- **External integrations:** a geocoding service (Nominatim/OpenStreetMap) to resolve place-name mentions to coordinates.

*(A full boxes-and-arrows version of this architecture is described separately in the accompanying diagram-description file, ready to feed into a diagramming tool.)*

---

## 6. Functional Requirements

| ID | Requirement | Priority |
|----|---|---|
| FR1 | System shall allow ingestion of free-text witness statements, individually or via bulk CSV/JSON upload, associated with a single incident. | Must |
| FR2 | System shall extract named entities (people, vehicles, objects, locations) from each statement. | Must |
| FR3 | System shall extract and normalize temporal expressions (absolute or relative) from each statement. | Must |
| FR4 | System shall extract spatial references and resolve them to coordinates where possible. | Must |
| FR5 | System shall extract event/action tuples (subject–action–object with time/location context) per statement. | Must |
| FR6 | System shall align claims from different witnesses referring to the same entity or event. | Must |
| FR7 | System shall detect contradictions between aligned claims (attribute, spatial, temporal, existence, or motion/direction mismatches). | Must |
| FR8 | System shall detect corroborations where ≥2 witnesses agree on a claim. | Must |
| FR9 | System shall render a unified timeline of all witness claims with contradiction/agreement markers. | Must |
| FR10 | System shall render a map of spatial claims with witness attribution. | Must |
| FR11 | System shall allow a reviewer to click any flagged item and see the exact source statement text it came from. | Must |
| FR12 | System shall allow export of a consolidated findings report (PDF/CSV). | Should |
| FR13 | System shall support incrementally adding new statements to an existing incident without full pipeline re-run. | Could |

---

## 7. Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|---|---|---|
| NFR1 | Performance | Statement extraction latency | < 5s per ~200-word statement |
| NFR2 | Scalability | ML service scalable independently of web backend | Horizontal scaling via separate deployable service |
| NFR3 | Accuracy | Extraction & contradiction-detection quality | ≥ 0.80 F1 against synthetic ground truth (MVP bar) |
| NFR4 | Usability | Non-technical reviewers can use timeline/map without training | Usability walkthrough with 2–3 non-team testers |
| NFR5 | Security | Witness statement data access control | Role-based auth (reviewer/admin), encrypted at rest |
| NFR6 | Explainability | Every flagged item traceable to exact source text | 100% traceability (hard requirement, not a target) |
| NFR7 | Extensibility | New incident types addable without core rework | Pluggable entity/event ontology per incident category |
| NFR8 | Maintainability | Pipeline stages independently testable | Unit tests per stage (extraction, alignment, detection) |

---

## 8. Core Workflows

**Workflow 1 — Statement Ingestion & Extraction**
Reviewer submits a statement → Web backend stores it and enqueues an extraction job → ML service performs NER, temporal/spatial extraction, and event-tuple extraction → structured claims are written back to the database → reviewer sees the statement marked "processed."

**Workflow 2 — Cross-Witness Alignment & Detection**
Triggered after each new statement (or on-demand) → ML service pulls all claims for the incident → aligns claims referring to the same entity/event across witnesses → runs contradiction and corroboration detection on aligned clusters → results (with source-span references) are written to the database.

**Workflow 3 — Reviewer Exploration & Export**
Reviewer opens an incident → frontend requests timeline and map data from the web backend → reviewer interacts with markers, drilling into source statements for any contradiction/agreement → reviewer triggers export of a consolidated report.

*(Sequence/swimlane versions of these workflows are described separately in the accompanying diagram-description file.)*

---

## 9. Scalability Strategy

- **Service separation:** the ML/NLP service is deployed independently from the web backend, so it can be scaled horizontally (more instances, bigger models, GPU-backed inference later) without touching the web tier — this is the core scalability decision for the whole system.
- **Asynchronous processing:** extraction and detection jobs run through a task queue (Celery + Redis) so statement submission is never blocked on NLP latency, and job throughput can be scaled by adding worker instances.
- **Immutable statement caching:** once a statement is extracted, its structured claims are cached — re-processing is only needed if the extraction model itself is upgraded.
- **Graph database for relational queries at scale:** spatio-temporal cross-referencing queries (this entity, across these witnesses, in this time window) are natively efficient in a graph database as incident size grows.
- **Containerization:** each component (frontend, web backend, ML service, DB, Redis) is Dockerized; Docker Compose is sufficient for the capstone demo, with Kubernetes noted as a documented future step rather than an MVP requirement.

---

## 10. Proposed Dataset

### 10.1 Synthetic Dataset (primary)
Given the near-total absence of public datasets containing multiple witnesses describing the *same* incident with comparable spatio-temporal claims, the primary dataset is purpose-built:
- **Event ground truth:** ~20–25 staged incidents (accident/robbery/fire), each with a structured timeline of sub-events (timestamp, location, action, entities involved) and an entity registry (people, vehicles, objects).
- **Witness perception profiles:** 3–5 witnesses per incident, each with a vantage point (partial visibility), a reliability map (which specific attributes they misremember and how), and a confidence level per claim.
- **Generated statements:** natural first-person text generated from each witness's ground truth + perception profile, written with realistic hedging and imperfect recall.
- **Auto-generated labels:** because both the true event and each witness's perception profile are known, contradiction and agreement labels are computed directly by diffing perception profiles — no manual annotation pass required.

### 10.2 Real-World / Actual Dataset Sources (secondary validation)
To avoid an all-synthetic evaluation story (a supervisor is likely to ask about this), a small real-world validation set is recommended:
- **Multi-source news coverage:** for a handful of real, publicly reported incidents, different news outlets quote different eyewitnesses — these can be manually compiled (5–10 incidents) as a lightweight, genuinely real validation set.
- **MIND dataset (academic, stretch goal):** a February 2025 research dataset ("Incongruence Identification in Eyewitness Testimony," arXiv 2502.05650) built for near-identical purposes — 389 statements across 149 events with annotated contradictions. No confirmed public download was found; contacting the authors is worth doing early, in parallel, but should not block the project timeline.
- **Note on the "Echoes of Testimonies" dataset:** this was considered and ruled out — it is ICTY witness-wellbeing survey data (psychological/socio-economic impact of testifying), not multiple accounts of the same incident, and is worth mentioning briefly to a supervisor as evidence of due diligence in dataset selection.

### 10.3 Evaluation Strategy
Synthetic data (with full ground truth) is used for development, tuning, and quantitative evaluation (precision/recall/F1). The small real-world set is used as a qualitative validation and demo showcase, to demonstrate the system isn't only tuned to its own synthetic distribution.

---

## 11. Technology Stack

| Layer | Technology | Justification |
|---|---|---|
| Frontend | React, Tailwind CSS | Team's existing frontend strength |
| Timeline UI | `vis-timeline` or custom D3 component | Interactive, attributable timeline rendering |
| Map UI | Leaflet + OpenStreetMap tiles | Free, no API key/cost management needed |
| Web/API Backend | FastAPI (Python) or Node.js/Express | Lightweight, I/O-bound service layer |
| ML/NLP Service | Python, FastAPI | Isolated compute-bound service |
| NER & parsing | spaCy | Fast, production-grade entity/dependency parsing |
| Event/relation extraction | Fine-tuned transformer (Hugging Face) | Higher accuracy than rule-based extraction alone |
| Temporal normalization | `dateparser` / SUTime-style rules | Converts relative time phrases to absolute timestamps |
| Semantic similarity | `sentence-transformers` | Embedding-based claim alignment across paraphrased text |
| Contradiction detection | Rule-based comparator + NLI model (e.g. `roberta-large-mnli`) | Hybrid: structured attributes rule-checked, free-text semantically checked |
| Graph construction | `networkx` (in-pipeline), Neo4j (persisted) | Native fit for entity/event/witness relationships |
| Task queue | Celery + Redis | Async job processing, independent scaling |
| Database | Neo4j (primary) or PostgreSQL + PostGIS (fallback) | Graph-native queries vs. team familiarity trade-off |
| Geocoding | Nominatim (OpenStreetMap) | Free, no key management |
| Deployment | Docker Compose, GitHub Actions CI | Reproducible multi-service deployment for a capstone demo |

---

## 12. API Integration Specification

### 12.1 Internal REST API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/incidents` | Create a new incident |
| POST | `/incidents/{id}/statements` | Submit a witness statement (enqueues extraction job) |
| GET | `/jobs/{job_id}` | Poll async extraction/detection job status |
| GET | `/incidents/{id}/timeline` | Retrieve consolidated timeline data |
| GET | `/incidents/{id}/map` | Retrieve consolidated spatial data |
| GET | `/incidents/{id}/contradictions` | Retrieve flagged contradictions with source spans |
| GET | `/incidents/{id}/agreements` | Retrieve flagged corroborations with source spans |
| POST | `/incidents/{id}/export` | Trigger PDF/CSV report export |

Auth: JWT-based, with `reviewer` and `admin` roles.

### 12.2 External Integrations
- **Geocoding:** Nominatim (OpenStreetMap) — resolves extracted place-name text to coordinates.
- **Map tiles:** OpenStreetMap tile server via Leaflet.
- **Optional LLM API (enhancement, not MVP-required):** a general-purpose LLM API can supplement rule-based extraction for particularly ambiguous phrasing, and is also the mechanism used to *generate* the synthetic dataset statements (Section 10.1).

---

## 13. Project Roadmap

| Phase | Focus | Key Deliverables | Suggested Duration |
|---|---|---|---|
| 1 | Dataset & ontology design | Synthetic generation pipeline, entity/event schema, auto-labeling script | 2 weeks |
| 2 | NLP extraction module | NER, temporal, spatial, event-tuple extraction | 2–3 weeks |
| 3 | Alignment & contradiction engine | Claim alignment, rule-based + NLI hybrid detection | 2–3 weeks |
| 4 | Backend & database integration | Web API, ML service, task queue, graph DB schema | 2 weeks |
| 5 | Frontend | Timeline & map UI, contradiction panel, export | 2–3 weeks |
| 6 | Integration & evaluation | End-to-end testing, metrics against synthetic ground truth, real-world validation set | 1–2 weeks |
| 7 | Documentation & defense prep | Final report, demo script, slide deck | 1 week |

*(Durations are placeholders — adjust to your actual semester calendar and team size.)*

---

## 14. Success Metrics / Evaluation Criteria

- Extraction accuracy (entity/temporal/spatial) against synthetic ground truth.
- Contradiction/agreement detection precision, recall, and F1 against synthetic ground truth.
- 100% traceability of flagged items to source text (hard requirement, not a percentage target).
- Qualitative reviewer usability feedback on the timeline/map interface.
- Successful end-to-end demo on at least one real-world (non-synthetic) incident.

---

## 15. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Claim alignment across witnesses is harder than expected (same entity described very differently) | High — undermines core contradiction detection | Start with rule-based + embedding hybrid; fall back to simpler heuristic alignment if needed for MVP |
| Real-world validation set is too small to be convincing | Medium | Be upfront with supervisor about synthetic-primary methodology and its rationale (Section 10.3) |
| MIND dataset authors don't respond / dataset unavailable | Low (already treated as stretch, not a dependency) | Proceed entirely on synthetic + manually compiled real-world set |
| Two-service architecture adds integration overhead the team underestimates | Medium | Define the API contract (Section 12.1) early, before either service is fully built |
| Scope creep toward "credibility scoring" (a supervisor or team member suggests it) | High — ethical and technical risk | Keep the non-adjudicative stance explicit in every project artifact (Section 2.5, 3) |

---

## 16. Glossary

- **NER (Named Entity Recognition):** identifying entities (people, vehicles, locations) in text.
- **NLI (Natural Language Inference):** determining whether one statement entails, contradicts, or is neutral to another.
- **PostGIS:** a spatial extension for PostgreSQL enabling geographic queries.
- **Claim alignment:** matching statements from different witnesses that refer to the same underlying entity or event.

---

## 17. References
- Incongruence Identification in Eyewitness Testimony (MIND dataset), arXiv:2502.05650.
- "Echoes of Testimonies" dataset (ICTY witness-wellbeing survey) — considered and ruled out as a poor fit for this project's requirements (see Section 10.2).
