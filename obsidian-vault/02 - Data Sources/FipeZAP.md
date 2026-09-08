# FipeZAP

**Role:** Price validation

## What it provides

Historical residential price index and trend by region, published jointly by FIPE and ZAP.

## How we use it

Cross-check/validate [[ITBI]] transaction prices and capture price trend over time, since ITBI is transaction-level and can be noisy at fine granularity.

## Open questions

- ~~Is the FipeZAP index available at neighborhood granularity for São Paulo, or only city-wide?~~ #decision (2026-09-07): treat as city-wide / trend-only — it is a single global price-trend deflator, not a per-distrito cost input. See [[09 - Spatial Aggregation]].
- #open-question Licensing/terms of use for redistribution in the project report.

## Links

- [[ITBI]]
- [[05 - Methodology]]
