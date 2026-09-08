---
date: 2026-09-07
tags: [decision, aggregation]
---

# Spatial Aggregation Strategy

Resolves the central Phase 1 question from [[Inside Airbnb]]:

> How do we spatially join Inside Airbnb listings to the São Paulo cost/risk microregions?

And the related open questions in [[ITBI]] (granularity of the cost source), [[ISP]] (AISP / police-district boundaries don't align), and [[FipeZAP]] (neighborhood vs city-wide index).

> #decision (2026-09-07): the common spatial unit for the whole pipeline is the **distrito** (São Paulo has 96). Every source is normalized to a `distrito` key before any feature is built. The investment score is produced at the `distrito × property-profile` level. Logged in [[05 - Methodology]].

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
- **Primary route: `cep` → distrito.** Join the IPTU `cep` against a CEP→distrito table built from the GeoSampa logradouros layer (which carries both CEP and distrito). One join, no geocoding, no multi-million-row lot shapefile. Boundary error is under ~5% of lots and irrelevant at distrito-level aggregation.
- **Fallback route: `numero_contribuinte` (SQL) → lot geometry.** Join the contribuinte number to the GeoSampa "Lotes fiscais IPTU" layer, then point-in-polygon to distrito. More exact, much heavier. Use only if the Phase 2 check shows CEP boundary leakage changes the cost ranking.
- Cost signal per distrito: median `valor_m2_construcao` (already derived in `notebooks/iptu_analysis.ipynb`), filtered to residential `finalidade_imovel` (filter already in that notebook).

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

## Step-by-step execution

1. **Acquire boundaries and lookups** (`data/external/`)
   - GeoSampa: 96-distrito shapefile.
   - GeoSampa: logradouros layer (for the CEP→distrito table) — or the "Lotes fiscais IPTU" layer if the fallback route is needed.
   - Population by distrito (SEADE or IBGE Censo 2022).
2. **Normalize each source to a `distrito` key** (`src/cleaning/`)
   - `airbnb`: point-in-polygon validation of `neighbourhood_cleansed`.
   - `iptu`: `cep` → distrito join; residential filter; per-distrito median `valor_m2_construcao`.
   - `crime`: DP→distrito crosswalk; occurrences only; per-distrito annual count.
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

## Gaps — must close before or during execution

- **Google Places / TripAdvisor data not collected yet.** The tourist-appeal term of the score has no input. Blocks step 3's POI column and step 5. See [[Google Places - TripAdvisor]] (POI categories and API-key ownership still open).
- **Population by distrito not in the repo.** Needed to turn crime counts into rates (step 2, `crime`). Source: SEADE or IBGE Censo 2022.
- **GeoSampa layers not downloaded.** Distrito shapefile, logradouros/CEP layer, and (conditionally) the IPTU lot layer. All of step 1.
- **DP→distrito crosswalk does not exist as data.** Only an informal per-"perfil" dictionary in the crime notebook. Must be rebuilt as an explicit `dp,distrito` lookup and reviewed for the DPs that span multiple distritos.
- **Crime basket undecided.** Which categories count toward guest-safety risk — open question in [[ISP]].
- **Crime time window undecided.** `data/raw/ISP/` has all 12 months of 2025; the notebook currently uses a single combined file. Decide: full-year 2025 total, or trailing 12 months. Open question in [[ISP]].
- **IPTU vintage vs Airbnb snapshot.** IPTU is 2025, Airbnb snapshot is 2026-06. FipeZAP deflator handles the price-level gap but the choice of deflation base needs to be logged.
- **`src/` does not exist yet.** No `cleaning`, `features`, `modeling`, or `visualization` packages — steps 2–5 all start from an empty `src/`.
- **Vault vs repo drift.** [[ITBI]] and [[ISP]] notes still describe the Rio sources as current and the SP replacements as "not yet researched", though IPTU-SP and SSP-SP data and EDA notebooks are already in the repo. Decision-log entries added to [[05 - Methodology]] on 2026-09-07; the source notes themselves still need updating.

---

## Links

- [[05 - Methodology]] — decision log
- [[01 - Project Overview]] — region + property-profile framing
- [[04 - Timeline & Milestones]] — Phase 1 (aggregation) and Phase 2 (representativeness) milestones
- Data source notes: [[Inside Airbnb]], [[ITBI]], [[ISP]], [[FipeZAP]], [[Google Places - TripAdvisor]]
- Notebooks: `notebooks/airbnb_analysis.ipynb`, `notebooks/iptu_analysis.ipynb`, `notebooks/crime_analysis.ipynb`
