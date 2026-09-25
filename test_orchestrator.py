import json
from unittest.mock import patch
from ml_core.orchestrator import analyze_incident

def mock_call_local_llm(prompt, error_msg=None):
    # This simulates what LM Studio / SmolLM would return
    mock_response = [
        {
            "subject": "John",
            "action": "saw",
            "object": "a red car",
            "is_explicit_denial": False,
            "source_span": [0, 15]
        }
    ]
    return json.dumps(mock_response)

@patch('ml_core.orchestrator.call_local_llm', side_effect=mock_call_local_llm)
def run_mock_test(mock_llm):
    statements = [
        "I saw a red car speed past the traffic light.",
        "The black sedan didn't stop at the red light."
    ]
    
    print("Running orchestrator with mocked LM Studio...")
    result = analyze_incident(statements)
    
    print("\n--- TEST RESULTS ---")
    print(f"Entities: {result['metrics']['total_entities']}")
    print(f"Events: {result['metrics']['total_events']}")
    print(f"Contradictions: {result['metrics']['total_contradictions']}")
    print("Status:", result['status'])
    
    assert result['status'] == 'success'
    assert result['metrics']['total_events'] == 2 # 1 mocked event per statement
    print("\nAll pipeline components (spaCy, sentence-transformers, clustering, detection) executed successfully!")

if __name__ == "__main__":
    run_mock_test()
