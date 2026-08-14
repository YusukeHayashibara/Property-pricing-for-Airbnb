# Project Overview

Developed for **SSC0957 — Practical Data Science II**.

## Question

> Which regions and property profiles in São Paulo maximize the expected return of an Airbnb, once the return is adjusted for the surrounding crime risk and tourist attractiveness?

> #decision (2026-08-14): project scope shifted from Rio de Janeiro to **São Paulo** — the Inside Airbnb export the team is working with is a São Paulo snapshot (see [[Inside Airbnb]] EDA). [[ITBI]] and [[ISP]] are Rio-specific and need São Paulo replacements before the cost/risk pipeline steps can run; see the open questions logged in those notes. Decision log: [[05 - Methodology]].

## Framing

Spatial multi-criteria optimization, following the causal chain:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

Rather than only listing cheap properties, the goal is a composite **investment score** per region + property profile.

## Why "region + property profile" and not individual listings

ITBI and FipeZAP give price and location but not property attributes (bedrooms, area, etc.). So the analysis works at the microregion level: Inside Airbnb supplies attribute/revenue data, ITBI/FipeZAP supply cost per m² per microregion.

See [[05 - Methodology]] for the full pipeline and [[08 - References & Literature]] for background reading.

## Possible pivot — under discussion, not decided

#open-question (2026-08-14): the team is unsure whether "best property to buy" is answerable with current data, since neither [[ITBI]]-style transaction data nor [[FipeZAP]] carry property attributes (bedrooms, area, condition) — the project already works around this by scoring at the region + property-profile level rather than per-property (see above), but that's a workaround, not a fix.

Idea being floated as an alternative framing: instead of "which property should I buy to run as an Airbnb," ask **"which existing Airbnb listing/operation is performing best"** — using Inside Airbnb's own attributes and performance data directly, plus **Google Street View imagery** of the property/block as an additional visual signal (curb appeal, building condition, street character) feeding the tourist-appeal or investment-score side. This would reduce reliance on ITBI/FipeZAP entirely.

Still just an idea — no decision made. If pursued, it changes the causal chain above and likely drops or reduces the role of [[ITBI]] and [[FipeZAP]]. Revisit and log the outcome in [[05 - Methodology]]'s decision log once discussed with the team.

## Links

- Code repo root README: `../README.md`
- Data sources detail: [[ITBI]], [[FipeZAP]], [[Inside Airbnb]], [[Google Places - TripAdvisor]], [[ISP]]
- Timeline: [[04 - Timeline & Milestones]]
