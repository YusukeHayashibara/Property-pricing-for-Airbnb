# Branch focus: aggregation open items

**Branch:** `feature/aggregation-open-items`
**Scope:** close the open points left after the wide aggregation build
(`notebooks/aggregation.ipynb`). Nothing else belongs on this branch.

Source of the list: `obsidian-vault/09 - Spatial Aggregation.md` (checklist at the end).

## Items

- [ ] Review the `dp,distrito` crosswalk and replace the nearest-distrito
      imputation for the distritos without a DP
  - [x] All 94 DP rows reviewed (2026-11-03): 22 corrected (23%), 58 confirmed,
        12 kept on a bairro argument, 1 `kept-ambiguous` (Vila Clementino).
        Method + evidence + slide outline: `docs/crime-crosswalk-review.md`
        Distritos with a direct DP: 71 → 76 (20 still imputed). Notebook rerun and
        CSVs regenerated on 2026-11-03 (they are git-ignored: rerun locally).
  - [x] Before/after crime map for the slides: `outputs/crime_crosswalk_antes_depois.png`
  - [ ] Imputation rule for the 20 DP-less distritos (still nearest-neighbour)
  - [ ] Map check of the 13 weaker rows (`reviewed-bairro`, `kept-ambiguous`)
  - [x] Population by distrito: `data/external/populacao_distrito_2022.csv`
        (IBGE Censo 2022, SIDRA 9923, 96 distritos, 11,451,999 inhabitants;
        `scripts/fetch_population_distrito.py`). Crime per 100k not applied yet.
- [ ] Replace OSM POIs with Google Places (needs `GOOGLE_PLACES_API_KEY`);
      check the 6 distritos currently filled with 0 POIs
- [ ] Add population by distrito (SEADE / IBGE 2022) and compute crime per 100k
- [ ] Decide the crime basket and the time window ([[ISP]])
- [ ] Choose the FipeZAP deflation base (IPTU 2025 vs Airbnb 2026-06) and apply it
- [x] Regenerate `listings_aggregated.csv` / `distrito_features.csv` (2026-11-03,
      crosswalk update only; POI, population-based rates, FipeZAP still pending)
- [ ] Regenerate again after the remaining items above, and update
      `docs/data-dictionary-aggregation.md`

## Out of scope

Property-profile clustering, composite investment score, modeling, `src/` redesign.
