# Feasibility Study: Spatial Aggregation

**Date:** 2026-09-07
**Branch:** `feature/spatial-aggregation`
**Type:** Feasibility study — output is a recommendation; the notebook code is exploratory/throwaway
**Vault reference:** `obsidian-vault/09 - Spatial Aggregation.md`

## Question

Does the "everything to `distrito` (96)" join actually work with the data we
have, and for each source, which of the candidate routes is best?

Concretely:

1. **Airbnb → distrito** — can we trust `neighbourhood_cleansed`, or do we
   need a point-in-polygon join on `latitude`/`longitude`?
2. **IPTU-SP → distrito** — CEP-based route vs `bairro`-based route: which
   gives better coverage and accuracy?
3. **Crime (SSP-SP) → distrito** — how clean is the DP → distrito crosswalk,
   and does treatment A (impute the DP rate to the distrito) vs treatment B
   (aggregate distritos that share a DP) change the crime ranking?
4. **POI / tourist appeal** — can we get a usable per-distrito POI density
   from OpenStreetMap (Overpass) as a stand-in until Google Places is
   available?

## Output

- One exploratory notebook: `notebooks/spatial_aggregation_study.ipynb`.
- A `distrito`-level table with: median cost per m² (IPTU), estimated
  revenue (Airbnb), crime rate, POI density.
- A short written recommendation per join (which route won, with the
  numbers), fed back into `obsidian-vault/09 - Spatial Aggregation.md`.

## Test plan

| Step | What | Success metric |
|---|---|---|
| 0 | Load the 96-distrito boundary (GeoSampa WFS GeoJSON; fallback IBGE malha SP / geodata-br) | shapefile loads, 96 polygons, valid geometry |
| 1 | Airbnb: `neighbourhood_cleansed` vs point-in-polygon | % of listings where the two disagree; inspect the disagreements |
| 2 | IPTU route A (CEP): dedupe to unique CEP, geocode a random sample (Nominatim, N≈500) → point-in-polygon distrito | % IPTU rows with a CEP that resolves; agreement of geocoded distrito vs CEP-table distrito |
| 2b | IPTU route B (`bairro`): fuzzy-match IPTU `bairro` to distrito names | % rows matched; on the geocoded sample, does `bairro` predict the true distrito? |
| 3 | Crime: build explicit `dp,distrito` lookup from the 94-entry dict in `crime_analysis.ipynb` | # DPs mapping 1:1 vs # spanning multiple distritos vs # distritos with no DP |
| 3b | Crime treatments: compute per-distrito crime rate under A and under B | rank correlation (Spearman) between the two orderings; list distritos that move most |
| 4 | POI: Overpass query for tourism/leisure/historic POIs within the SP municipality, spatial join → count per distrito, normalize by area | POIs returned, all fall inside a distrito, density spread looks plausible |
| 5 | Assemble the `distrito × {cost, revenue, crime, poi}` table | table has 96 rows, no all-NaN column |

## Known constraints / gaps carried in

- **Google Places not wired up.** POI step uses OSM Overpass. Swap for
  Places once `GOOGLE_PLACES_API_KEY` is in `.env`.
- **Population by distrito not in repo.** For the study, crime "rate" is
  per unit area (or raw count); true per-100k-inhabitants needs SEADE /
  IBGE Censo 2022 population and is out of scope here.
- **IPTU vintage 2025 vs Airbnb snapshot 2026-06.** Not deflated in the
  study; FipeZAP deflator is a later pipeline concern.
- **Environment.** Python 3.14, no conda. `geopandas` 1.1.4 installed ad
  hoc for the study; if this route is adopted, add it to
  `environment.yml` / `requirements.txt` (already listed there).
- **Nominatim usage policy.** Sample geocoding only (N≈500), 1 req/s,
  descriptive User-Agent. Not a bulk geocode.

## Not in scope

- Building `src/` packages (cleaning / features / modeling).
- Property-profile clustering.
- The composite investment score.
- FipeZAP deflation.
- Choosing the final crime basket / time window (open questions in
  `obsidian-vault/02 - Data Sources/ISP.md`).

## Decision criteria

For each join, the winning route is the one that maximizes matched rows
**and** holds up on the geocoded validation sample. If no route clears a
usable bar (say ~90% coverage, ~90% sample agreement), that is itself the
finding — record it and the fallback needed.
