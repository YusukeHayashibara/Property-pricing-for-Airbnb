# ISP

**Role:** Risk

## What it provides

Crime statistics by neighborhood / AISP (Área Integrada de Segurança Pública), published by the Instituto de Segurança Pública do São Paulo.

## How we use it

Crime risk adjustment on the investment score — same causal chain step described in [[01 - Project Overview]]:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

## Known limitations

- AISP boundaries don't necessarily align with neighborhood or ITBI microregion boundaries — spatial join/aggregation needed.
- Reporting lag / underreporting is a known issue with public crime statistics generally — worth a caveat in the final report.

## Open questions

- #open-question **Scope mismatch:** the project shifted from Rio de Janeiro to **São Paulo** on 2026-08-14 (see [[01 - Project Overview]], decision log in [[05 - Methodology]]). ISP-RJ is Rio de Janeiro's public security institute and doesn't cover São Paulo — this source needs a São Paulo equivalent for crime statistics (e.g. SSP-SP, TBD — not yet researched). Until replaced, this note and `ISP_RJ_BASE_URL` describe a source the project can no longer use as-is.
- #open-question Which crime categories are most relevant to Airbnb guest safety perception (violent crime vs. property crime)?
- #open-question Time window: recent 12 months? Multi-year average?

## Links

- Base URL: configured in `../../.env.example` as `ISP_RJ_BASE_URL`
- [[05 - Methodology]]
