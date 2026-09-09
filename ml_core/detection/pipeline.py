from typing import List, Callable, Optional
from ml_core.schema.models import EventTuple, EventOccurrence, DetectionResult
from ml_core.detection.rules import check_existence_contradictions, evaluate_negation_override
from ml_core.detection.calibration import calibrator

# Denylist for credibility-adjacent language (Step 6)
CREDIBILITY_DENYLIST = ["lying", "unreliable", "credible", "trustworthy", "mistaken", "false", "true", "dishonest", "reliable", "inaccurate"]

def verify_rationale(rationale: str) -> str:
    """
    Ensures the generated rationale does not violate the non-adjudicative constraint.
    If a denylisted word is found, returns a generic safe fallback.
    """
    lower_rat = rationale.lower()
    for word in CREDIBILITY_DENYLIST:
        if word in lower_rat:
            return "This claim presents a factual inconsistency between the statements."
    return rationale

def generate_nli_rationale(claim1: EventTuple, claim2: EventTuple, llm_call: Callable[[str], str]) -> str:
    """
    Calls an LLM to generate a single-sentence rationale for a contradiction.
    """
    prompt = (
        f"Generate a single-sentence rationale describing the factual mismatch between these two statements.\n"
        f"Statement 1: {claim1.text}\nStatement 2: {claim2.text}\n"
        f"CRITICAL: Do NOT comment on witness reliability, credibility, or who is mistaken. Only state the factual difference."
    )
    raw_rationale = llm_call(prompt)
    return verify_rationale(raw_rationale)

def run_detection_pipeline(
    occurrences: List[EventOccurrence], 
    events: List[EventTuple], 
    nli_model_predict: Callable[[str, str], float],
    llm_rationale_gen: Callable[[str], str]
) -> List[DetectionResult]:
    """
    Core detection pipeline merging rules and NLI predictions (Steps 5 & 6).
    """
    results = []
    
    # 1. Existence Contradictions (Rule-based)
    results.extend(check_existence_contradictions(occurrences, events))
    
    # 2. Semantic Contradictions (NLI-based) on pairwise combinations
    # (Assuming we are iterating over aligned claim clusters in a real system)
    for i in range(len(events)):
        for j in range(i+1, len(events)):
            c1 = events[i]
            c2 = events[j]
            
            if c1.source_statement_id == c2.source_statement_id:
                continue
                
            # Hard Negation Override
            rule_override = evaluate_negation_override(c1, c2)
            if rule_override:
                results.append(rule_override)
                continue
                
            # NLI Scoring and Calibration
            raw_score = nli_model_predict(c1.text, c2.text)
            calibrated_score = calibrator.calibrate(raw_score)
            
            # Threshold for contradiction
            if calibrated_score > 0.7:
                rat = generate_nli_rationale(c1, c2, llm_rationale_gen)
                results.append(DetectionResult(
                    claim_ids=["c1", "c2"],
                    type="semantic",
                    verdict="contradiction",
                    confidence=calibrated_score,
                    rationale=rat,
                    source_span=[(c1.source_statement_id, c1.source_span), (c2.source_statement_id, c2.source_span)]
                ))
                
    return results
