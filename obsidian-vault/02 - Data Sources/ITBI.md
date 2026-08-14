# ITBI 

**Role:** Cost (base)

## What it provides

Real estate transaction prices (ITBI — Imposto sobre Transmissão de Bens Imóveis), geolocated, published data portal.

## Known limitations

- Gives price + location, but **not** property attributes (bedrooms, area, condition, etc.).
- Coverage/format can change — confirm current availability before collection starts (see `../../README.md` → Notes).

## How we use it

Aggregated to microregion level to estimate **cost per m²**, combined with FipeZAP for validation. See [[05 - Methodology]].

## Open questions

- #open-question **Scope mismatch:** the project shifted from Rio de Janeiro to **São Paulo** on 2026-08-14 (see [[01 - Project Overview]], decision log in [[05 - Methodology]]). Data.Rio is Rio de Janeiro's municipal open-data portal and does not cover São Paulo — this source needs a São Paulo equivalent for transaction-level ITBI data (e.g. the São Paulo municipal ITBI/GeoSampa data, TBD — not yet researched). Until replaced, this note and `DATA_RIO_BASE_URL` describe a source the project can no longer use as-is.
- #open-question What's the most recent ITBI dataset vintage available on Data.Rio? (moot if replaced by a São Paulo source)
- #open-question What geographic granularity does the portal expose (bairro? AISP? custom grid)?

## Links

- [[FipeZAP]] — used to validate/trend-check ITBI prices
- Portal base URL: configured in `../../.env.example` as `DATA_RIO_BASE_URL`
