# Silent Witness — Build Execution Plan
### Order: NLP/ML core → Backend → Frontend → Graph polish → Hardening
### Written as an agent-executable spec (each step is a discrete, testable task)

---

## How to use this file
Each Phase is a self-contained milestone with: **Goal**, **Preconditions**, **Steps** (in execution order), **File/Folder outputs**, and **Definition of Done (DoD)**. Do not start a Phase until the previous Phase's DoD is fully met — the architecture is intentionally sequential (ML core proven correct *before* anything is wired to it, so bugs are never masked by backend/frontend glue code).

Repo root assumed: `silent-witness/`

---

## PHASE 1 — NLP/ML Core (standalone, no backend, no frontend)

### Goal
Build and validate the extraction + alignment + contradiction/agreement detection pipeline as a **pure Python library**, callable from a script or notebook, fully unit-tested against the synthetic dataset — before any API or UI exists. This is the highest-risk, highest-value part of the system; it must be provably correct in isolation first.

### Preconditions
- Python 3.11 environment
- `pip install spacy sentence-transformers transformers torch dateparser networkx pytest`
- `python -m spacy download en_core_web_trf`

### Steps

1. **Scaffold the ML package**
   - Create `ml_core/` with submodules: `extraction/`, `alignment/`, `detection/`, `schema/`, `synthetic/`, `tests/`.
   - Define `schema/models.py`: dataclasses for `Entity`, `TemporalExpression`, `SpatialReference`, `EventTuple` (subject, action, object, time_ref, location_ref, source_span, confidence), `Claim`, `Witness`, `Incident`.
   - Every extracted object must carry a `source_span: (start_char, end_char)` and `source_statement_id` field from the moment it is created — traceability is a hard requirement (NFR6), so bake it into the schema before writing any extraction logic, not after.

2. **Build the synthetic dataset generator first** (Section 10.1 of the proposal)
   - `synthetic/incident_templates.py`: define 3 incident-type schemas (road accident, robbery/assault, fire), each with a ground-truth sub-event timeline (timestamp, location, action, entities).
   - `synthetic/witness_profiles.py`: generate 3–5 witness perception profiles per incident (vantage point, per-attribute reliability/error map, per-claim confidence).
   - `synthetic/statement_generator.py`: turns (ground truth + perception profile) into natural first-person text. Use an LLM call (Claude API or local template+noise) with a strict prompt: realistic hedging, imperfect recall, no meta-commentary.
   - `synthetic/label_generator.py`: diff perception profiles against ground truth to auto-produce contradiction/agreement labels per claim pair. This is your evaluation ground truth — get it right before tuning anything downstream.
   - Generate **20–25 incidents × 3–5 witnesses** → save as `synthetic/generated/*.json`.
   - **Checkpoint:** manually read 5 generated statements. If they don't read like a real human account, fix the generator before proceeding — a bad dataset invalidates every metric downstream.

3. **Entity, temporal, spatial extraction**
   - `extraction/ner.py`: wrap spaCy `en_core_web_trf` for PERSON/VEHICLE(custom)/OBJECT/LOCATION entities. Add a custom spaCy `EntityRuler` for vehicle-attribute patterns (color + make/model regex) since base spaCy won't catch these well.
   - `extraction/temporal.py`: wrap `dateparser` with a preprocessing pass for relative expressions ("about ten minutes before", "right after the crash") — write a small rule table mapping incident-relative phrases to offsets from a detected anchor time.
   - `extraction/spatial.py`: extract location noun phrases, pass to Nominatim (rate-limited, cached) for coordinate resolution; keep a local fallback gazetteer for incident-scene-relative terms ("the crosswalk", "the north corner") that geocoding can't resolve — flag these as `resolved: false` rather than guessing.
   - **Unit tests**: for every extractor, assert against 10 hand-labeled sentences per category, minimum 0.8 F1 per Section 9 NFR3 bar — write these tests before moving to step 4.

4. **Event/action tuple extraction**
   - `extraction/events.py`: fine-tune or prompt a transformer (start with a prompted LLM call for MVP speed, document fine-tuning as a stretch goal) to output subject–action–object tuples with attached time/location refs.
   - Output must validate against the `EventTuple` schema from Step 1 — reject and log any malformed output rather than silently dropping fields.

