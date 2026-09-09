import json
import os
from datetime import datetime
from typing import Literal

FEEDBACK_LOG_PATH = os.path.join(os.path.dirname(__file__), "feedback_log.jsonl")

def record_feedback(
    detection_result_id: str, 
    reviewer_verdict: Literal["confirmed", "false_positive", "missed"], 
    note: str = ""
):
    """
    Optional feedback hook (Step 8) to capture reviewer corrections for future retuning.
    Appends to a simple local JSONL log file.
    """
    feedback_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "detection_result_id": detection_result_id,
        "reviewer_verdict": reviewer_verdict,
        "note": note
    }
    
    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(feedback_entry) + "\n")
        
    return feedback_entry
