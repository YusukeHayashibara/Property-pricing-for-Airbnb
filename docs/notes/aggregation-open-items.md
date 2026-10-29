# Branch focus: aggregation open items

**Branch:** `feature/aggregation-open-items`
**Scope:** close the open points left after the wide aggregation build
(`notebooks/aggregation.ipynb`). Nothing else belongs on this branch.

Source of the list: `obsidian-vault/09 - Spatial Aggregation.md` (checklist at the end).

## Items

- [ ] Review the `dp,distrito` crosswalk (9 `manual-guess` rows) and replace the
      nearest-distrito imputation for the 25 distritos without a DP
- [ ] Replace OSM POIs with Google Places (needs `GOOGLE_PLACES_API_KEY`);
      check the 6 distritos currently filled with 0 POIs
- [ ] Add population by distrito (SEADE / IBGE 2022) and compute crime per 100k
- [ ] Decide the crime basket and the time window ([[ISP]])
- [ ] Choose the FipeZAP deflation base (IPTU 2025 vs Airbnb 2026-06) and apply it
- [ ] Regenerate `listings_aggregated.csv` / `distrito_features.csv` and update
      `docs/data-dictionary-aggregation.md`

## Out of scope

Property-profile clustering, composite investment score, modeling, `src/` redesign.
