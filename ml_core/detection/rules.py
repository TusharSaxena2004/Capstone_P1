from typing import List, Optional
from ml_core.schema.models import EventOccurrence, EventTuple, DetectionResult

def check_existence_contradictions(occurrences: List[EventOccurrence], events: List[EventTuple]) -> List[DetectionResult]:
    """
    Checks for existence contradictions (Step 4).
    Compares explicit EventOccurrence denials against EventTuple assertions.
    """
    results = []
    
    for occ in occurrences:
        if occ.occurred is False:
            # Find any EventTuple from a DIFFERENT witness with the same action
            for ev in events:
                if occ.source_statement_id != ev.source_statement_id and occ.event_type == ev.action:
                    # Direct existence contradiction
                    results.append(DetectionResult(
                        claim_ids=[],  # To be populated by pipeline
                        type="existence",
                        verdict="contradiction",
                        confidence=1.0,
                        rationale=f"One witness stated that the action '{occ.event_type}' did not happen, while another described it happening.",
                        source_span=[(occ.source_statement_id, occ.source_span), (ev.source_statement_id, ev.source_span)]
                    ))

    return results

def evaluate_negation_override(claim1: EventTuple, claim2: EventTuple) -> Optional[DetectionResult]:
    """
    Evaluates a pair of aligned claims for negation-based hard overrides (Step 3).
    Returns a contradiction if exactly one claim is negated.
    """
    if claim1.negated != claim2.negated:
        return DetectionResult(
            claim_ids=[], # To be populated by pipeline
            type="attribute", # or existence, mapped generally as attribute mismatch here
            verdict="contradiction",
            confidence=1.0,
            rationale="One witness explicitly negated this claim, while the other asserted it.",
            source_span=[(claim1.source_statement_id, claim1.source_span), (claim2.source_statement_id, claim2.source_span)]
        )
        
    return None