5. **Claim alignment**
   - `alignment/cluster.py`: for each pair of claims across different witnesses, compute a similarity score combining (a) `sentence-transformers` embedding cosine similarity on the claim text, (b) entity-attribute overlap (same approximate location/time window), (c) event-type match.
   - Cluster claims above a similarity threshold (start at 0.75, tune against synthetic ground truth) using simple agglomerative clustering — do not over-engineer this before you have a baseline number.
   - **Checkpoint:** run against synthetic ground truth, report clustering precision/recall. If alignment F1 < 0.7, fall back to the simpler heuristic in the Risks table (Section 15) before continuing: same entity-type + overlapping time window = aligned, no embedding needed.

6. **Contradiction & agreement detection**
   - `detection/rules.py`: hard-attribute comparator for structured fields (color, plate fragment, count of people, direction of travel) — exact/near-match logic, no ML needed here.
   - `detection/nli.py`: wrap `roberta-large-mnli` for free-text claim pairs that don't reduce to structured attributes — label as `contradiction` / `agreement` / `neutral` (drop neutral).
   - `detection/pipeline.py`: merge rule-based + NLI outputs into a single `DetectionResult` list, each with `claim_ids`, `type` (attribute/spatial/temporal/existence/motion), `verdict`, `confidence`, and full `source_span` lineage back through alignment → extraction → original statement.
   - **This is the core deliverable of Phase 1** — everything else in the project depends on this being trustworthy.

7. **End-to-end evaluation script**
   - `tests/eval_pipeline.py`: run the full pipeline (extraction → alignment → detection) over the entire synthetic dataset, compute precision/recall/F1 against auto-generated labels, dump a metrics report.
   - Iterate on thresholds/prompts until NFR3 (≥0.80 F1) is met on synthetic data.

8. **Real-world validation set (secondary, do in parallel, does not block)**
   - `synthetic/real_world/`: manually compile 5–10 real incidents from multi-outlet news coverage (different outlets quoting different eyewitnesses of the same event). No auto-labels here — spot-check qualitatively only.

### DoD for Phase 1
- [ ] Full pipeline runs end-to-end on a synthetic incident from raw statement text → contradiction/agreement list, with zero backend/frontend code involved.
- [ ] Synthetic eval F1 ≥ 0.80 for extraction and for contradiction/agreement detection.
- [ ] Every output object traces back to an exact `(statement_id, char_start, char_end)`.
- [ ] `pytest ml_core/tests/` passes fully.
- [ ] A `pipeline.run(statements: List[Statement]) -> IncidentResult` function exists as the **single entry point** the backend will call in Phase 2 — this function signature is now frozen.

---

## PHASE 2 — Backend Integration

### Goal
Wrap the frozen Phase 1 `pipeline.run()` entry point in a real, async, persisted, multi-user service — without touching pipeline internals.

### Preconditions
Phase 1 DoD fully met. `pipeline.run()` signature frozen.

### Steps

1. **Database schema (Neo4j)**
   - Nodes: `Incident`, `Witness`, `Statement`, `Entity`, `EventClaim`, `TemporalClaim`, `SpatialClaim`.
   - Relationships: `(Witness)-[:GAVE]->(Statement)`, `(Statement)-[:CONTAINS]->(Claim)`, `(Claim)-[:ALIGNED_WITH]->(Claim)`, `(Claim)-[:CONTRADICTS {type, confidence}]->(Claim)`, `(Claim)-[:CORROBORATES]->(Claim)`.
   - Write `db/schema.cypher` with constraints (unique incident IDs, unique statement IDs) and indexes on `Incident.id`, `Statement.id`.

2. **Web/API service (FastAPI)**
   - Scaffold `api/main.py`, `api/routers/{incidents,statements,jobs,timeline,map,export}.py`.
   - Implement all endpoints from Section 12.1 exactly as specified: `POST /incidents`, `POST /incidents/{id}/statements`, `GET /jobs/{job_id}`, `GET /incidents/{id}/timeline`, `GET /incidents/{id}/map`, `GET /incidents/{id}/contradictions`, `GET /incidents/{id}/agreements`, `POST /incidents/{id}/export`.
   - JWT auth middleware with `reviewer`/`admin` roles (NFR5). No endpoint reachable without a valid token.

