import spacy
from typing import List
from ml_core.schema.models import Statement, EventTuple

try:
    nlp = spacy.load("en_core_web_trf")
except Exception:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None

def apply_negation_scoping(statement: Statement, events: List[EventTuple]) -> List[EventTuple]:
    """
    Detects if an event is explicitly negated using spaCy's dependency parser.
    Populates the negated: bool field on the EventTuple.
    """
    if not nlp or not events:
        return events
        
    doc = nlp(statement.text)
    
    for event in events:
        start_char, end_char = event.source_span
        event_tokens = [tok for tok in doc if tok.idx >= start_char and tok.idx < end_char]
        
        if not event_tokens:
            continue
            
        neg_count = 0
        for etok in event_tokens:
            neg_count += sum(1 for c in etok.children if c.dep_ == "neg")
            # Also check if negation is attached to an auxiliary verb of this token
            if etok.pos_ in ("VERB", "AUX"):
                for aux in [c for c in etok.children if c.dep_ in ("aux", "auxpass")]:
                    neg_count += sum(1 for c in aux.children if c.dep_ == "neg")
                    
        # If odd number of negations attached to the event tokens, it is negated
        if neg_count % 2 != 0:
            event.negated = True
        else:
            event.negated = False
            
    return events
