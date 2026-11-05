# Audit Report: Silent Witness (Capstone_P1)

## Summary
The project is roughly an **85–90% complete, fully operational forensic prototype**. The core pipeline (spaCy deterministic extraction, Sentence-Transformers semantic vector clustering, local LLM event extraction via LM Studio, and rule-based/NLI contradiction detection) is fully functional and backed by SQLite persistence (`silent_witness.db`). The frontend builds cleanly with 0 errors (`npm run build`), renders attributable timelines and Leaflet maps, and includes court export capabilities and live reviewer feedback. Gaps remain primarily in four abandoned 9-line synthetic data stubs (`pass`), hardcoded developer paths in documentation, and outdated theoretical claims/placeholder metrics in the academic LaTeX report (`capstone_report.tex`).

---

## Claims vs Reality

| Feature | Claimed Where | Status | Evidence |
|---|---|---|---|
| **Frontend Production Build** | `README.md:5, 217` | **REAL** | `frontend/` builds cleanly (`tsc -b && vite build`) producing `dist/` bundles in ~9s with 0 TypeScript errors. |
| **Local LLM Event Extraction** | `README.md:127-130` | **REAL** | `ml_core/extraction/events.py:17-90` connects via OpenAI API format to LM Studio (SmolLM-3B), extracts and validates `(Subject, Action, Object)` tuples with Pydantic. |
| **Semantic Vector Clustering** | `README.md:133-136` | **REAL** | `ml_core/alignment/cluster.py:27-63` lazily loads `all-MiniLM-L6-v2` (`local_files_only=True`) and clusters claims with `AgglomerativeClustering`. |
| **Negation Contradiction Override** | `README.md:123` | **REAL** | `ml_core/detection/rules.py:33-58` verifies subject identity, action compatibility, and object overlap before declaring contradictions. 8 unit tests in `test_negation.py` pass. |
| **Cross-Statement Coreference** | `project_summary.md:22` | **REAL** | `ml_core/extraction/ner.py:41-78` extracts colors, makes, and roles; `ml_core/extraction/coref.py:49-114` clusters matching named entities across testimonies. Verified in `test_coref.py`. |
| **Interactive Spatial Map** | `README.md:48, 71` | **REAL** | `ml_core/extraction/spatial.py:18-45` deterministically resolves crime scene coordinates offline; mapped to Leaflet map markers in `SpatialView.tsx`. |
| **Attributable Timeline** | `README.md:48, 70` | **REAL** | `ml_core/orchestrator.py:121, 180` aggregates temporal references; `server.py:194-225` maps real extracted timestamps into Vis-Timeline items. |
| **Persistent Storage** | `project_summary.md:61-65` | **REAL** | `server.py:46-118` initializes and persists incident records into SQLite database (`silent_witness.db`). |
| **Human-in-the-Loop Feedback** | `README.md:417` | **REAL** | `server.py:395-403` exposes `POST /api/feedback`, recording verdicts to `feedback_log.jsonl`; UI review buttons in `IncidentWorkspace.tsx:470-493` trigger live review submissions. |
| **Evidentiary Dossier & Custody Hash** | `README.md:419`, `IncidentWorkspace.tsx` | **REAL** | `IncidentWorkspace.tsx:81-133` generates and downloads signed `.txt` dossiers, `.csv` tables, and `.json` graphs; computes live SHA-256 hash using Web Crypto API. |
| **Quantitative Pipeline Evaluation** | `README.md:402` | **REAL** | `ml_core/tests/eval_pipeline.py:24-143` evaluates extraction and rules against 100 benchmark incidents in `ml_core/synthetic/generated/` and generates empirical `eval_report.md`. |
| **Academic LaTeX Report Sync** | `capstone_report.tex:1022-1029` | **FAKE** | `capstone_report.tex:1022-1029` retains old hardcoded synthetic metrics (`0.85, 0.88, 0.86`); lines 285, 309, 515 still reference old LAN IP `http://172.19.121.89:1234`. |
| **Asynchronous Celery/Redis Task Queue** | `capstone_report.tex:223`, `plan.md:1` | **MISSING** | Claimed in project plan and LaTeX report as BE2 responsibility, but never implemented. System executes synchronously via FastAPI and background threads. |
| **Neo4j Graph Database Backend** | `capstone_report.tex:223`, `plan.md:1` | **PARTIAL** | Graph export format in UI is Neo4j-compatible JSON, but runtime storage is SQLite (`silent_witness.db`), not a live Neo4j instance. |
| **Direct Audio / Whisper Ingestion** | `README.md:418` | **MISSING** | Listed as future roadmap item; testimonies currently ingested via text paste or JSON API only. |

