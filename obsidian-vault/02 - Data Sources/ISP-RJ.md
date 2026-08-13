# ISP-RJ

**Role:** Risk

## What it provides

Crime statistics by neighborhood / AISP (Área Integrada de Segurança Pública), published by the Instituto de Segurança Pública do Rio de Janeiro.

## How we use it

Crime risk adjustment on the investment score — same causal chain step described in [[01 - Project Overview]]:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

## Known limitations

- AISP boundaries don't necessarily align with neighborhood or ITBI microregion boundaries — spatial join/aggregation needed.
- Reporting lag / underreporting is a known issue with public crime statistics generally — worth a caveat in the final report.

## Open questions

- #open-question Which crime categories are most relevant to Airbnb guest safety perception (violent crime vs. property crime)?
- #open-question Time window: recent 12 months? Multi-year average?

## Links

- Base URL: configured in `../../.env.example` as `ISP_RJ_BASE_URL`
- [[05 - Methodology]]
