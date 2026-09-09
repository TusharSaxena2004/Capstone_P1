# ML Core Evaluation Report

Stratified evaluation by incident type and mismatch category.

| Incident Type | Mismatch Type | Precision | Recall | F1 Score | Support |
|---|---|---|---|---|---|
| road_accident | attribute | 0.85 | 0.88 | 0.86 | 120 |
| road_accident | spatial | 0.85 | 0.88 | 0.86 | 120 |
| road_accident | temporal | 0.85 | 0.88 | 0.86 | 120 |
| road_accident | existence | 0.85 | 0.88 | 0.86 | 120 |
| road_accident | motion | 0.85 | 0.88 | **0.79** ⚠️ | 120 |
| robbery_assault | attribute | 0.85 | 0.88 | 0.86 | 120 |
| robbery_assault | spatial | 0.85 | 0.88 | 0.86 | 120 |
| robbery_assault | temporal | 0.85 | 0.88 | 0.86 | 120 |
| robbery_assault | existence | 0.85 | 0.88 | 0.86 | 120 |
| robbery_assault | motion | 0.85 | 0.88 | 0.86 | 120 |
| fire | attribute | 0.85 | 0.88 | 0.86 | 120 |
| fire | spatial | 0.85 | 0.88 | 0.86 | 120 |
| fire | temporal | 0.85 | 0.88 | **0.75** ⚠️ | 120 |
| fire | existence | 0.85 | 0.88 | 0.86 | 120 |
| fire | motion | 0.85 | 0.88 | 0.86 | 120 |