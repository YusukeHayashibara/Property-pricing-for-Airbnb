# Data dictionary — aggregation outputs

Produced by `notebooks/aggregation.ipynb` (branch `feature/final-aggregation`).
Both files are git-ignored (`data/processed/`). Spatial-unit rationale:
`obsidian-vault/09 - Spatial Aggregation.md`.

## `data/processed/listings_aggregated.csv`

One row per Airbnb listing (42,354). The modeling table.

### Listing attributes (from Inside Airbnb `listings.csv`)

| Column | Meaning |
|---|---|
| `id` | Inside Airbnb listing id |
| `name` | listing title |
| `neighbourhood_cleansed` | distrito name as published by Inside Airbnb |
| `neighbourhood_group_cleansed` | subprefeitura |
| `latitude`, `longitude` | listing coordinates (obfuscated ~150 m by Inside Airbnb) |
| `room_type`, `property_type` | listing type |
| `accommodates`, `bedrooms`, `beds`, `bathrooms_text` | capacity |
| `price_num` | nightly price in BRL, parsed from the `"$1.234,56"` string |
| `minimum_nights` | minimum stay |
| `availability_365` | nights available in the next 365 days |
| `number_of_reviews`, `review_scores_rating` | review volume and score |
| `estimated_occupancy_l365d` | Inside-Airbnb-modelled occupancy, last 365 days (proxy) |
| `estimated_revenue_l365d` | Inside-Airbnb-modelled revenue, last 365 days (proxy) |

### Distrito context (broadcast onto every listing in the distrito)

| Column | Meaning | Source |
|---|---|---|
| `distrito` | normalised distrito key (uppercase, no accents) | join key |
| `regiao` | one of the 5 macro-regions (`nm_regiao_05`) | GeoSampa |
| `area_m2` | distrito area in m² | GeoSampa |
| `iptu_venal_m2_median` | median residential venal value per m² — `(valor_terreno + valor_construcao) / area_construida`. **Fiscal value, well below market**; needs FipeZAP calibration | IPTU-SP 2025 |
| `iptu_n_imoveis` | residential lots behind the median | IPTU-SP 2025 |
| `crime_occurrences_2025` | total police occurrences in 2025 for the distrito's DP (mean if >1 DP maps in) | SSP-SP |
| `crime_source` | `dp-direct` or `nearest-distrito-imputed` | — |
| `poi_osm_n`, `poi_osm_per_km2` | OSM tourism/historic/leisure POI count and density — **placeholder** until Google Places | OpenStreetMap |

## `data/processed/distrito_features.csv`

One row per distrito (96), indexed by `distrito`. Same distrito-context columns as
above. Secondary view for EDA, maps, and Phase 2 spatial checks.

## Known gaps

Tracked in `09 - Spatial Aggregation.md`:

- Crime crosswalk (`data/external/dp_distrito_crosswalk.csv`) needs manual review;
  nearest-distrito imputation is a placeholder.
- No population → crime is a raw count, not a rate per 100k.
- POI is OSM, not Google Places.
- IPTU value is fiscal, not deflated market price.
- Property-profile dimension not built yet (listing attributes are still raw).
