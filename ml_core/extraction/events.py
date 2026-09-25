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
    source_span: Optional[Tuple[int, int]] = Field(default=(0, 0), description="The character span of the extracted event in the text")

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
        
        # Determine text representation and span safely
        event_summary = f"{base_event.subject or ''} {base_event.action} {base_event.object or ''}".strip()
        
        start, end = base_event.source_span
        if (end - start) < 4 or start >= end or end > len(statement.text):
            action_lower = base_event.action.lower() if base_event.action else ""
            stmt_lower = statement.text.lower()
            idx = stmt_lower.find(action_lower) if action_lower else -1
            if idx != -1:
                start = idx
                end = idx + len(base_event.action)
            else:
                start = 0
                end = min(len(statement.text), 50)
        
        resolved_span = (start, end)
        snippet = event_summary if event_summary else statement.text[start:end]
        
        if base_event.is_explicit_denial:
            final_occurrences.append(EventOccurrence(
                source_statement_id=statement.id,
                source_span=resolved_span,
                text=snippet,
                event_type=base_event.action,
                occurred=False
            ))
        else:
            final_events.append(EventTuple(
                source_statement_id=statement.id,
                source_span=resolved_span,
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
    prompt = f"""Extract all events/actions from the following eyewitness testimony.
Return the result as a strict JSON array of objects. Do not wrap in markdown or add explanations.

Schema:
- "subject": (string) Who/what is performing the action.
- "action": (string) The verb or action (e.g. "enter", "speed", "shoot", "carry").
- "object": (string) What or who was targeted / affected.
- "is_explicit_denial": (boolean) Set to true ONLY if the witness explicitly says the action did NOT occur (e.g. "did not enter", "never ran").
- "source_span": (array of 2 ints) [0, 0]

Example Input: "The suspect entered the bank. The security guard did not fire."
Example Output:
[
  {{"subject": "The suspect", "action": "entered", "object": "the bank", "is_explicit_denial": false, "source_span": [0, 0]}},
  {{"subject": "The security guard", "action": "fire", "object": "", "is_explicit_denial": true, "source_span": [0, 0]}}
]

Testimony to extract:
"{statement.text}"

JSON Output:"""
    error_msg = None
    
    for attempt in range(2):
        try:
            response_text = llm_call(prompt, error_msg)
            raw = response_text.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
                
            start = raw.find('[')
            end = raw.rfind(']')
            if start != -1 and end != -1 and end > start:
                raw = raw[start:end+1]
                
            import re
            raw = re.sub(r',\s*\]', ']', raw)
            raw = re.sub(r',\s*\}', '}', raw)
            
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("Output must be a JSON list")
                
            validated = [PydanticEventTuple(**item) for item in data]
            return validated
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            error_msg = f"Validation failed: {str(e)}. Please fix the output to match the schema."
            logger.warning(f"Attempt {attempt + 1} failed for statement {statement.id}: {error_msg}")
            
    logger.error(f"Failed to extract events for statement {statement.id} after 2 attempts.")
    return None
