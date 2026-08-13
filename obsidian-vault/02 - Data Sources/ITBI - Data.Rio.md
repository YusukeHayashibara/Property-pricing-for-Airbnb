# ITBI — Data.Rio

**Role:** Cost (base)

## What it provides

Real estate transaction prices (ITBI — Imposto sobre Transmissão de Bens Imóveis), geolocated, published via the Data.Rio open data portal.

## Known limitations

- Gives price + location, but **not** property attributes (bedrooms, area, condition, etc.).
- Coverage/format can change — confirm current availability before collection starts (see `../../README.md` → Notes).

## How we use it

Aggregated to microregion level to estimate **cost per m²**, combined with FipeZAP for validation. See [[05 - Methodology]].

## Open questions

- #open-question What's the most recent ITBI dataset vintage available on Data.Rio?
- #open-question What geographic granularity does the portal expose (bairro? AISP? custom grid)?

## Links

- [[FipeZAP]] — used to validate/trend-check ITBI prices
- Portal base URL: configured in `../../.env.example` as `DATA_RIO_BASE_URL`
