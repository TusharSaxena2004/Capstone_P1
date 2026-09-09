from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

@dataclass
class ExtractedBase:
    """Base class ensuring every extracted object has traceability."""
    source_statement_id: str
    source_span: Tuple[int, int]
    text: str

@dataclass
class Entity(ExtractedBase):
    label: str  # PERSON, VEHICLE, OBJECT, LOCATION
    attributes: Dict[str, Any] = field(default_factory=dict)
    entity_cluster_id: Optional[str] = None  # Step 1: added entity_cluster_id

@dataclass
class TemporalExpression(ExtractedBase):
    resolved_time: Optional[str] = None

@dataclass
class SpatialReference(ExtractedBase):
    resolved_coordinates: Optional[Tuple[float, float]] = None
    resolved: bool = False

@dataclass
class EventTuple(ExtractedBase):
    subject: Optional[str]
    action: str
    object: Optional[str]
    time_ref: Optional[TemporalExpression]
    location_ref: Optional[SpatialReference]
    confidence: float = 1.0
    low_confidence: bool = False  # Step 2: Added for self-consistency ambiguity
    negated: bool = False  # Step 3: Added for explicit negation scoping

@dataclass
class EventOccurrence(ExtractedBase):
    """Step 4: Explicit claim type for whether an event happened."""
    event_type: str
    occurred: Optional[bool] = None

@dataclass
class Claim:
    id: str
    event: EventTuple
    entities: List[Entity] = field(default_factory=list)

@dataclass
class DetectionResult:
    """Step 6: Single verdict combining NLI and rule-based outputs."""
    claim_ids: List[str]
    type: str  # attribute, spatial, temporal, existence, motion
    verdict: str  # contradiction, agreement
    confidence: float
    rationale: str
    source_span: List[Tuple[str, Tuple[int, int]]] # [(statement_id, span)]

@dataclass
class Witness:
    id: str
    name: str
    perception_profile: Optional[Dict[str, Any]] = None

@dataclass
class Statement:
    id: str
    witness_id: str
    text: str
    incident_id: str

@dataclass
class Incident:
    id: str
    incident_type: str  # e.g., road_accident, robbery, fire
    description: str
    statements: List[Statement] = field(default_factory=list)
