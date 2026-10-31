import json
import os

# Simulate what server.py does in create_incident
base_dir = os.path.dirname(os.path.abspath(__file__))
theft_path = os.path.join(base_dir, "theft_case_output.json")
with open(theft_path, "r", encoding="utf-8") as f:
    results = json.load(f)

# Mock statements that would have produced this (since we don't have the original text)
# In reality, req.statements has the text. We will use dummy text that is long enough.
dummy_statements = [
    "I was stationed by the glass doors of the Tanishq showroom on MG Road. " + "A"*200,
    "I run. three robbers sprinted out of the store entrance carrying heavy duffel bags. " + "B"*200,
    "the primary robber wore a dark leather jacket... the primary robber fled. " + "C"*200,
    "I was walking along MG Road. the thieves dashed. The primary robber was wearing a bright red hoodie with beige cargo pants. " + "D"*200,
    "I securing the cash register. The thieves took fifty lakhs worth of diamond necklaces and luxury watches from the vault counters. " + "E"*200
]

ui_contradictions = []
for i, d in enumerate(results.get("contradictions", [])):
    claims = []
    for j, span_info in enumerate(d.get("source_span", [])):
        stmt_id = span_info[0]
        span_range = span_info[1]
        
        full_text = ""
        snippet = "Excerpt"
        stmt_idx = int(stmt_id.split('_')[-1]) if '_' in stmt_id else 0
        if stmt_idx < len(dummy_statements):
            full_text = dummy_statements[stmt_idx]
            if len(span_range) == 2:
                start, end = span_range
                # Make sure indices are valid
                start = min(start, len(full_text))
                end = min(end, len(full_text))
                snippet = full_text[start:end]
        
        claims.append({
            "witness": f"Witness {chr(65+stmt_idx)}",
            "snippet": snippet,
            "fullText": full_text,
            "span": span_range
        })
        
    ui_contradictions.append({
        "id": f"c_{i}",
        "type": d.get("type", "semantic"),
        "title": f"Flagged Discrepancy #{i+1}",
        "rationale": d.get("rationale", "Statements conflict."),
        "claims": claims
    })

print(f"Mapped {len(ui_contradictions)} contradictions successfully!")
if len(ui_contradictions) > 0:
    print(json.dumps(ui_contradictions[0], indent=2))
