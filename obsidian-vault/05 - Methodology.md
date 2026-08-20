# Methodology

Expands on the causal chain in [[01 - Project Overview]]:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

## 1. Aggregation

Collect + geocode + integrate: [[ITBI - Data.Rio]], [[FipeZAP]], [[Inside Airbnb]], [[Google Places - TripAdvisor]], [[ISP-RJ]]. Work at the **region + property-profile** level (see [[01 - Project Overview]] for why).

Corresponds to `src/collection/` and `src/cleaning/` in the code repo.

## 2. Visual interpretation

Maps and charts (PySal, seaborn) to argue the aggregated data is representative for the purpose — i.e., that the microregion-level joins didn't wash out meaningful spatial variation.

Corresponds to `src/visualization/` and `notebooks/`.

## 3. Modeling

- **Hedonic revenue model** (scikit-learn) — estimate expected Airbnb revenue from property profile + location features.
- **Spatial analysis** (PySal: Moran's I / LISA) — detect spatial autocorrelation/clusters in price, revenue, crime.
- **Composite investment score** — combine cost, revenue, tourist appeal, and crime risk into a single rankable score per region + profile.

Corresponds to `src/features/` and `src/modeling/`.

## 4. Final candidate scoring

The composite score from step 3 lives at the **region + property-profile** level (e.g., "2-bed apartments in Copacabana, 60-80m²"), not per specific property. To go from that to actual buy recommendations:

- Once the region+profile ranking is available, collect a **small, one-off, non-recurring** snapshot of active for-sale listings (ZapImóveis and/or VivaReal/QuintoAndar as alternatives — see [[ZapImoveis - Scraping Assessment]]) limited to the top-ranked regions/profiles. Not a continuous pipeline, not redistributed as a dataset.
- Apply the already-trained model to each real listing's own attributes (asking price, area, bedrooms, neighborhood) to produce a per-property investment score.
- Final output: a ranked list of real candidate properties (address/link, asking price, score) — not just an abstract profile.

Corresponds to a new `src/collection/listings_snapshot.py` module (not yet implemented; scoped small and separate from the main `src/collection/` sources, since it's the only source involving a commercial listing portal rather than public/API data).

Corresponds to `src/features/` and `src/modeling/` for the scoring reuse.

## Design decisions log

> Append dated entries here when a methodology choice is made (e.g., "2026-08-13: chose z-score normalization before combining score components because raw units differ by orders of magnitude"). Tag with #decision.

- 2026-08-20: added a "Final candidate scoring" step to go from region+profile scores to real buy candidates, since none of ITBI/IPTU/FipeZAP/SECOVI contain active for-sale listings — only a listings portal snapshot can. Scoped as a small, one-off collection at the end of the pipeline, not a continuous scraping pipeline. #decision
