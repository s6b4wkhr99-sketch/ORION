# Volume 10 — Business Rule Library

Authoritative repository for every business rule in CIOS.

## Implementation

| Module | Purpose |
|--------|---------|
| `backend/app/rules/library.py` | All Rule IDs, execution order, dependency matrix |
| `backend/app/rules/upload.py` | RULE-UP-001, RULE-UP-002 enforcement |
| `backend/app/intelligence/` | Volume 04 implementation rules (Rule-005–070) |
| `backend/app/intelligence/types.py` | Trace links implementation → business Rule ID |

## Rule Categories

UP, VAL, MAP, DAT, ZIP, PRZ, SEG, PUR, PAI, LIF, REC, CAM, FOR, LRN

## Execution Order (Section 18)

Upload → Validation → Mapping → Database → Datalogix → ZIP → PRIZM → Purchase Power → Pain → Lifestyle → Ceragem Segment → Recommendation → Campaign → Forecast → Export → Campaign Report → Learning

## Forecast Formulas

| Rule ID | Formula |
|---------|---------|
| RULE-FOR-001 | Expected Orders = Target Customers × Conversion Rate |
| RULE-FOR-002 | Expected Revenue = Expected Orders × Product Price |
| RULE-FOR-003 | Le Frame Incentive = Expected Revenue × 15% |
| RULE-FOR-004 | Forecast Accuracy = Actual Revenue ÷ Expected Revenue |

## Tests

```bash
cd backend && python tests/test_volume10_acceptance.py
```
