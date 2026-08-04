# Silent Witness — Diagram Descriptions

These are written as generation prompts — paste any one section into an LLM or diagramming tool (e.g. Antigravity) to produce the actual visual. Each description specifies the components, their grouping, and the connections between them explicitly enough to render without further clarification.

---

## 1. System Architecture Diagram

**Prompt / description to generate this diagram:**

Create a boxes-and-arrows system architecture diagram, laid out left-to-right in four vertical layers:

**Layer 1 — Client (leftmost):**
- One box: "Reviewer (Browser)"

**Layer 2 — Presentation:**
- One box: "React Frontend" containing three labeled sub-sections inside it: "Statement Entry/Upload", "Timeline View", "Map View"
- Arrow from "Reviewer (Browser)" to "React Frontend", labeled "HTTPS"

**Layer 3 — Services (draw as two side-by-side boxes, connected to each other, not stacked):**
- Box A: "Web/API Backend" — sub-labels: "Auth (JWT)", "Incident & Statement CRUD", "Report Export"
- Box B: "ML/NLP Service" — sub-labels: "NER + Temporal + Spatial Extraction", "Claim Alignment", "Contradiction/Agreement Detection"
- Between Box A and Box B, draw a small box: "Task Queue (Celery + Redis)" — arrow from Web/API Backend into the Task Queue labeled "enqueue job", and an arrow from the Task Queue into the ML/NLP Service labeled "dispatch job"
- Arrow from ML/NLP Service back to Web/API Backend labeled "job result / webhook"
- Arrow from "React Frontend" to "Web/API Backend" labeled "REST API calls"

**Layer 4 — Data & External (rightmost):**
- Box: "Neo4j Graph Database" — arrows connecting to both Web/API Backend and ML/NLP Service (both read/write), labeled "entities, events, claims, witnesses"
- Box: "Geocoding Service (Nominatim/OSM)" — arrow from ML/NLP Service to this box, labeled "resolve location text → coordinates"

Use a clean, muted color palette (blues/grays), rounded rectangle nodes, and directional arrows with the labels exactly as given above.

---

## 2. Workflow / Sequence Diagram

**Prompt / description to generate this diagram:**

Create a swimlane sequence diagram with five vertical lanes (actors), left to right in this order:
1. Reviewer
2. Frontend
3. Web/API Backend
4. ML/NLP Service
5. Database

Sequence of steps (draw as numbered arrows moving between lanes, top to bottom, in this exact order):

1. Reviewer → Frontend: "Submit witness statement"
2. Frontend → Web/API Backend: "POST /incidents/{id}/statements"
3. Web/API Backend → Database: "Store raw statement"
4. Web/API Backend → ML/NLP Service: "Enqueue extraction job (async)"
5. Web/API Backend → Frontend: "202 Accepted (job id)"
6. ML/NLP Service → ML/NLP Service: "Run NER + temporal + spatial + event extraction" (self-loop / internal processing box)
7. ML/NLP Service → Database: "Write structured claims"
8. ML/NLP Service → ML/NLP Service: "Align claims across witnesses; detect contradictions/agreements" (self-loop / internal processing box)
9. ML/NLP Service → Database: "Write contradiction/agreement results with source-span references"
10. Frontend → Web/API Backend: "GET /incidents/{id}/timeline and /map" (polling or on job-complete notification)
11. Web/API Backend → Database: "Read consolidated results"
12. Web/API Backend → Frontend: "Return timeline + map + flagged items"
13. Frontend → Reviewer: "Render timeline, map, and contradiction/agreement markers"
14. Reviewer → Frontend: "Click a flagged item"
15. Frontend → Reviewer: "Show exact source statement text (traceability)"

Use standard sequence-diagram notation: vertical lifelines per lane, solid arrows for requests, dashed arrows for responses, and numbered steps matching the order above.

---

## 3. Technology Stack Diagram

**Prompt / description to generate this diagram:**

Create a horizontal layered stack diagram, top to bottom, five layers, each layer a wide horizontal band containing labeled chips/pills for each technology:

**Layer 1 (top) — Presentation:**
React · Tailwind CSS · `vis-timeline` (or D3) · Leaflet + OpenStreetMap

**Layer 2 — API / Backend:**
FastAPI or Node.js/Express · JWT Auth · REST API

**Layer 3 — ML / NLP:**
spaCy · Hugging Face Transformers (event/relation extraction) · `sentence-transformers` (semantic similarity) · NLI model (e.g. `roberta-large-mnli`) · `dateparser` (temporal normalization) · `networkx` (graph construction)

**Layer 4 — Data:**
Neo4j (primary graph store) · PostgreSQL + PostGIS (fallback) · Redis (task queue backing store)

**Layer 5 (bottom) — Infrastructure:**
Docker Compose · GitHub Actions (CI) · Nominatim (geocoding, external)

Draw each layer as a distinct horizontal band with a subtle background color per layer (e.g. layer 1 light blue, layer 2 light green, layer 3 light purple, layer 4 light orange, layer 5 light gray), and each technology as a rounded pill/chip within its band. Label each band on the left margin with its layer name.
