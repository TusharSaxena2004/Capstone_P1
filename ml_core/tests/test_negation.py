import pytest
from ml_core.schema.models import Statement, EventTuple
from ml_core.extraction.negation import apply_negation_scoping

def test_direct_negation():
    stmt = Statement(id="s1", witness_id="w1", text="She did not see a weapon.", incident_id="i1")
    events = [EventTuple(source_statement_id="s1", source_span=(12, 15), text="see", subject="She", action="see", object="weapon")]
    events = apply_negation_scoping(stmt, events)
    assert events[0].negated is True

def test_no_negation():
    stmt = Statement(id="s2", witness_id="w1", text="She saw a weapon.", incident_id="i1")
    events = [EventTuple(source_statement_id="s2", source_span=(4, 7), text="saw", subject="She", action="saw", object="weapon")]
    events = apply_negation_scoping(stmt, events)
    assert events[0].negated is False

def test_double_negation():
    stmt = Statement(id="s3", witness_id="w1", text="I didn't not see it.", incident_id="i1")
    events = [EventTuple(source_statement_id="s3", source_span=(13, 16), text="see", subject="I", action="see", object="it")]
    events = apply_negation_scoping(stmt, events)
    assert events[0].negated is False  # Two negations cancel out

def test_hedged_negation():
    stmt = Statement(id="s4", witness_id="w1", text="I didn't clearly see the driver, but I think it was a man.", incident_id="i1")
    # 'see' is negated
    events1 = [EventTuple(source_statement_id="s4", source_span=(17, 20), text="see", subject="I", action="see", object="driver")]
    events1 = apply_negation_scoping(stmt, events1)
    assert events1[0].negated is True
    
    # 'was' is NOT negated
    events2 = [EventTuple(source_statement_id="s4", source_span=(48, 51), text="was", subject="it", action="was", object="man")]
    events2 = apply_negation_scoping(stmt, events2)
    assert events2[0].negated is False
