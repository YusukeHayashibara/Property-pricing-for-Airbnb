# Inside Airbnb

**Role:** Revenue

## What it provides

Listing-level data: daily rate, neighbourhood, estimated occupancy/revenue, and property attributes (bedrooms, room type, reviews, etc.).

## How we use it

Primary source for **Airbnb revenue estimation** and for the property-attribute profiles that ITBI/FipeZAP lack. Attributes here define the "property profile" dimension of the region + profile analysis. See [[01 - Project Overview]].

## EDA summary

See `notebooks/airbnb_analysis.ipynb` for the full exploratory analysis. Headline facts about the current export in `data/data/`:

- **42,354 listings**, single snapshot, `last_scraped` 2026-06-14/15/16 (`source` = "city scrape").
- `calendar.csv` covers the 12 months following the scrape (through 2027-06-15); `reviews.csv` goes back to 2011-04-19.
- `price` is a currency-formatted string (`"$540.43"`) and needs cleaning before use; ~1.2% of listings have no price.
- 13 columns are entirely empty in this export (`host_since`, `license`, `instant_bookable`, `neighbourhood`, `host_verifications`, `calendar_updated`, etc.) — don't rely on them without a fresh scrape or another source.
- `Entire home/apt` is ~86% of listings; price scales with `accommodates`/`bedrooms` and varies a lot by neighborhood, as expected for a hedonic model.

## Known limitations

- Estimated occupancy/revenue (`estimated_occupancy_l365d`, `estimated_revenue_l365d`) are Inside-Airbnb-modeled proxies, not verified booking data — treat as an approximation.
- Snapshot-based (single scrape date, 2026-06-14/15/16) — no trend/multi-snapshot data currently in `data/`.

## Open questions

- ~~Geographic scope mismatch~~ #decision (2026-08-14): confirmed — the project has shifted from Rio de Janeiro to **São Paulo**, matching this export's `neighbourhood_cleansed` values and coordinates. [[ITBI]] and [[ISP]] are Rio-specific sources and now need São Paulo equivalents — see the open question logged in each of those notes. See [[01 - Project Overview]] and the decision log in [[05 - Methodology]].
- #open-question How do we spatially join Inside Airbnb listings to the (still-to-be-found) São Paulo cost/risk microregions?
- ~~Which snapshot date(s) will we use?~~ Resolved for now: single snapshot, 2026-06-14/15/16 (see EDA summary above). Revisit if multi-snapshot trend data is added later.

## Links

- Base URL: configured in `../../.env.example` as `INSIDE_AIRBNB_BASE_URL`
- Raw data: `data/data/{listings,calendar,reviews,neighbourhoods}.csv`
- Analysis: `notebooks/airbnb_analysis.ipynb`
- [[05 - Methodology]]
