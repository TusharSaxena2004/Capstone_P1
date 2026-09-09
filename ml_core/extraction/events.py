import json
from typing import List, Optional, Tuple, Callable
from pydantic import BaseModel, Field, ValidationError
import logging

from ml_core.schema.models import EventTuple, EventOccurrence, Statement

logger = logging.getLogger(__name__)

class PydanticEventTuple(BaseModel):
    subject: Optional[str] = Field(None, description="The subject performing the action")
    action: str = Field(..., description="The action being performed")
    object: Optional[str] = Field(None, description="The object receiving the action")
    is_explicit_denial: bool = Field(False, description="True if the text explicitly states an event did NOT happen")
    source_span: Tuple[int, int] = Field(..., description="The character span of the extracted event in the text")

def extract_events_llm(statement: Statement, llm_call: Callable[[str, Optional[str]], str], sample_count: int = 3) -> Tuple[List[EventTuple], List[EventOccurrence]]:
    """
    Extracts events using a provided LLM callable.
    llm_call(prompt, error_msg) -> JSON string matching PydanticEventTuple list.
    Implements retries and self-consistency.
    """
    
    samples = []
    for _ in range(sample_count):
        extracted_list = _extract_with_retry(statement, llm_call)
        if extracted_list is not None:
            samples.append(extracted_list)
            
    if not samples:
        return [], []
        
    final_events = []
    final_occurrences = []
    
    base_sample = samples[0]
    
    for i, base_event in enumerate(base_sample):
        agreements = 0
        for other_sample in samples[1:]:
            if i < len(other_sample):
                other_event = other_sample[i]
                if (base_event.subject == other_event.subject and 
                    base_event.action == other_event.action and 
                    base_event.object == other_event.object):
                    agreements += 1
                    
        is_low_confidence = agreements < (len(samples) // 2) and len(samples) > 1
        
        # Determine text snippet safely
        start, end = base_event.source_span
        snippet = statement.text[start:end] if start < len(statement.text) else ""
        
        if base_event.is_explicit_denial:
            final_occurrences.append(EventOccurrence(
                source_statement_id=statement.id,
                source_span=base_event.source_span,
                text=snippet,
                event_type=base_event.action,
                occurred=False
            ))
        else:
            final_events.append(EventTuple(
                source_statement_id=statement.id,
                source_span=base_event.source_span,
                text=snippet,
                subject=base_event.subject,
                action=base_event.action,
                object=base_event.object,
                time_ref=None,
                location_ref=None,
                low_confidence=is_low_confidence,
                confidence=1.0 if not is_low_confidence else 0.5
            ))
            
    return final_events, final_occurrences


def _extract_with_retry(statement: Statement, llm_call: Callable[[str, Optional[str]], str]) -> Optional[List[PydanticEventTuple]]:
    prompt = f"Extract events from: {statement.text}"
    error_msg = None
    
    for attempt in range(2):
        try:
            response_text = llm_call(prompt, error_msg)
            data = json.loads(response_text)
            if not isinstance(data, list):
                raise ValueError("Output must be a JSON list")
                
            validated = [PydanticEventTuple(**item) for item in data]
            return validated
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            error_msg = f"Validation failed: {str(e)}. Please fix the output to match the schema."
            logger.warning(f"Attempt {attempt + 1} failed for statement {statement.id}: {error_msg}")
            
    logger.error(f"Failed to extract events for statement {statement.id} after 2 attempts.")
    return None
