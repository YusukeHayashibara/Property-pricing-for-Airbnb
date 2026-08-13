# Project Overview

Developed for **SSC0957 — Practical Data Science II**.

## Question

> Which regions and property profiles in Rio de Janeiro maximize the expected return of an Airbnb, once the return is adjusted for the surrounding crime risk and tourist attractiveness?

## Framing

Spatial multi-criteria optimization, following the causal chain:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

Rather than only listing cheap properties, the goal is a composite **investment score** per region + property profile.

## Why "region + property profile" and not individual listings

ITBI and FipeZAP give price and location but not property attributes (bedrooms, area, etc.). So the analysis works at the microregion level: Inside Airbnb supplies attribute/revenue data, ITBI/FipeZAP supply cost per m² per microregion.

See [[05 - Methodology]] for the full pipeline and [[08 - References & Literature]] for background reading.

## Links

- Code repo root README: `../README.md`
- Data sources detail: [[ITBI - Data.Rio]], [[FipeZAP]], [[Inside Airbnb]], [[Google Places - TripAdvisor]], [[ISP-RJ]]
- Timeline: [[04 - Timeline & Milestones]]
