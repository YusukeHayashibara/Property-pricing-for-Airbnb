# Methodology

Expands on the causal chain in [[01 - Project Overview]]:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

## 1. Aggregation

Collect + geocode + integrate: [[ITBI]], [[FipeZAP]], [[Inside Airbnb]], [[Google Places - TripAdvisor]], [[ISP]]. Work at the **region + property-profile** level (see [[01 - Project Overview]] for why).

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

- #decision 2026-08-14: project scope shifted from Rio de Janeiro to **São Paulo**, since the Inside Airbnb data the team is working with is a São Paulo snapshot (confirmed via EDA in `notebooks/airbnb_analysis.ipynb` — neighborhood names and coordinates match São Paulo). Consequence: [[ITBI]] and [[ISP]] are Rio-specific and no longer fit; São Paulo equivalents still need to be found (open questions logged in those notes).
- #open-question 2026-08-14: not decided — possibly pivoting from "best property to buy for an Airbnb" to "best existing Airbnb listing/operation," adding Google Street View imagery as a signal, because ITBI/FipeZAP-style cost data lacks property attributes. See [[01 - Project Overview]] → "Possible pivot" for detail. Log the outcome here once the team decides.
