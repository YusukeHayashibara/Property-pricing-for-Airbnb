# Inside Airbnb (Rio)

**Role:** Revenue

## What it provides

Listing-level data: daily rate, estimated occupancy, and property attributes (bedrooms, room type, reviews, etc.) for Rio de Janeiro.

## How we use it

Primary source for **Airbnb revenue estimation** and for the property-attribute profiles that ITBI/FipeZAP lack. Attributes here define the "property profile" dimension of the region + profile analysis. See [[01 - Project Overview]].

## Known limitations

- Estimated occupancy is a proxy, not verified booking data — treat as an approximation.
- Snapshot-based (specific scrape date) — check which snapshot(s) are used and note the date.

## Open questions

- #open-question Which snapshot date(s) will we use? Single snapshot or multiple for trend?
- #open-question How do we spatially join Inside Airbnb listings to ITBI/FipeZAP microregions?

## Links

- Base URL: configured in `../../.env.example` as `INSIDE_AIRBNB_BASE_URL`
- [[05 - Methodology]]
