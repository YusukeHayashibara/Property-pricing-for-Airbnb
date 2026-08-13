# Google Places / TripAdvisor

**Role:** Tourism

## What it provides

Points of interest, their location, and ratings — used to build a **tourist appeal** signal per region.

## How we use it

Density/quality of nearby points of interest feeds the tourist-appeal term in the investment score. See [[05 - Methodology]].

## Known limitations

- API quota/cost — Google Places API is not free at scale; budget calls carefully.
- TripAdvisor may require scraping if no accessible API tier fits the budget — **check terms of use before automated collection** (see `../../README.md` → Notes).

## Open questions

- #open-question Which POI categories count toward "tourist appeal" (beaches, landmarks, restaurants, nightlife)?
- #open-question API budget / rate limits — who owns the API key? (see `../../.env.example`)

## Links

- [[ISP-RJ]] — combined with tourist appeal and crime risk in the investment score
- [[05 - Methodology]]
