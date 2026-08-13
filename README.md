# Property Pricing for Airbnb — Rio de Janeiro

Which properties for sale in the city of Rio de Janeiro are the best options to build an Airbnb? This project combines multiple data sources to score real estate by **return on investment adjusted for crime risk and tourist appeal**.

Developed for **SSC0957 — Practical Data Science II**.

## The question

> Which regions and property profiles in Rio de Janeiro maximize the expected return of an Airbnb, once the return is adjusted for the surrounding crime risk and tourist attractiveness?

Rather than only listing cheap properties, the project treats the decision as a **spatial multi-criteria optimization**, following the causal chain:

```
cost → Airbnb revenue → tourist appeal → crime risk → investment score
```

## Data sources

| Source | Role | What it provides |
|--------|------|------------------|
| ITBI / Data.Rio | Cost (base) | Real transaction prices per m², geolocated |
| FipeZAP | Price validation | Historical price index and trend |
| Inside Airbnb (Rio) | Revenue | Daily rate, estimated occupancy, listing attributes |
| Google Places / TripAdvisor | Tourism | Points of interest, location, ratings |
| ISP-RJ | Risk | Crime statistics by neighborhood / AISP |

> **Note on real estate data:** ITBI and FipeZAP give price and location but not property attributes (bedrooms, area, etc.). The project therefore works at the **region + property-profile** level, using Inside Airbnb for attributes and ITBI/FipeZAP for the cost per m² of each microregion.

## Method

1. **Aggregation** — collect, geocode, and integrate the sources; clean and diagnose data quality.
2. **Visual interpretation** — maps and charts (PySal, seaborn) to argue representativeness for the purpose.
3. **Modeling** — hedonic revenue model (scikit-learn), spatial analysis (PySal: Moran/LISA), and a composite investment score.

## Tools

- Python — pandas, geopandas
- PySal — spatial analysis
- scikit-learn — modeling
- seaborn — visualization

## Repository structure

```
.
├── data/            # raw and processed data (not versioned)
├── notebooks/       # exploration and analysis
├── src/             # collection, cleaning, and modeling code
├── outputs/         # maps, figures, and final score
└── README.md
```

## Status

Work in progress. See the project timeline document for the 4-month plan and milestones.

## Notes

- Confirm the current availability and format of each source (ITBI, ISP-RJ, Inside Airbnb) before starting, as coverage and formats change.
- Check the terms of use of any listing portal before automated collection.
