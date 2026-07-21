# Volume 04 — Intelligence Engine

Implemented in `backend/app/intelligence/` with approved entry point `backend/app/segmentation/`.

Pipeline order (Section 21): Normalization → Datalogix → ZIP → PRIZM → Ceragem → Message Direction → Purchase Power → Pain Index → Lifestyle → Recommendation → Revenue Forecast.

Required outputs: PRIZM Proxy Segment, Ceragem Segment, Message Direction, Purchase Power, Pain Index, Lifestyle, Recommended Product, Expected Revenue, Campaign Priority.

**Principle 004:** Datalogix X/Y/Z/U values preserved as strings via `preserve_datalogix_value()`.