3. **Async task queue**
   - Stand up Celery + Redis. `POST /incidents/{id}/statements` enqueues a `run_extraction_and_detection` task instead of blocking — statement submission must return immediately (NFR1, NFR2).
   - Task calls the frozen `pipeline.run()` from Phase 1, writes results into Neo4j via the schema in Step 1.
   - `GET /jobs/{job_id}` polls Celery task state and returns `pending | processing | done | failed`.

4. **ML service isolation**
   - Deploy the Phase 1 package as its own FastAPI micro-service (`ml_service/`) with a single internal endpoint `POST /process` that the Celery worker calls — this is what makes the ML tier independently scalable (Section 5, Section 9). Do not import `ml_core` directly into the web backend process.

5. **Geocoding integration**
   - Wire Nominatim calls (with local caching layer — a simple Redis or SQLite cache keyed on place-name string) into the extraction stage, respecting Nominatim's rate limits.

6. **Incremental statement addition (FR13, "Could" priority — do only after everything else works)**
   - When a new statement is added to an existing incident, only re-run alignment/detection for claims touching the new statement's entities/timeframe, not the whole incident — implement this last, and only if time allows.

7. **Integration tests**
   - `api/tests/test_integration.py`: submit a full synthetic incident through the real API (statement POSTs → poll job → fetch timeline/map/contradictions), assert results match the Phase 1 standalone pipeline output for the same input. This is the regression check that proves the wiring didn't break anything.

### DoD for Phase 2
- [ ] Every endpoint in Section 12.1 implemented and auth-protected.
- [ ] A statement submitted via API produces identical contradiction/agreement results to running `pipeline.run()` directly (Phase 1 parity test passes).
- [ ] Statement submission returns in <200ms regardless of NLP processing time (async confirmed).
- [ ] ML service can be stopped/restarted/scaled independently of the web backend without data loss (job stays queued in Redis).
- [ ] `docker-compose up` brings up all five services (frontend placeholder, web backend, ML service, Neo4j, Redis) cleanly.

---

## PHASE 3 — Frontend (Core UI, functional but not final visual polish)

### Goal
Build a working React interface covering ingestion, timeline, map, and contradiction panel — functionally complete, wired to the real Phase 2 API, before spending time on visual refinement.

### Preconditions
Phase 2 DoD met; API is stable and documented (OpenAPI/Swagger from FastAPI is sufficient documentation).

### Steps

1. **Scaffold**
   - `frontend/`: React + Vite + Tailwind CSS. Set up routing: `/login`, `/incidents`, `/incidents/:id`.
   - API client layer: `frontend/src/api/client.ts` with typed wrappers for every Section 12.1 endpoint, JWT token attached automatically.

2. **Statement ingestion view**
   - Form for single statement entry (witness name, free text) + bulk CSV/JSON upload (FR1).
   - Show per-statement processing status by polling `GET /jobs/{job_id}` (pending/processing/done), so the reviewer always knows what's still being extracted.

3. **Timeline view**
   - Integrate `vis-timeline` (fastest path to FR9) bound to `GET /incidents/{id}/timeline`.
   - Each timeline item colored/badged by witness; contradiction pairs get a distinct marker style (defer exact visual language to Phase 4 — for now, just make contradictions visibly different from agreements and from uncontested claims).

4. **Map view**
   - Leaflet + OpenStreetMap tiles bound to `GET /incidents/{id}/map` (FR10). Markers per spatial claim, colored by witness, with a toggle to overlay only contradicted or only corroborated spatial claims.

5. **Contradiction/Agreement panel**
   - List view of `GET /incidents/{id}/contradictions` and `/agreements`, each entry showing the claim pair, mismatch type, and confidence.
   - Clicking any entry opens a side panel showing the **exact source sentence highlighted** in the full original statement text for each witness involved (FR11 — this is a non-negotiable requirement, not a nice-to-have; build it in Phase 3, not later).

6. **Export**
   - Button triggers `POST /incidents/{id}/export`, polls for completion, offers PDF/CSV download (FR12).

7. **Usability pass**
   - Run the NFR4 walkthrough: have 2–3 people unfamiliar with the project use the timeline/map without guidance, note every point of confusion, fix the worst 3 before Phase 4.

### DoD for Phase 3
- [ ] A reviewer can go from "paste 5 statements" to "see contradictions with clickable source text" entirely through the UI, no API calls made manually.
- [ ] Every FR in Section 6 marked "Must" is demonstrably working end-to-end through the browser.
- [ ] Usability walkthrough completed with at least 2 non-team testers; top issues logged and fixed.

