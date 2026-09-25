import json
import time
from pathlib import Path
from ml_core.orchestrator import analyze_incident

OUTPUT_FILE = Path("theft_case_output.json")

def test_theft_case():
    print("=" * 80)
    print(" SILENT WITNESS — DETAILED MULTI-WITNESS THEFT CASE (5 WITNESSES)")
    print("=" * 80)

    # 5 rich, detailed eyewitness testimonies for a major jewelry store heist
    witness_statements = [
        # Witness 1: Store Security Guard (Inside the showroom)
        "At approximately 8:15 PM, I was stationed by the glass doors of the Tanishq showroom on MG Road. "
        "Two masked robbers stormed inside shouting threats and ordered all customers to lie flat on the floor. "
        "The robbers were armed with black handguns and pointed them directly at the staff. "
        "The primary robber was wearing a dark leather jacket and blue jeans. "
        "They shattered the display cases and loaded diamond jewelry into canvas bags before running out.",

        # Witness 2: Tea Stall Vendor (Directly across the road)
        "I have run my tea stall opposite Tanishq for ten years and was preparing tea around 8:20 PM. "
        "Suddenly, three robbers sprinted out of the store entrance carrying heavy duffel bags. "
        "The robbers were not holding handguns; they were armed with heavy iron crowbars. "
        "They pushed past frightened pedestrians on the sidewalk as people screamed for police assistance.",

        # Witness 3: Auto Rickshaw Driver (Waiting at the intersection corner)
        "I was parked near the MG Road junction waiting for passengers when the commotion erupted. "
        "The primary robber was wearing a dark leather jacket and fled on a black motorcycle heading east. "
        "He revved the motorcycle loudly, weaving dangerously through traffic toward the central railway station.",

        # Witness 4: Pedestrian Shopper (Walking on the same sidewalk)
        "I was walking along MG Road when the thieves dashed out into the evening crowd. "
        "The primary robber was wearing a bright red hoodie with beige cargo pants. "
        "The robbers did not escape on a motorcycle; they escaped in a silver getaway sedan that sped west toward the highway. "
        "The sedan screeched its tires and nearly struck an oncoming bus as it fled.",

        # Witness 5: Store Cashier / Vault Manager (Behind the counter)
        "I was securing the cash register when the panic buttons were triggered at 8:30 PM. "
        "The thieves took fifty lakhs worth of diamond necklaces and luxury watches from the vault counters. "
        "The emergency sirens began blaring as soon as they exited the building."
    ]

    roles = [
        "Witness 1 (Store Security Guard - Inside Showroom)",
        "Witness 2 (Tea Vendor - Directly Across the Street)",
        "Witness 3 (Auto Rickshaw Driver - Corner Intersection)",
        "Witness 4 (Pedestrian Shopper - Sidewalk Eyewitness)",
        "Witness 5 (Store Cashier - Behind Vault Counter)"
    ]

    print("\n--- INPUT WITNESS STATEMENTS (RICH & DETAILED) ---")
    for role, text in zip(roles, witness_statements):
        print(f"\n[{role}]:\n\"{text}\"")

    print("\n" + "-" * 80)
    print("Executing full NLP pipeline via local SmolLM-3B (http://172.19.121.89:1234)...")
    start_time = time.time()

    # Run the central orchestrator
    result = analyze_incident(witness_statements)
    elapsed = time.time() - start_time

    # Save to JSON file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Pipeline completed in {elapsed:.2f} seconds!")
    print(f"Structured JSON output saved to: {OUTPUT_FILE.resolve()}")
    print("-" * 80)

    # Display Metrics & Summary
    print("\n--- EXTRACTION & CONTRADICTION SUMMARY ---")
    print(f"Total Witnesses/Statements : {result['metrics']['total_statements']}")
    print(f"Entities Recognized (NER)  : {result['metrics']['total_entities']}")
    print(f"Events Extracted (S-V-O)   : {result['metrics']['total_events']}")
    print(f"Claims Generated           : {result['metrics']['total_claims']}")
    print(f"Contradictions Flagged     : {result['metrics']['total_contradictions']}")

    # Display clean JSON preview on terminal
    print("\n" + "=" * 80)
    print(" TERMINAL DISPLAY: STRUCTURED JSON OUTPUT")
    print("=" * 80)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_theft_case()
