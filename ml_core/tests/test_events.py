import pytest
import json
from ml_core.schema.models import Statement
from ml_core.extraction.events import extract_events_llm

def test_extract_events_success():
    stmt = Statement(id="s1", witness_id="w1", text="The man ran to the store.", incident_id="i1")
    
    def mock_llm(prompt, error_msg):
        return json.dumps([
            {"subject": "man", "action": "ran", "object": "store", "is_explicit_denial": False, "source_span": [4, 24]}
        ])
        
    events, occurrences = extract_events_llm(stmt, mock_llm, sample_count=1)
    
    assert len(events) == 1
    assert events[0].subject == "man"
    assert events[0].low_confidence == False
    assert len(occurrences) == 0

def test_extract_events_retry_success():
    stmt = Statement(id="s2", witness_id="w1", text="I didn't see anyone.", incident_id="i1")
    call_count = [0]
    
    def mock_llm_with_failure(prompt, error_msg):
        call_count[0] += 1
        if call_count[0] == 1:
            return "Not a json list"
        return json.dumps([
            {"subject": "I", "action": "see", "object": "anyone", "is_explicit_denial": True, "source_span": [2, 19]}
        ])
        
    events, occurrences = extract_events_llm(stmt, mock_llm_with_failure, sample_count=1)
    
    assert call_count[0] == 2
    assert len(events) == 0
    assert len(occurrences) == 1
    assert occurrences[0].occurred == False
    assert occurrences[0].event_type == "see"

def test_extract_events_low_confidence():
    stmt = Statement(id="s3", witness_id="w1", text="The car hit the pole.", incident_id="i1")
    call_count = [0]
    
    def mock_inconsistent_llm(prompt, error_msg):
        call_count[0] += 1
        if call_count[0] == 1:
            # Base sample
            return json.dumps([{"subject": "car", "action": "hit", "object": "pole", "is_explicit_denial": False, "source_span": [0, 20]}])
        else:
            # Different output for subsequent samples
            return json.dumps([{"subject": "vehicle", "action": "crashed", "object": "sign", "is_explicit_denial": False, "source_span": [0, 20]}])
            
    events, occurrences = extract_events_llm(stmt, mock_inconsistent_llm, sample_count=3)
    
    assert len(events) == 1
    assert events[0].low_confidence == True
    assert events[0].confidence == 0.5
