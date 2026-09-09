import uuid
from typing import List, Dict, Optional
from ml_core.schema.models import Entity, Statement

# Documentation of choice:
# We attempt to use fastcoref for single-document coreference resolution.
# If it fails to load or fails during inference, we fallback to a simple heuristic
# or leave it unresolved, to ensure the pipeline doesn't completely break.

try:
    from fastcoref import FCoref
    _coref_model = FCoref(device='cpu')  # load model
except ImportError:
    _coref_model = None
except Exception:
    _coref_model = None

def resolve_single_document_coref(statement: Statement, entities: List[Entity]) -> List[Entity]:
    """
    Resolves pronouns and generic mentions within a single statement using fastcoref.
    If fastcoref is unavailable, returns the entities unmodified as a fallback.
    """
    if _coref_model is None or not statement.text.strip():
        return entities

    try:
        preds = _coref_model.predict(texts=[statement.text])
        clusters = preds[0].get_clusters()
        
        doc_cluster_mapping = {}
        for cluster_idx, cluster_spans in enumerate(clusters):
            for span in cluster_spans:
                # span is (start, end)
                doc_cluster_mapping[span] = f"doc_{statement.id}_{cluster_idx}"
        
        for entity in entities:
            # Check overlap
            for span, c_id in doc_cluster_mapping.items():
                if max(entity.source_span[0], span[0]) < min(entity.source_span[1], span[1]):
                    entity.attributes["_doc_cluster_id"] = c_id
                    break
    except Exception as e:
        # Fallback if prediction fails
        pass

    return entities


def resolve_cross_statement_coref(statements: List[Statement], all_entities: List[Entity]) -> List[Entity]:
    """
    Lightweight cross-statement entity resolution: for entities with matching type
    + at least one shared attribute (e.g., 'sedan' + 'red'), link them into a shared EntityCluster 
    with a unique ID. Does NOT merge attribute values.
    """
    parent = {}
    
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
        
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    for i in range(len(all_entities)):
        parent[i] = i
        
    doc_cluster_to_indices = {}
    for i, entity in enumerate(all_entities):
        dc_id = entity.attributes.get("_doc_cluster_id")
        if dc_id:
            if dc_id not in doc_cluster_to_indices:
                doc_cluster_to_indices[dc_id] = []
            doc_cluster_to_indices[dc_id].append(i)
            
    for indices in doc_cluster_to_indices.values():
        first = indices[0]
        for other in indices[1:]:
            union(first, other)

    # Now cross-statement heuristics
    for i in range(len(all_entities)):
        for j in range(i + 1, len(all_entities)):
            e1 = all_entities[i]
            e2 = all_entities[j]
            
            if e1.source_statement_id == e2.source_statement_id:
                continue
                
            if e1.label == e2.label:
                # Check for at least one shared attribute (excluding internals)
                attrs1 = {k: v for k, v in e1.attributes.items() if not k.startswith("_")}
                attrs2 = {k: v for k, v in e2.attributes.items() if not k.startswith("_")}
                
                shared_attrs = set(attrs1.items()) & set(attrs2.items())
                
                if len(shared_attrs) > 0:
                    union(i, j)
                    
    cluster_mapping = {}
    for i in range(len(all_entities)):
        root = find(i)
        if root not in cluster_mapping:
            cluster_mapping[root] = str(uuid.uuid4())
        
        all_entities[i].entity_cluster_id = cluster_mapping[root]
        
    for e in all_entities:
        e.attributes.pop("_doc_cluster_id", None)
        
    return all_entities
