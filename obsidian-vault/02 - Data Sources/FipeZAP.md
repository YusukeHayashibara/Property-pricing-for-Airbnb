# FipeZAP

**Role:** Price validation

## What it provides

Historical residential price index and trend by region, published jointly by FIPE and ZAP.

## How we use it

Calibrate the **level** and trend of the cost source (IPTU-SP fiscal values, see [[ITBI]]), which are not market prices. FipeZAP is city-wide only, so it acts as a single deflator, not a per-distrito input.

## Open questions

- ~~Is the FipeZAP index available at neighborhood granularity for São Paulo, or only city-wide?~~ #decision (2026-09-07): treat as city-wide / trend-only — it is a single global price-trend deflator, not a per-distrito cost input. See [[09 - Spatial Aggregation]].
- #open-question Licensing/terms of use for redistribution in the project report.

## Links

- [[ITBI]]
- [[05 - Methodology]]
