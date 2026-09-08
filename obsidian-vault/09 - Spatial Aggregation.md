---
date: 2026-09-07
tags: [decision, aggregation]
---

# Spatial Aggregation Strategy

Resolves the central Phase 1 question from [[Inside Airbnb]]:

> How do we spatially join Inside Airbnb listings to the São Paulo cost/risk microregions?

And the related open questions in [[ITBI]] (granularity of the cost source), [[ISP]] (AISP / police-district boundaries don't align), and [[FipeZAP]] (neighborhood vs city-wide index).

> #decision (2026-09-07): the common spatial unit for the whole pipeline is the **distrito** (São Paulo has 96). Every source is normalized to a `distrito` key before any feature is built. The investment score is produced at the `distrito × property-profile` level. Logged in [[05 - Methodology]].

## For the team — what to review

This note is the full record of how we picked the spatial unit for the pipeline.
Read it and push back if the reasoning doesn't hold. Structure:

1. **Why "distrito"** — the argument, and the units we rejected.
2. **The crime problem** — the one weak spot, and the two ways to handle it.
3. **Join key, source by source** — how each dataset connects to `distrito`.
4. **Study results (2026-09-07)** — we actually ran the joins; the numbers are here.
5. **Next steps** and **What's still missing** — what to do from here.

> **Decision to ratify at the next weekly sync:** distrito as the pipeline unit, and
> default to crime treatment **A** (impute the DP rate) until Phase 2 says otherwise.
> If nobody objects, it's settled.

### How this was decided

A short feasibility study (2026-09-07): the throwaway notebook
`notebooks/spatial_aggregation_study.ipynb` on branch `feature/spatial-aggregation`
tested whether the joins actually work; results are written back here. Spec:
`docs/specs/2026-09-07-spatial-aggregation.md`. No `src/` code was
written; that is a separate, later decision (see Next steps).

---

## Why "distrito" is the right unit

The four datasets speak three incompatible spatial vocabularies, and only one carries geometry:

| Dataset | Spatial key it exposes | Geometry |
|---|---|---|
| [[Inside Airbnb]] `listings.csv` | `neighbourhood_cleansed` = one of the 96 **distritos**; `neighbourhood_group_cleansed` = one of the 32 subprefeituras | latitude / longitude ✔ |
| [[ITBI]] → **IPTU-SP** `iptu_2025.csv` | `logradouro` + `numero_imovel`, `bairro` (IPTU's own vocabulary), `cep`, `numero_contribuinte` (SQL = setor-quadra-lote) | none |
| [[ISP]] → **SSP-SP** crime data | `DP` → derived `bairro` (~94 police-district labels), yearly counts | none |
| [[FipeZAP]] | city-wide index, at best a few macro-zonas for São Paulo | none |

The unit has to satisfy four constraints at once. Only the distrito does:

1. **Official geometry exists.** GeoSampa publishes the 96-distrito shapefile. Subprefeitura and DP catchments either lose too much resolution or have no clean published boundary.
2. **Native match to the revenue source.** Inside Airbnb already labels every listing with its distrito (`neighbourhood_cleansed`); no reconstruction needed, just point-in-polygon validation.
3. **Enough sample per unit.** ~42k listings over 96 distritos. The distribution is skewed (central distritos have thousands, peripheral ones tens), but medians are still estimable everywhere. A finer unit (setor censitário, grid) would leave most cells with a handful of listings and no crime data at all.
4. **Crime is mappable to it.** ~94 DPs vs 96 distritos — close to 1:1. A manual DP→distrito crosswalk is feasible and small (the crime notebook already contains a hand-built 94-entry dictionary for the same kind of mapping).

It is also **report-defensible**: "distrito" is a standard unit of São Paulo urban analysis that the course staff will recognize without explanation.

### Units considered and rejected

- **Subprefeitura (32)** — too coarse; washes out the price variation the hedonic model depends on.
- **Setor censitário / regular grid** — too fine; Airbnb sample per cell collapses, crime data does not exist at that level.
- **DP catchment (~94)** — driven by the crime data, but SSP-SP does not publish a clean police-district shapefile, so the geometry would have to be reconstructed by hand.
- **CEP-based** — native to IPTU, but Airbnb and crime would still need a CEP mapping, so it just moves the problem.

---

## The granularity ceiling is set by the crime data

DP boundaries do not nest inside distritos: some DPs cover more than one distrito, some distritos are served by more than one DP. This is the tightest constraint in the whole join.

Two acceptable treatments, to be chosen during Phase 2 and logged in [[05 - Methodology]]:

- **(A) Impute the DP rate to the distrito** — assign each distrito the crime rate of its primary DP. Simple, keeps the distrito grain, introduces ecological error at DP boundaries.
- **(B) Aggregate up on conflict** — where a DP spans several distritos, collapse those distritos into one scoring unit. Fewer units, no ecological error, less spatial resolution.

Default to (A); switch to (B) only if the Phase 2 representativeness check (below) shows the imputation distorts the score ranking.

---

## Join key, source by source

### Inside Airbnb — revenue
- Use `neighbourhood_cleansed` directly.
- Validate with a point-in-polygon join of (`latitude`, `longitude`) against the GeoSampa distrito shapefile; flag and inspect mismatches.
- Property attributes (`room_type`, `bedrooms`, `accommodates`, `bathrooms`, …) feed the property-profile dimension, not the spatial key.

### IPTU-SP — cost
- **Chosen route (study-validated): `numero_contribuinte` (SQL) → `quadra_fiscal` → distrito.** The first 6 digits of the contribuinte number are the fiscal sector + block; join them to the GeoSampa `quadra_fiscal` polygons (64k of them), take each block's representative point, point-in-polygon to distrito. Maps **99.94%** of the 3.8M IPTU rows, covers all 96 distritos, needs **no geocoding**. Lookup cached as `data/external/quadra_to_distrito.csv`.
- Rejected: the `cep` route (never needed — SQL was cleaner) and the `bairro` route (free text, ~96k dirty values, 14% match).
- Cost signal per distrito: median value per m², filtered to residential `finalidade_imovel` (filter already in `notebooks/iptu_analysis.ipynb`). Note the study used `valor_construcao`, which is a *fiscal* value (~R$60/m² median) — not market price. The level needs FipeZAP calibration; the join itself is settled.

### SSP-SP — crime risk
- Build a manual **DP → distrito crosswalk** (~94 rows). Start from the 94-entry dictionary already in `notebooks/crime_analysis.ipynb` and re-map it from the informal "perfil" labels to actual distrito names.
- Convert counts to a **rate per 100k inhabitants** — requires population by distrito (see Gaps).
- Use occurrences only (`df_ocorrencias` in the notebook already strips the "Nº DE VÍTIMAS" categories to avoid double-counting).
- Decide the crime basket (violent vs property crime) — open question still live in [[ISP]].

### FipeZAP — price validation
- São Paulo index is city-wide (a few macro-zonas at best), so it **cannot** be a per-distrito cost input.
- Role: a single global price-trend deflator, to bring the IPTU 2025 values and the Airbnb 2026 snapshot onto a comparable time basis, and a sanity check on the overall IPTU price level.
- This resolves the [[FipeZAP]] open question: coarse, trend-only.

---

## Study results (2026-09-07)

Feasibility study run on branch `feature/spatial-aggregation`, notebook
`notebooks/spatial_aggregation_study.ipynb`, spec
`docs/specs/2026-09-07-spatial-aggregation.md`.

> #decision (2026-09-07): the distrito unit is **confirmed workable for cost and
> revenue**. Crime remains the weak link and needs a hand-built crosswalk.

| Join | Winning route | Coverage | Confidence |
|---|---|---|---|
| Airbnb → distrito | `neighbourhood_cleansed` as-is | 100% (0 disagreements with point-in-polygon, 0 points outside) | high — Inside Airbnb already did the PIP against these exact boundaries |
| IPTU → distrito | `numero_contribuinte`[:6] (fiscal sector+block) → GeoSampa `quadra_fiscal` polygon → point-in-polygon | 99.94% of 3.8M rows, 96/96 distritos, **no geocoding** | high |
| Crime → distrito | hand-built + reviewed `dp,distrito` lookup | only ~71/96 distritos get a DP; ~25 need imputation | **low** |
| POI → distrito | OSM Overpass (placeholder) | 69/96 non-zero, central-biased | low — Google Places still required |

## Aggregation output (2026-09-08, branch `feature/final-aggregation`)

> #decision (2026-09-08, with Yusuke): the **modeling table is at listing grain** —
> one row per Airbnb listing, with crime / IPTU / POI attached as columns of the
> listing's distrito. The per-distrito table is a secondary EDA / maps view. Both are
> the same join; the study aggregated to distrito only to validate the join and draw
> the maps.

Notebook `notebooks/aggregation.ipynb` produces two git-ignored files:

| File | Grain | Rows × cols |
|---|---|---|
| `data/processed/listings_aggregated.csv` | 1 listing | 42,354 × 28 |
| `data/processed/distrito_features.csv` | 1 distrito | 96 × 8 |

Column dictionary: `docs/data-dictionary-aggregation.md`.

Crime handling in this build: `dp_distrito_crosswalk.csv` (geocoded + 9 hand-mapped);
the 25 distritos with no DP take their **nearest** distrito's value, flagged in
`crime_source`. This is a placeholder — the crosswalk still needs the team's manual
review and a real imputation rule.

Route notes:
- **IPTU `bairro` route is dead** — free text, ~96k dirty distinct values, 14% match.
  The CEP route was not needed; the SQL route won outright.
- **Crime**: DP labels are *not* a partition of the distritos. Name-matching covers
  48/94; bounded Nominatim geocoding gets 85/94; 9 informal names hand-mapped (flagged
  `manual-review` in the crosswalk). Treatment A (impute DP rate) vs B (sum DPs per
  distrito) correlate only at **Spearman ρ ≈ 0.79** — the choice changes the ranking, so
  it must be made deliberately in Phase 2.
- **IPTU cost level is meaningless as-is** — `valor_construcao` is a fiscal value
  (median ≈ R$60/m²), not market price. The join is validated; calibration is a later
  FipeZAP concern.

Artifacts (all git-ignored under `data/`): `data/external/{distrito_municipal.geojson,
quadra_fiscal.gpkg, quadra_to_distrito.csv, dp_to_distrito.csv, poi_by_distrito.csv}`,
`data/interim/distrito_features_study.csv`.

---

## Step-by-step execution

1. **Acquire boundaries and lookups** (`data/external/`) — study already cached these
   - GeoSampa WFS `geoportal:distrito_municipal` (96 polygons).
   - GeoSampa WFS `geoportal:quadra_fiscal` (64k polygons) → `quadra_to_distrito.csv`.
   - Population by distrito (SEADE or IBGE Censo 2022) — **still missing**.
2. **Normalize each source to a `distrito` key** (`src/cleaning/`)
   - `airbnb`: use `neighbourhood_cleansed` directly (study: 100% = point-in-polygon).
   - `iptu`: `numero_contribuinte`[:6] → `quadra_fiscal` → distrito (study: 99.94%); residential filter; per-distrito median value/m².
   - `crime`: hand-built reviewed `dp,distrito` lookup (geocoding is only a first draft); occurrences only; impute the ~25 DP-less distritos; per-distrito annual count.
   - Output: one tidy table per source, keyed by `distrito`.
3. **Build the feature table** (`src/features/`)
   - Grain: `distrito × property_profile`.
   - Columns: cost per m² (IPTU), estimated revenue and occupancy (Airbnb `estimated_revenue_l365d`, `estimated_occupancy_l365d`), crime rate per 100k, POI / tourist-appeal density (Google Places — not yet collected, see Gaps).
   - Derive property profiles by clustering Airbnb attributes into ~4–6 groups.
4. **Phase 2 representativeness check** (`notebooks/`, `src/visualization/`)
   - Moran's I / LISA on cost, revenue, and crime at distrito level (PySal).
   - Compare within-distrito vs between-distrito variance for the key signals — confirm the join did not wash out meaningful spatial variation (the Phase 2 milestone in [[04 - Timeline & Milestones]]).
   - Re-evaluate the crime treatment (A vs B above) and the IPTU route (CEP vs SQL) here.
5. **Composite investment score** (`src/modeling/`)
   - Hedonic revenue model on `distrito × profile`.
   - Combine cost, revenue, crime, and tourist appeal into one rankable score per `distrito × profile` (z-score normalize components first — units differ by orders of magnitude).

---

## Next steps — from here

The study answered "does the join work". It did, for cost and revenue. From here:

1. **Ratify the decision** at the next weekly sync (distrito + crime treatment A default).
2. **Fix the crime crosswalk** — the one real weakness. Build an explicit, reviewed
   94-row `dp,distrito` table (start from `data/external/dp_to_distrito.csv`, review
   every row, replace the 9 `manual-review` guesses, decide how to fill the ~25
   distritos with no DP: nearest neighbour, or subprefectura average).
3. **Get Google Places** — obtain `GOOGLE_PLACES_API_KEY`, decide POI categories that
   count as tourist appeal (open in [[Google Places - TripAdvisor]]), collect for SP,
   replace the OSM placeholder.
4. **Get population by distrito** (SEADE or IBGE Censo 2022) so crime counts become
   rates per 100k.
5. **Close the crime open questions in [[ISP]]** — crime basket (violent vs property),
   time window (full-year 2025 vs trailing 12 months).
6. **Decide whether to build the real `src/` pipeline** — promote the exploratory study
   code into tested `src/cleaning/`, `src/features/`, `src/modeling/` packages. This is
   a bigger decision and needs its own design discussion before any coding. Could be
   sliced: `src/cleaning/` alone delivers the Phase 1 milestone (one clean
   `distrito`-keyed table per source).
7. **Phase 2 representativeness check** (Moran/LISA, within- vs between-distrito
   variance) — this is where the crime treatment A-vs-B and the score design get
   validated.

## What's still missing — checklist

- [ ] Decision ratified by the team
- [ ] Reviewed `dp,distrito` crosswalk (94 rows) + imputation rule for DP-less distritos
- [ ] `GOOGLE_PLACES_API_KEY` + POI category list + collected Places data for SP
- [ ] Population by distrito (SEADE / IBGE 2022)
- [ ] Crime basket decided ([[ISP]])
- [ ] Crime time window decided ([[ISP]])
- [ ] FipeZAP deflation base chosen (IPTU 2025 ↔ Airbnb 2026-06)
- [ ] Go / no-go on building `src/` (needs a design discussion)
- [ ] [[ITBI]] and [[ISP]] source notes updated to drop the Rio framing (data + EDA already in repo; only [[05 - Methodology]] decision log updated so far)

### Already done (2026-09-07)

- [x] Spatial unit chosen and justified (this note)
- [x] Join routes validated for Airbnb, IPTU, POI; crime route scoped
- [x] GeoSampa layers downloaded and cached (`data/external/`)
- [x] `quadra_to_distrito.csv` lookup built (IPTU → distrito)
- [x] First-draft `dp_to_distrito.csv` crosswalk (geocoded, needs review)
- [x] Study notebook + spec committed to `feature/spatial-aggregation` (PR #2)
- [x] Grain decided with the team: listing-level modeling table (2026-09-08)
- [x] `notebooks/aggregation.ipynb` + `data/processed/{listings_aggregated,distrito_features}.csv` (branch `feature/final-aggregation`)
- [x] Data dictionary: `docs/data-dictionary-aggregation.md`

---

## Links

- [[05 - Methodology]] — decision log
- [[01 - Project Overview]] — region + property-profile framing
- [[04 - Timeline & Milestones]] — Phase 1 (aggregation) and Phase 2 (representativeness) milestones
- Data source notes: [[Inside Airbnb]], [[ITBI]], [[ISP]], [[FipeZAP]], [[Google Places - TripAdvisor]]
- EDA notebooks: `notebooks/airbnb_analysis.ipynb`, `notebooks/iptu_analysis.ipynb`, `notebooks/crime_analysis.ipynb`
- Study (branch `feature/spatial-aggregation`): `notebooks/spatial_aggregation_study.ipynb`, spec `docs/specs/2026-09-07-spatial-aggregation.md`
