# Data dictionary — aggregation outputs

Produced by `notebooks/aggregation.ipynb` (branch `feature/final-aggregation`).
Both files are git-ignored (`data/processed/`). Spatial-unit rationale:
`obsidian-vault/09 - Spatial Aggregation.md`.

This build is **deliberately wide** — every column that could be derived is kept.
Column selection / cleaning is the next step.

## `data/processed/listings_aggregated.csv`

One row per Airbnb listing (**42,354 × ~188**). The modeling table.
= all non-empty `listings.csv` columns + `price_num` + every column of
`distrito_features.csv`, joined on `distrito`.

### Listing attributes (~79 cols)

Straight from Inside Airbnb `listings.csv` (13 always-empty columns dropped:
`host_since`, `license`, `instant_bookable`, `neighbourhood`, …). See the Inside Airbnb
data dictionary for these. Added:

| Column | Meaning |
|---|---|
| `price_num` | nightly price in BRL, parsed from the `price` string |
| `distrito` | normalised distrito key (uppercase, no accents) — the join key |

### Distrito features (~109 cols, constant within a distrito)

**Meta**

| Column | Meaning |
|---|---|
| `regiao5`, `regiao8` | 5- and 8-way macro-region of São Paulo |
| `subprefeitura_cd` | subprefeitura code |
| `area_km2` | distrito area |

**IPTU-SP 2025** — residential lots only, `iptu_*` (13). Fiscal *venal* values —
**below market**, need FipeZAP calibration.

| Column | Meaning |
|---|---|
| `iptu_n` | residential lots behind the stats |
| `iptu_venal_m2_median` / `_mean` / `_p25` / `_p75` | venal value per m² of built area = `(valor_terreno + valor_construcao) / area_construida` |
| `iptu_terreno_m2_median` | land value per m² of land |
| `iptu_constr_m2_median` | construction value per m² built |
| `iptu_venal_total_median` | total venal value per lot |
| `iptu_area_constr_median`, `iptu_area_terreno_median` | median areas (m²) |
| `iptu_idade_median` | median building age (`ano − ano_construcao`) |
| `iptu_pavimentos_median` | median number of floors |
| `iptu_share_apto` | share of lots that are apartment/flat |

**Crime (SSP-SP 2025)** — `crime_*` (~22). Per-DP mean of occurrences (occurrences
only, "Nº DE VÍTIMAS" categories excluded).

| Column | Meaning |
|---|---|
| `crime_<categoria>` | 2025 count for each `NATUREZA2` (e.g. `crime_furto_outros`, `crime_roubo_de_veiculo`, `crime_homicidio_doloso`, …) |
| `crime_total` | sum of all categories |
| `crime_patrimonial` | furto + roubo categories |
| `crime_violento` | homicídio / latrocínio / lesão seguida de morte / tentativa / estupro / roubo |
| `crime_total_2024` | same total for 2024 (trend) |
| `crime_n_dp` | number of DPs mapped into the distrito |
| `crime_source` | `dp-direct` or `nearest-imputed` (25 distritos with no DP inherit the nearest distrito's row) |

**POI (OpenStreetMap, placeholder for Google Places)** — `poi_*` counts and
`poidens_*` per-km² densities (~71). One pair per category:
`tourism_museum`, `tourism_attraction`, `tourism_hotel`, `tourism_viewpoint`,
`historic`, `leisure_park`, `amenity_restaurant`, `amenity_bar`, … plus `poi_total` /
`poidens_total`.

## `data/processed/distrito_features.csv`

One row per distrito (**96 × ~109**), indexed by `distrito`. The distrito-feature block
above on its own. Secondary view for EDA, maps, Phase 2 spatial checks.

## Known gaps

Tracked in `09 - Spatial Aggregation.md`:

- Crime crosswalk (`data/external/dp_distrito_crosswalk.csv`) needs manual review;
  nearest-distrito imputation is a placeholder.
- No population → crime is a raw count, not a rate per 100k.
- POI is OSM, not Google Places.
- IPTU value is fiscal, not deflated market price.
- Property-profile dimension not built yet (listing attributes still raw).
- Column set is intentionally over-wide; needs pruning.
