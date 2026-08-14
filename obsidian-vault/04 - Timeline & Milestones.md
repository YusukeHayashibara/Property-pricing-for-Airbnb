# Timeline & Milestones

4-month plan, mirrored in `../docs/TIMELINE.md`. Update both when dates shift — this note is for team-facing discussion/context, `docs/TIMELINE.md` is the citable version for the report.

## Phase 1 — Aggregation (Month 1)

- Confirm current availability/format of each source: [[ITBI]], [[FipeZAP]], [[Inside Airbnb]], [[Google Places - TripAdvisor]], [[ISP]].
- Collect, geocode, and integrate sources.
- Clean and diagnose data quality.
- **Milestone:** unified, geolocated dataset at microregion level.

## Phase 2 — Visual interpretation (Month 2)

- Maps and charts (PySal, seaborn) arguing representativeness.
- Exploratory spatial analysis.
- **Milestone:** exploratory report / checkpoint presentation.

## Phase 3 — Modeling (Month 3)

- Hedonic revenue model (scikit-learn).
- Spatial analysis: Moran's I / LISA (PySal).
- Composite investment score.
- **Milestone:** working investment score per region + property profile.

## Phase 4 — Validation & writeup (Month 4)

- Sensitivity analysis / robustness checks on the score.
- Final report + presentation.
- **Milestone:** final deliverable submitted.

## Tracking

- #decision and #open-question tags across this vault mark things that affect the timeline — search for them before each weekly sync.
- Meeting-by-meeting progress: `06 - Meetings/`.
