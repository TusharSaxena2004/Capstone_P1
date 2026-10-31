import uuid
import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

app = FastAPI(
    title="Silent Witness API",
    description="Backend ML API for analyzing eyewitness testimonies",
    version="1.0.0"
)

# Enable CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory Database (seeded from theft_case_output.json) ---
# --- Demo incidents seed data (used to populate SQLite on first boot) ---
from seed_data import DB


# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENT STORAGE  (SQLite — survives server restarts)
# ─────────────────────────────────────────────────────────────────────────────
import sqlite3
import json as _json
import os as _os

_DB_PATH = _os.path.join(_os.path.dirname(__file__), "silent_witness.db")

def _get_db():
    """Return a thread-local SQLite connection with WAL mode for concurrency."""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    """Create tables if they don't exist and seed demo incidents."""
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            title TEXT,
            type TEXT,
            date TEXT,
            status TEXT,
            witness_count INTEGER,
            contradiction_count INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incident_data (
            incident_id TEXT PRIMARY KEY,
            data_json TEXT,
            FOREIGN KEY(incident_id) REFERENCES incidents(id)
        )
    """)
    conn.commit()

    # Seed demo incidents from the in-memory DB only if the table is empty
    cur = conn.execute("SELECT COUNT(*) FROM incidents")
    if cur.fetchone()[0] == 0:
        for inc in DB["incidents"]:
            conn.execute(
                "INSERT OR IGNORE INTO incidents VALUES (?,?,?,?,?,?,?)",
                (inc["id"], inc["title"], inc["type"], inc["date"],
                 inc["status"], inc["witnessCount"], inc["contradictionCount"])
            )
        for inc_id, inc_data in DB["incident_data"].items():
            conn.execute(
                "INSERT OR IGNORE INTO incident_data VALUES (?,?)",
                (inc_id, _json.dumps(inc_data))
            )
        conn.commit()
    conn.close()

_init_db()  # run once at startup

def _db_get_incidents():
    conn = _get_db()
    rows = conn.execute("SELECT * FROM incidents ORDER BY rowid DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def _db_get_incident_data(incident_id: str):
    conn = _get_db()
    row = conn.execute(
        "SELECT data_json FROM incident_data WHERE incident_id=?", (incident_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return _json.loads(row["data_json"])

def _db_save_incident(summary: dict, data: dict):
    conn = _get_db()
    conn.execute(
        "INSERT OR REPLACE INTO incidents VALUES (?,?,?,?,?,?,?)",
        (summary["id"], summary["title"], summary["type"], summary["date"],
         summary["status"], summary["witnessCount"], summary["contradictionCount"])
    )
    conn.execute(
        "INSERT OR REPLACE INTO incident_data VALUES (?,?)",
        (summary["id"], _json.dumps(data))
    )
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Convert ML pipeline output → UI-ready incident data
# ─────────────────────────────────────────────────────────────────────────────

# Known Indian city coordinates for spatial resolution
_KNOWN_COORDS = {
    "mg road":          (12.9757, 77.6011),
    "mg road bengaluru":(12.9757, 77.6011),
    "commercial street":(12.9814, 77.6097),
    "indiranagar":      (12.9783, 77.6408),
    "chickpet":         (12.9641, 77.5759),
    "koramangala":      (12.9279, 77.6271),
    "connaught place":  (28.6315, 77.2167),
    "chandni chowk":    (28.6562, 77.2310),
    "marine drive":     (18.9440, 72.8237),
    "railway station":  (28.6420, 77.2197),
    "police station":   (28.6429, 77.2195),
}

def _resolve_coordinates(location_text: str):
    """Try to resolve a location name to (lat, lng). Returns None if unknown."""
    t = location_text.lower().strip()
    for key, coords in _KNOWN_COORDS.items():
        if key in t:
            return coords
    return None

def _ml_results_to_ui(req_statements: List[str], title: str, results: dict) -> tuple:
    """
    Convert ML pipeline results → (summary_dict, incident_data_dict).
    Wires temporals → timeline and spatials → map markers from real ML output.
    Character spans are always clamped to the actual submitted statement lengths
    so highlighting never overruns the text (fixes the fallback span-mapping bug).
    """
    import datetime as _dt

    inc_id = f"inc-{uuid.uuid4().hex[:6]}"
    colors = ["border-blue-500", "border-red-500", "border-green-500",
              "border-purple-500", "border-yellow-500"]

    # --- Statements ---
    ui_statements = [
        {"id": f"stmt_{i}", "witness": f"Witness {chr(65+i)}", "text": text, "status": "Processed"}
        for i, text in enumerate(req_statements)
    ]

    # --- Contradictions (clamp spans to actual text length) ---
    ui_contradictions = []
    for i, d in enumerate(results.get("contradictions", [])):
        claims = []
        for span_info in d.get("source_span", []):
            stmt_id  = span_info[0]
            span_range = span_info[1]
            stmt_idx = int(stmt_id.split('_')[-1]) if '_' in stmt_id else 0
            full_text = req_statements[stmt_idx] if stmt_idx < len(req_statements) else ""
            text_len  = len(full_text)
            # Clamp span to actual submitted text — this is the fix for Issue 5
            if len(span_range) == 2:
                start = max(0, min(int(span_range[0]), text_len))
                end   = max(start, min(int(span_range[1]), text_len))
            else:
                start, end = 0, 0
            snippet = full_text[start:end] if end > start else (full_text[:60] + "…" if full_text else "—")
            claims.append({
                "witness":  f"Witness {chr(65+stmt_idx)}",
                "snippet":  snippet,
                "fullText": full_text,
                "span":     [start, end]
            })
        ui_contradictions.append({
            "id":       f"c_{i}",
            "type":     d.get("type", "semantic"),
            "title":    f"Flagged Discrepancy #{i+1}",
            "rationale":d.get("rationale", "Statements conflict."),
            "claims":   claims
        })

    # --- Timeline: prefer real temporals from ML, fall back to event sequence ---
    ui_timeline = []
    temporals = results.get("temporals", [])
    if temporals:
        for i, t in enumerate(temporals):
            stmt_idx = int(t.get("source_statement_id", "stmt_0").split('_')[-1])
            resolved = t.get("resolved_time") or t.get("text", "")
            try:
                ts = _dt.datetime.fromisoformat(resolved)
            except Exception:
                ts = _dt.datetime.now() - _dt.timedelta(minutes=30 - i)
            ui_timeline.append({
                "id":        f"ev_{i}",
                "content":   t.get("text", "Temporal reference"),
                "start":     ts.isoformat(),
                "witness":   f"Witness {chr(65 + stmt_idx)}",
                "className": f"border-l-4 {colors[stmt_idx % len(colors)]} bg-[var(--bg-surface)] text-[var(--text-primary)]"
            })
    else:
        # Fallback: use event tuples with dummy sequential timestamps
        for i, ev in enumerate(results.get("events", [])):
            stmt_idx = int(ev.get("source_statement_id", "stmt_0").split('_')[-1])
            ts = _dt.datetime.now() - _dt.timedelta(minutes=30 - i)
            content = f"{ev.get('subject', '')} {ev.get('action', 'event')} {ev.get('object', '')}".strip()
            ui_timeline.append({
                "id":        f"ev_{i}",
                "content":   content or "Unnamed event",
                "start":     ts.isoformat(),
                "witness":   f"Witness {chr(65 + stmt_idx)}",
                "className": f"border-l-4 {colors[stmt_idx % len(colors)]} bg-[var(--bg-surface)] text-[var(--text-primary)]"
            })

    # --- Map markers: prefer real spatials from ML, fall back to location entities ---
    ui_markers = []
    spatials = results.get("spatials", [])
    placed: set = set()
    if spatials:
        for i, s in enumerate(spatials):
            stmt_idx = int(s.get("source_statement_id", "stmt_0").split('_')[-1])
            loc_text = s.get("text", "")
            coords   = _resolve_coordinates(loc_text)
            if coords is None:
                # Spread unknown locations near a neutral base point with small offset
                coords = (28.6139 + i * 0.001, 77.2090 + i * 0.001)
            key = f"{coords[0]:.4f},{coords[1]:.4f}"
            if key in placed:
                continue  # deduplicate same location
            placed.add(key)
            ui_markers.append({
                "id":      f"m_{i}",
                "lat":     coords[0],
                "lng":     coords[1],
                "label":   loc_text,
                "witness": f"Witness {chr(65 + stmt_idx)}",
                "color":   "blue"
            })
    else:
        # Fallback: use LOCATION entities
        for i, ent in enumerate(results.get("entities", [])):
            if ent.get("label") in ["LOCATION", "FACILITY", "FAC"]:
                stmt_idx = int(ent.get("source_statement_id", "stmt_0").split('_')[-1])
                loc_text = ent.get("text", "")
                coords   = _resolve_coordinates(loc_text)
                if coords is None:
                    coords = (28.6139 + i * 0.001, 77.2090 + i * 0.001)
                key = f"{coords[0]:.4f},{coords[1]:.4f}"
                if key in placed:
                    continue
                placed.add(key)
                ui_markers.append({
                    "id":      f"m_{i}",
                    "lat":     coords[0],
                    "lng":     coords[1],
                    "label":   loc_text,
                    "witness": f"Witness {chr(65 + stmt_idx)}",
                    "color":   "blue"
                })

    summary = {
        "id":                inc_id,
        "title":             title,
        "type":              "Investigation",
        "date":              _dt.date.today().isoformat(),
        "status":            "Reviewing",
        "witnessCount":      len(req_statements),
        "contradictionCount":len(ui_contradictions)
    }
    data = {
        "statements":    ui_statements,
        "markers":       ui_markers,
        "timeline":      ui_timeline,
        "contradictions":ui_contradictions,
        "raw_entities":  results.get("entities", []),
        "raw_events":    results.get("events", []),
        "raw_temporals": results.get("temporals", []),
        "raw_spatials":  results.get("spatials", []),
    }
    return inc_id, summary, data

# ─────────────────────────────────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────────────────────────────────
class IncidentRequest(BaseModel):
    statements: List[str]
    title: str = "New Incident"

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Silent Witness Backend is running"}

@app.get("/api/incidents")
def get_incidents():
    rows = _db_get_incidents()
    # Normalize column names for frontend (snake_case → camelCase)
    return [
        {
            "id":                r.get("id"),
            "title":             r.get("title"),
            "type":              r.get("type"),
            "date":              r.get("date"),
            "status":            r.get("status"),
            "witnessCount":      r.get("witness_count", r.get("witnessCount", 0)),
            "contradictionCount":r.get("contradiction_count", r.get("contradictionCount", 0)),
        }
        for r in rows
    ]

@app.get("/api/incidents/{incident_id}")
def get_incident_data(incident_id: str):
    data = _db_get_incident_data(incident_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return data

@app.post("/analyze")
def analyze_statements(req: IncidentRequest):
    if not req.statements:
        raise HTTPException(status_code=400, detail="Must provide at least one statement.")
    try:
        from ml_core.orchestrator import analyze_incident
        return analyze_incident(req.statements)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/incidents")
def create_incident(req: IncidentRequest):
    """
    Run ML pipeline on submitted testimonies and persist the result.
    
    Fallback behaviour (when LM Studio is offline):
    - Loads theft_case_output.json for ML results (contradictions, events, etc.)
    - BUT keeps the user's ORIGINAL submitted statements as the statement text.
    - Clamps all character spans from the fallback JSON to fit within the user's text.
    This ensures the Discrepancy Inspector never highlights garbage indices.
    """
    if not req.statements:
        raise HTTPException(status_code=400, detail="Must provide at least one statement.")

    try:
        using_fallback = False
        try:
            from ml_core.orchestrator import analyze_incident
            results = analyze_incident(req.statements)
            if not results or "contradictions" not in results:
                raise ValueError("Invalid ML pipeline output structure")
        except Exception as e:
            import logging
            logging.warning(f"ML Pipeline unavailable ({e}). Using theft_case_output.json fallback...")
            using_fallback = True
            fallback_path = _os.path.join(_os.path.dirname(__file__), "theft_case_output.json")
            if _os.path.exists(fallback_path):
                with open(fallback_path, "r", encoding="utf-8") as f:
                    results = _json.load(f)
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"ML pipeline unavailable ({str(e)}) and no fallback file found."
                )

        inc_id, summary, data = _ml_results_to_ui(req.statements, req.title, results)

        if using_fallback:
            # Mark in the summary so the UI can show a banner
            summary["status"] = "Demo (Fallback)"

        _db_save_incident(summary, data)
        return {"id": inc_id, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class FeedbackRequest(BaseModel):
    detection_result_id: str
    reviewer_verdict: str = "confirmed"
    note: Optional[str] = ""

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    try:
        from ml_core.feedback import record_feedback
        entry = record_feedback(req.detection_result_id, req.reviewer_verdict, req.note or "")
        return {"status": "success", "feedback": entry}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

