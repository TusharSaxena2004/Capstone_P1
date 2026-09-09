import pytest
from ml_core.schema.models import EventTuple
from ml_core.detection.pipeline import verify_rationale, generate_nli_rationale

def test_verify_rationale_clean():
    rationale = "Witness A says the car was red, but Witness B says it was blue."
    assert verify_rationale(rationale) == rationale
    
def test_verify_rationale_denylist():
    rationale = "Witness A is lying about the car color."
    safe_rationale = verify_rationale(rationale)
    assert safe_rationale != rationale
    assert "lying" not in safe_rationale
    assert "factual inconsistency" in safe_rationale
    
def test_generate_nli_rationale():
    c1 = EventTuple(source_statement_id="s1", source_span=(0,5), text="The car sped through.", subject=None, action="sped", object=None)
    c2 = EventTuple(source_statement_id="s2", source_span=(0,5), text="The car stopped.", subject=None, action="stopped", object=None)
    
    def mock_llm(prompt):
        # We simulate a bad LLM that outputs a denylisted word
        return "Witness 1 is mistaken; the car stopped."
        
    rat = generate_nli_rationale(c1, c2, mock_llm)
    assert "mistaken" not in rat
    assert "factual inconsistency" in rat
