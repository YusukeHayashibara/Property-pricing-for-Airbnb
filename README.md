# Property Pricing for Airbnb — São Paulo

Which properties for sale in the city of São Paulo are the best options to build an Airbnb? This project combines multiple data sources to score real estate by **return on investment adjusted for crime risk and tourist appeal**.

Developed for **SSC0957 — Practical Data Science II**.

> **Scope note (2026-08-14):** the project shifted from Rio de Janeiro to São Paulo, matching the Inside Airbnb data in use. **Decisions (2026-09-07):** the cost source is **IPTU-SP** (municipal property register), the risk source is **SSP-SP** (crime by police district), and the common spatial unit is the **distrito** (96 in São Paulo). Rationale, join routes and open items: `obsidian-vault/09 - Spatial Aggregation.md`.

## The question

> Which regions and property profiles in São Paulo maximize the expected return of an Airbnb, once the return is adjusted for the surrounding crime risk and tourist attractiveness?

Rather than only listing cheap properties, the project treats the decision as a **spatial multi-criteria optimization**, following the causal chain:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

## Data sources

| Source | Role | What it provides |
|--------|------|------------------|
| IPTU-SP + GeoSampa | Cost (base) | Fiscal value per m², area and age of the whole property register (~3.8M rows), joined to the distrito through the fiscal block (99.94%) |
| FipeZAP | Price validation | Historical price index and trend |
| Inside Airbnb (São Paulo) | Revenue | Daily rate, estimated occupancy, listing attributes |
| Google Places / TripAdvisor | Tourism | Points of interest, location, ratings (OpenStreetMap POIs are the placeholder until a Google Places key is available) |
| Google Street View | Images of streets | Security analysis based in images |
| SSP-SP + IBGE Censo 2022 | Risk | Monthly occurrences by police district (DP), mapped to the distrito with a reviewed crosswalk; rates per 100k residents |

> **Note on real estate data:** IPTU-SP values are *fiscal* (median ≈ R$ 60/m²), not market prices, and FipeZAP is city-wide only. The project therefore works at the **distrito + property-profile** level: Inside Airbnb supplies attributes and revenue, IPTU-SP supplies a relative cost signal per distrito, and FipeZAP is a single trend deflator to calibrate the level.

## Method

1. **Aggregation** — collect, geocode, and integrate the sources; clean and diagnose data quality.
2. **Visual interpretation** — maps and charts (PySal, seaborn) to argue representativeness for the purpose.
3. **Modeling** — hedonic revenue model (scikit-learn), spatial analysis (PySal: Moran/LISA), and a composite investment score.

## Tools

- Python — pandas, geopandas
- PySAL (`libpysal`, `esda`, `splot`, `spreg`) — spatial weights, Moran/LISA, Getis-Ord, spatial regression
- scikit-learn — modeling
- seaborn — visualization

## Repository structure

```
.
├── data/            # raw/processed/external data (not versioned) + reference/ (versioned); see data/README.md
├── notebooks/       # aggregation, EDA (incl. spatial, images, text)
├── src/             # tested reusable code (bairro standardization so far)
├── scripts/         # reproducible scripts (population fetch, crime sensitivity, figures)
├── docs/            # data dictionary, analysis write-ups, timeline
├── obsidian-vault/  # shared knowledge base: sources, methodology, decisions, meetings
├── outputs/         # figures and tables used in the report and slides
└── README.md
```

## Status

Work in progress. Phase 1 (aggregation) and the exploratory spatial analysis of Phase 2 are done; modeling (Phase 3) has not started. See [docs/TIMELINE.md](docs/TIMELINE.md) for the 4-month plan and current progress, and `docs/notes/aggregation-open-items.md` for what is still open.

## Notes

- Confirm the current availability and format of each source (IPTU-SP/GeoSampa, SSP-SP, Inside Airbnb, IBGE) before refreshing the data, as coverage and formats change.
- Check the terms of use of any listing portal before automated collection.
