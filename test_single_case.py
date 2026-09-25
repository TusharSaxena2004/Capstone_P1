import json
import time
from ml_core.orchestrator import analyze_incident

def test_single_incident():
    print("=" * 60)
    print(" SILENT WITNESS — SINGLE CASE TEST")
    print("=" * 60)
    
    statements = [
        "At 6:15 AM near Marine Drive, a black SUV sped through a red light and struck a cyclist.",
        "At 6:30 AM near Marine Drive, a white sedan driving with a green light struck a delivery boy on a motorbike."
    ]
    
    print("\n--- INPUT WITNESS STATEMENTS ---")
    for i, s in enumerate(statements, 1):
        print(f"Witness {i}: \"{s}\"")
        
    print("\nProcessing pipeline with local ML + SmolLM-3B (http://172.19.121.89:1234)...")
    start_time = time.time()
    
    result = analyze_incident(statements)
    elapsed = time.time() - start_time
    
    print(f"\nCompleted in {elapsed:.2f} seconds!")
    print("\n" + "=" * 60)
    print(" PIPELINE RESULTS (STRUCTURED JSON)")
    print("=" * 60)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_single_incident()
