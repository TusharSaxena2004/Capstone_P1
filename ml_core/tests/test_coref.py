import pytest
from ml_core.schema.models import Entity, Statement
from ml_core.extraction.coref import resolve_single_document_coref, resolve_cross_statement_coref

def test_single_document_coref():
    stmt = Statement(
        id="stmt_1",
        witness_id="w_1",
        text="A man ran from the store. He was wearing a red jacket. The man dropped something as he ran.",
        incident_id="inc_1"
    )
    
    entities = [
        Entity(source_statement_id="stmt_1", source_span=(2, 5), text="man", label="PERSON", attributes={"gender": "male"}),
        Entity(source_statement_id="stmt_1", source_span=(26, 28), text="He", label="PERSON", attributes={}),
        Entity(source_statement_id="stmt_1", source_span=(55, 62), text="The man", label="PERSON", attributes={}),
        Entity(source_statement_id="stmt_1", source_span=(84, 86), text="he", label="PERSON", attributes={})
    ]
    
    resolved = resolve_single_document_coref(stmt, entities)
    
    assert len(resolved) == 4
    
def test_cross_statement_coref():
    # Witness 1
    e1 = Entity(source_statement_id="s1", source_span=(0,5), text="sedan", label="VEHICLE", attributes={"color": "red", "make": "honda"})
    e2 = Entity(source_statement_id="s1", source_span=(20,23), text="car", label="VEHICLE", attributes={"_doc_cluster_id": "doc1_1"})
    
    # Witness 2
    e3 = Entity(source_statement_id="s2", source_span=(0,5), text="vehicle", label="VEHICLE", attributes={"color": "red"})
    e4 = Entity(source_statement_id="s2", source_span=(10,13), text="man", label="PERSON", attributes={"clothing": "black"})
    
    # Witness 3
    e5 = Entity(source_statement_id="s3", source_span=(0,3), text="guy", label="PERSON", attributes={"clothing": "black"})
    
    all_entities = [e1, e2, e3, e4, e5]
    
    e1.attributes["_doc_cluster_id"] = "doc1_1"
    
    resolved = resolve_cross_statement_coref([], all_entities)
    
    assert resolved[0].entity_cluster_id == resolved[1].entity_cluster_id
    assert resolved[0].entity_cluster_id == resolved[2].entity_cluster_id
    assert resolved[3].entity_cluster_id == resolved[4].entity_cluster_id
    assert resolved[0].entity_cluster_id != resolved[3].entity_cluster_id
    
    assert "_doc_cluster_id" not in resolved[0].attributes