---

## Issues by Severity

### Critical
*None.* (All previous build errors, merge conflict markers, discarded testimonies, and broken comparators have been resolved).

### High
1. **Fabricated Evaluation Metrics in Capstone Report (`capstone_report.tex:1022-1029`):** Table 10.1 in the formal submission report contains transcribed synthetic constants (`0.85, 0.88, 0.86`) instead of the true empirical numbers from `ml_core/tests/eval_pipeline.py`.
2. **Hardcoded LAN IP in Academic Documentation (`capstone_report.tex:285, 309, 515`):** The LaTeX report hardcodes `http://172.19.121.89:1234` instead of standard localhost or the documented `LOCAL_LLM_URL` environment variable.
3. **Ghost Architecture Claims in LaTeX Report (`capstone_report.tex:223-224, 238, 1229`):** The report describes active Celery task queues, Redis brokers, and a live Neo4j database as completed infrastructure, whereas the actual operational implementation is SQLite and synchronous FastAPI execution.

### Medium
4. **Student ID Placeholders in Report (`capstone_report.tex:127-131`):** Student registration numbers for 5 team members are set to `RA2211003010XXX`.

### Resolved in Recent Audits
- **Dead Stub Files in Synthetic Generator (`ml_core/synthetic/`):** Removed orphaned stubs (`incident_templates.py`, `label_generator.py`, `statement_generator.py`, `witness_profiles.py`) since logic was consolidated into `build_dataset.py`.
- **Hardcoded User Development Paths in Docs (`website_working.md:26, 47`):** Replaced hardcoded machine paths with relative, portable repository commands (`cd Capstone_P1` and `cd frontend`).

### Low
7. **Ad-Hoc Root Test Scripts (`test_all.py`, `test_fallback.py`):** Unstructured testing scripts at the root level contain hardcoded `time.sleep(3)` and fixed URLs (`http://127.0.0.1:8000`).
8. **Static Mock Fallback in Frontend Client (`frontend/src/api/client.ts:60, 77`):** When the backend is offline, API client falls back to static arrays (`mockIncidents`, `mockStatements`).
9. **Missing Type Declaration Suppression (`frontend/src/components/RelationshipGraph.tsx:2`):** `// @ts-ignore` used for `react-force-graph-2d` due to missing community `@types` package.

---

## Placeholders and Hardcoded Values
- `capstone_report.tex:127-131` - Registration numbers `RA2211003010XXX` for 5 team members.
- `capstone_report.tex:285, 309, 515` - Hardcoded private LAN IP `http://172.19.121.89:1234`.
- `capstone_report.tex:1022-1029` - Constant synthetic metrics `0.85, 0.88, 0.86`.
- `test_all.py:3` - Hardcoded `time.sleep(3)`.
- `frontend/src/api/client.ts:3-35` - Static fallback mock datasets used only when API server is unreachable.

---

## Incomplete and Dead Files
- None remaining in production core. All four orphaned synthetic generator stubs (`incident_templates.py`, `label_generator.py`, `statement_generator.py`, `witness_profiles.py`) removed.

---

## Verified by Running

