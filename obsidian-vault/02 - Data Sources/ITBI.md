# ITBI 

**Role:** Cost (base)

> #decision (2026-09-07): the São Paulo cost source is **IPTU-SP** (municipal property tax register, `data/raw/IPTU-SP/`, ~3.8M rows), not ITBI transactions. This note keeps the name "ITBI" for continuity. Data.Rio / the Rio ITBI are no longer used. EDA: `notebooks/iptu_analysis.ipynb`.

## What it provides

Real estate transaction prices (ITBI — Imposto sobre Transmissão de Bens Imóveis), geolocated, published data portal.

## Known limitations

- Gives price + location, but **not** property attributes (bedrooms, area, condition, etc.).
- Coverage/format can change — confirm current availability before collection starts (see `../../README.md` → Notes).

## How we use it

Aggregated to microregion level to estimate **cost per m²**, combined with FipeZAP for validation. See [[05 - Methodology]].

## Open questions

- ~~Scope mismatch (Rio vs São Paulo)~~ #decision (2026-09-07): resolved, IPTU-SP is the source. `DATA_RIO_BASE_URL` in `.env.example` is obsolete.
- Aggregation settled: `numero_contribuinte`[:6] (fiscal sector + block) → GeoSampa `quadra_fiscal` polygon → distrito, covering 99.94% of the rows with no geocoding (the `cep` and `bairro` routes were rejected). See [[09 - Spatial Aggregation]].
- #open-question **The values are fiscal (`valor_construcao` median ≈ R$ 60/m²), not market prices.** The level needs calibration with [[FipeZAP]] before it can be a cost input. Deflation base (IPTU 2025 vs Airbnb 2026-06) still undecided.
- IPTU describes the whole property registry (3.8M properties), not transactions or listings for sale. It supports a cost-per-m² signal per distrito, not property-level prices.

## Links

- [[FipeZAP]] — used to validate/trend-check ITBI prices
- Data: `data/raw/IPTU-SP/iptu_2025.zip` (cleaned copy under `data/processed/`)
