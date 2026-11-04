# ISP

**Role:** Risk

## What it provides

> #decision (2026-09-07): the São Paulo source is **SSP-SP** (Secretaria da Segurança Pública do Estado de São Paulo). This note keeps the name "ISP" for continuity; the Rio source (ISP-RJ) is no longer used.

Monthly occurrence counts by **Delegacia de Polícia (DP)** and crime type (`NATUREZA2`), for 2024 and 2025 (12 monthly files in `data/raw/ISP/`, consolidated in `data/processed/ISP/dados_criminais_sao_paulo_2025.csv`; 94 DPs in the municipality). EDA: `notebooks/crime_analysis.ipynb`.

## How we use it

Crime risk adjustment on the investment score — same causal chain step described in [[01 - Project Overview]]:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

## Known limitations

- AISP / DP boundaries don't necessarily align with neighborhood or microregion boundaries — spatial join/aggregation needed. Approach settled: manual **DP → distrito** crosswalk, crime rate per 100k. See [[09 - Spatial Aggregation]] (incl. the granularity-ceiling treatment A vs B).
- Reporting lag / underreporting is a known issue with public crime statistics generally — worth a caveat in the final report.

## Open questions

- ~~Scope mismatch (Rio vs São Paulo)~~ #decision (2026-09-07): resolved, SSP-SP is the source (see above). `ISP_RJ_BASE_URL` in `.env.example` is obsolete.
- #open-question Which crime categories are most relevant to guest safety perception: **property vs person**? Measured (2026-11-03): total, `patrimonial` and a street-exposure basket give the same distrito ranking (ρ ≥ 0.995); only crimes against the **person** change it (ρ = 0.69). So the real choice is property vs person; if unsure, keep both as separate features. See `docs/crime-sensitivity.md`.
- #open-question Time window: measured as irrelevant (2024, 2025, 2024–25 average, each semester: ρ ≥ 0.99), so closing it is cheap. Proposal: full-year 2025.
- #open-question Denominator: per 100k residents vs per km². Central distritos have few residents and a large floating population, so both inflate them. Real exposure is not measured. See `docs/crime-sensitivity.md`.

## Links

- Method and sensitivity: `../docs/crime-crosswalk-review.md` (DP → distrito crosswalk, 22 of 94 draft rows corrected) and `../docs/crime-sensitivity.md`
- Population for rates: IBGE Censo 2022, `data/external/populacao_distrito_2022.csv`
- [[05 - Methodology]]
