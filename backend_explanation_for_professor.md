# Silent Witness: Backend & ML Pipeline Explained
**Project Role:** Backend 1 (Harshit Mishra) — Core ML & Backend Architecture  
**Document Purpose:** Quick, plain-English reference to explain the backend system to professors and evaluators.

---

## 1. What Does This System Do? (The 30-Second Summary)

When a crime or accident happens, police record multiple witness statements. People often remember things differently—one person says the getaway car was **red**, another says it was **black**; one says it happened at **2:00 PM**, another says **2:30 PM**.

**Silent Witness** is an AI backend that:
1. Takes multiple raw witness statements (or transcripts of spoken audio interviews).
2. Reads and understands the facts in each statement.
3. Automatically spots **agreements** and **contradictions** between witnesses.
4. Returns a clean, structured JSON report mapping out who saw what, without ever guessing or judging who is "lying".

---

## 2. The Step-by-Step Pipeline (How a Story Becomes JSON)

When you send a story to the backend via `POST /analyze`, it flows through 5 clear stages:

```
[Raw Witness Stories]
        │
        ▼
1. Fast Local Tagging (spaCy)
   - Finds Names, Locations, and Vehicles
   - Catches negations (e.g., "did NOT run the red light")
        │
        ▼
2. Fact Extraction (Local SmolLM-3B via LM Studio)
   - Breaks rambling sentences into clean tuples:
     (Subject: "Red Sedan", Action: "Sped through", Object: "Intersection")
        │
        ▼
3. Alignment & Grouping (Sentence-Transformers)
   - Groups facts that are talking about the exact same incident/action
        │
        ▼
4. Contradiction Detection Engine
   - Flags differences: Color mismatch, time difference, or existence clash
   - Links every contradiction directly back to the exact character in the text
        │
        ▼
[Final JSON Output]
   - List of Entities, Timeline of Events, and Flagged Contradictions
```

---

## 3. What Has Been Built So Far?

### A. The Core ML Engine (`ml_core/`)
- **Data Models (`schema/models.py`):** Clean Python classes for Witnesses, Statements, Entities, Events, and Contradictions. Every single extracted fact has a strict `source_span` (character start and end) so we can prove exactly where it came from in the original statement.
- **Named Entity Recognition (`extraction/ner.py`):** Uses spaCy to automatically pull out people, vehicles, and objects.
- **Time & Space Extractors (`temporal.py`, `spatial.py`):** Detects times ("2:15 PM") and locations without needing external paid services.
- **Grammar & Negation Handling (`negation.py`):** Checks dependency trees so statements like *"I did not see a weapon"* are correctly marked as a denial rather than a sighting.
- **Local AI Integration (`llm_client.py`):** Talks directly to a locally-running open-source model (**SmolLM-3B** in LM Studio on `localhost:1234`). No OpenAI fees, no internet needed, 100% private.
- **Semantic Clustering (`alignment/cluster.py`):** Uses Sentence-Transformers (`all-MiniLM-L6-v2`) so witness statements describing the same action with different words get grouped together.
- **Contradiction Engine (`detection/`):** Evaluates whether two claims contradict each other and produces an impartial rationale.
- **Pipeline Orchestrator (`orchestrator.py`):** The master function (`analyze_incident`) that connects all these modules into one single call.

### B. The API Server (`server.py`)
- Built with **FastAPI**.
- Exposes a `POST /analyze` endpoint.
- Has an interactive **Swagger UI** (`http://127.0.0.1:8000/docs`) where anyone can paste sample stories and click **Execute** to see the JSON output live.

### C. Large Forensic Testing Dataset (`ml_core/synthetic/`)
- **20 Real-World Crime Scenarios** with **400 distinct eyewitness testimonies** in Speech-to-Text (TTS) format.
- Includes realistic spoken language flaws (rambling, "um/uh", false starts, `[inaudible]` tags).
- Features **5 dedicated Indian scenarios** (Chandni Chowk jewelry heist, Marine Drive hit-and-run, Mumbai port smuggling, Rajdhani train robbery, Delhi VIP kidnapping).

### D. Automated CI/CD & Testing
- **12 Unit Tests (`ml_core/tests/`):** 100% passing tests for data modeling, negation rules, and pipeline detection logic.
- **GitHub Actions CI Pipeline (`.github/workflows/ci.yml`):** Automatically tests every commit on Ubuntu every time code is pushed.

---

## 4. Key Talking Points for Your Professor

1. **Why is this 100% local and free?**
   - We did not rely on paid cloud APIs (like OpenAI or Gemini). Everything runs locally on the machine using spaCy, Sentence-Transformers, and a local 3B model (SmolLM) via LM Studio.
2. **How do we maintain legal integrity? (Non-Adjudicative Design)**
   - The AI never labels a witness as "lying" or "dishonest". It strictly presents the facts: *"Witness A stated X, whereas Witness B stated Y."*
3. **Traceability:**
   - Every detected contradiction points directly to the exact words and character offsets in the original statements, so human investigators can verify the source in one click.
4. **Production Readiness:**
   - The code is modular, fully typed with Pydantic dataclasses, wrapped in a FastAPI REST server, and protected by automated CI/CD testing.

---

## 5. How to Demonstrate It Live to the Professor

1. **Open LM Studio:** Start the local server with SmolLM-3B loaded (port `1234`).
2. **Start the API:** Run `python server.py`.
3. **Show the Interactive Docs:** Open `http://127.0.0.1:8000/docs` in the browser.
4. **Run a Test Case:** Paste in two conflicting witness statements and show the instant JSON response highlighting the detected contradictions.