---

## PHASE 4 — Graph & Visualization Final Polish ("the graph should be perfectly framed")

### Goal
This is the phase where the timeline + map stop being "functional" and become the system's signature interface — the unified spatio-temporal view is USP #3 (Section 3) and deserves dedicated polish time rather than being an afterthought bolted onto Phase 3.

### Preconditions
Phase 3 DoD met.

### Steps

1. **Visual language pass**
   - Define one consistent color-per-witness scheme used identically across timeline, map, and contradiction panel (a witness is always the same color everywhere).
   - Define a single iconography for verdict types: contradiction (attribute/spatial/temporal/existence/motion) vs corroboration — used consistently on both timeline and map so a reviewer can pattern-match across the two views without re-learning symbols.

2. **Timeline ↔ Map linkage**
   - Selecting a claim on the timeline highlights its corresponding marker on the map, and vice versa (this is what makes the "unified" in USP #3 real rather than nominal — two independently pretty widgets are not a unified view).
   - Add a shared time-scrubber: dragging it filters both the timeline and the map to claims within that window simultaneously.

3. **Graph density handling**
   - For incidents with many statements, add clustering/zoom behavior on the map (marker clustering) and horizontal zoom/pan with claim-density minimap on the timeline, so the view stays legible past ~10 witnesses.

4. **Contradiction emphasis**
   - Visually de-emphasize (lower opacity) claims with no contradictions/agreements so the reviewer's eye is drawn first to the parts of the incident that actually need human judgment — this directly serves the project's stated purpose (Section 2.2: review time should go to interpretation, not searching).

5. **Source-trace interaction polish**
   - Smooth transition/scroll-to when jumping from a flagged item to its source sentence (FR11), with the matched span visibly highlighted inline in full statement context, not just quoted in isolation — full traceability (NFR6) should feel effortless, not like digging.

6. **Final responsive/accessibility pass**
   - Verify timeline and map both work on a standard laptop screen width and don't break above/below typical resolutions used in a demo setting.

### DoD for Phase 4
- [ ] Timeline and map are cross-linked (selection state shared) and visually consistent (shared color/icon language).
- [ ] A time-scrubber filters both views together.
- [ ] Map handles marker density gracefully on a 5-witness, 25-sub-event synthetic incident without becoming unreadable.
- [ ] A cold reviewer, shown the timeline+map for the first time, can identify the single most-contested claim in an incident within ~10 seconds (informal test, not a hard metric — but check it).

---

## PHASE 5 — Hardening, Evaluation & Defense Prep

### Goal
Close out remaining NFRs, finalize metrics, and prepare deliverables for review/defense.

### Steps

1. **Full metrics run**: re-run Phase 1's eval script against the *final* pipeline (post any Phase 2/3/4 fixes that touched extraction), confirm NFR3 still holds.
2. **Security pass**: confirm role-based auth (NFR5) is enforced on every endpoint, confirm data encrypted at rest in Neo4j config.
3. **Real-world demo run**: execute one full incident from the manually-compiled real-world set (Section 10.2) end-to-end through the finished UI — this is your "it's not just tuned to its own synthetic data" proof point for a supervisor.
4. **Documentation**: architecture diagram (Section 5), workflow diagrams (Section 8), final report, demo script, slide deck.
5. **CI**: GitHub Actions running `pytest` (ML core + API integration tests) on every push.

### DoD for Phase 5
- [ ] All "Must" FRs and all NFRs in Sections 6–7 verifiably met, with evidence (test output, screenshots, or metrics report) for each.
- [ ] One successful real-world (non-synthetic) incident demo completed end-to-end.
- [ ] Final report + slide deck ready.

---

## Notes for the executing agent
- **Never skip ahead**: Phase 2 must call the Phase 1 pipeline as a black box through its frozen `pipeline.run()` signature — do not refactor extraction logic while wiring the API, or regressions become impossible to localize.
- **Every phase has a parity/regression test against the previous phase's output** — use these as hard gates, not suggestions.
- **The non-adjudicative constraint (Section 2.5) applies to every phase**: no UI element, API field, or ML output should ever produce a single "credibility" or "truthfulness" score for a witness. If a task seems to require one, stop and flag it rather than implementing it.