### 1. Frontend Production Build (`frontend/`)
- Command: `npm run build` (`tsc -b && vite build`)
- Result: **SUCCESS (Exit Code 0)** in 8.97s.
- Output: Generated production assets in `dist/` (JS: 1,328.56 kB, CSS: 64.59 kB, HTML: 0.87 kB).

### 2. Pytest Unit & Integration Suite (`ml_core/tests/`)
- Command: `python -m pytest ml_core/tests/ -v`
- Result: **26 passed in 42.76s (0 failures, 0 errors)**.
- Modules:
  - `test_spatial.py`: 3 passed (offline landmark coordinate geocoding)
  - `test_pipeline.py`: 4 passed (guardrails, isotonic calibration)
  - `test_negation.py`: 8 passed (negation overrides with subject/action/object rules)
  - `test_coref.py`: 3 passed (intra-document & cross-statement coreference)
  - `test_events.py`: 3 passed (event extraction)
  - `test_orchestrator_integration.py`: 5 passed (FastAPI routes, SQLite persistence, feedback recording)

### 3. Quantitative Benchmark Harness (`eval_pipeline.py`)
- Command: `python ml_core/tests/eval_pipeline.py`
- Result: Evaluated across 100 benchmark incidents in `ml_core/synthetic/generated/` and generated honest `ml_core/eval_report.md`.

---

## What Actually Works
1. **End-to-End Extraction & Contradiction Pipeline:** Ingests unstructured statements, extracts entities, events, timestamps, and locations, clusters related claims using local Sentence-Transformers, and detects contradictions with character-level span offsets.
2. **SQLite Database Persistence:** All created incidents, statements, and contradictions are persisted into `silent_witness.db` and fetched on restart.
3. **Interactive Frontend Workspace:** Multi-tab interface featuring attributable Vis-Timeline, Leaflet map with geocoded markers, dynamic contradiction confidence scoring, and side-by-side statement comparison.
4. **Human-in-the-Loop Review System:** Reviewers can confirm contradictions or flag false positives directly from the Discrepancy Inceptor, appending feedback records to `feedback_log.jsonl`.
5. **Court-Admissible Export Suite:** One-click downloads for signed text Evidentiary Dossiers, CSV spreadsheets, and Neo4j Claim Graphs, accompanied by real-time SHA-256 integrity hashing.
6. **Automated CI/CD:** GitHub Actions workflow verifies Python unit/integration suites and tests frontend compilation on every commit.

---

## Prioritized Fix Plan

1. **Synchronize `capstone_report.tex` Evaluation Table (`capstone_report.tex:1022-1029`)** with empirical metrics from `eval_pipeline.py` to ensure academic honesty.
2. **Update LM Studio IP and Config in `capstone_report.tex:285, 309, 515`** to reflect standard `127.0.0.1:1234` and `LOCAL_LLM_URL`.
3. **Clarify Architecture in `capstone_report.tex:223, 238, 1229`** to accurately document the operational SQLite persistence layer rather than unbuilt Neo4j/Celery/Redis infrastructure.
4. **[RESOLVED] Deleted Dead Synthetic Generator Stubs** (`incident_templates.py`, `label_generator.py`, `statement_generator.py`, `witness_profiles.py`).
5. **[RESOLVED] Cleaned Hardcoded Absolute Paths in Documentation (`website_working.md:26, 47`)** to use portable relative commands.
6. **Fill Student Registration Numbers in `capstone_report.tex:127-131`** before final report submission.
7. **Clean Legacy Root Test Scripts (`test_all.py`, `test_fallback.py`)** or consolidate them into `ml_core/tests/`.
8. **Add Containerization (`docker-compose.yml`)** to deliver the one-click workstation deployment promised in project goals.
9. **Implement Direct Audio Ingestion (`ml_core/audio/` / `POST /api/transcribe`)** to satisfy the speech-to-text milestone on the roadmap.
10. **Add Hindi / Indian Vernacular Translation Preprocessor** to expand accessibility for regional law enforcement testimonies.
