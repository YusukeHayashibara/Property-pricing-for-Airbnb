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

## Design decisions log

> Append dated entries here when a methodology choice is made (e.g., "2026-08-13: chose z-score normalization before combining score components because raw units differ by orders of magnitude"). Tag with #decision.
