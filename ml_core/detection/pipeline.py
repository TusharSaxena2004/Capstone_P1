from typing import List, Callable, Optional, Any
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
    llm_rationale_gen: Callable[[str], str],
    claim_clusters: Optional[List[List[Any]]] = None
) -> List[DetectionResult]:
    """
    Core detection pipeline merging rules and NLI predictions (Steps 5 & 6).
    """
    results = []
    
    # 1. Existence Contradictions (Rule-based)
    results.extend(check_existence_contradictions(occurrences, events))
    
    # 2. Semantic Contradictions (NLI-based)
    event_pairs = []
    seen_pairs = set()

    if claim_clusters is not None:
        # Check pairs within the same semantic cluster
        for cluster in claim_clusters:
            if len(cluster) < 2:
                continue
            for i in range(len(cluster)):
                for j in range(i + 1, len(cluster)):
                    key = (min(cluster[i].id, cluster[j].id), max(cluster[i].id, cluster[j].id))
                    if key not in seen_pairs:
                        seen_pairs.add(key)
                        event_pairs.append((cluster[i].event, cluster[j].event, cluster[i].id, cluster[j].id))
        
        # Also check cross-witness events sharing identical themes (clothing, escape, weapons, theft)
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                ev1 = events[i]
                ev2 = events[j]
                if ev1.source_statement_id != ev2.source_statement_id:
                    act1 = ev1.action.lower()
                    act2 = ev2.action.lower()
                    sub1 = (ev1.subject or "").lower()
                    sub2 = (ev2.subject or "").lower()
                    
                    themes = ["wear", "cloth", "escap", "fled", "flee", "arm", "gun", "crowbar", "steal", "stole", "loot", "alarm", "enter"]
                    matches_theme = any(k in act1 and k in act2 for k in themes) or \
                                    (any(k in act1 for k in themes) and any(k in act2 for k in themes)) or \
                                    (("suspect" in sub1 or "robber" in sub1 or "thie" in sub1) and ("suspect" in sub2 or "robber" in sub2 or "thie" in sub2) and (act1.split()[0] in act2 or act2.split()[0] in act1))
                    
                    if matches_theme:
                        key = (f"theme_{min(i, j)}", f"theme_{max(i, j)}")
                        if key not in seen_pairs:
                            seen_pairs.add(key)
                            event_pairs.append((ev1, ev2, f"claim_{i}", f"claim_{j}"))
    else:
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                event_pairs.append((events[i], events[j], f"c_{i}", f"c_{j}"))

    for c1, c2, id1, id2 in event_pairs:
        if c1.source_statement_id == c2.source_statement_id:
            continue
            
        # Hard Negation Override
        rule_override = evaluate_negation_override(c1, c2)
        if rule_override:
            rule_override.claim_ids = [id1, id2]
            results.append(rule_override)
            continue
            
        # NLI Scoring and Calibration
        raw_score = nli_model_predict(c1.text, c2.text)
        calibrated_score = calibrator.calibrate(raw_score)
        
        # Threshold for contradiction
        if calibrated_score > 0.7:
            rat = generate_nli_rationale(c1, c2, llm_rationale_gen)
            results.append(DetectionResult(
                claim_ids=[id1, id2],
                type="semantic",
                verdict="contradiction",
                confidence=calibrated_score,
                rationale=rat,
                source_span=[(c1.source_statement_id, c1.source_span), (c2.source_statement_id, c2.source_span)]
            ))
            
    return results
