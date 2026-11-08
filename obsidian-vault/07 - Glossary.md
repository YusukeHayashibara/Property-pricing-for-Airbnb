# Glossary

**AISP** — Área Integrada de Segurança Pública. Administrative unit used by ISP to report crime statistics (Rio). São Paulo's SSP-SP reports by **DP** instead.

**ITBI** — Imposto sobre Transmissão de Bens Imóveis. Brazilian real-estate transfer tax; its records give geolocated transaction prices. Not used for São Paulo; the cost source is **IPTU-SP** (see [[ITBI]]).

**Distrito** — São Paulo has 96. The common spatial unit of the project; every source is normalized to a `distrito` key ([[09 - Spatial Aggregation]]).

**DP** — Delegacia de Polícia (police district). SSP-SP publishes crime counts by DP; 94 DPs serve 96 distritos and their areas do not nest.

**Crosswalk (DP → distrito)** — reviewed table assigning each DP to a distrito, `data/reference/dp_distrito_crosswalk.csv`.

**IPTU** — Imposto Predial e Territorial Urbano. The municipal property register is the project's cost source; its values are fiscal, not market prices.

**Moran's I / LISA / G\*** — global spatial autocorrelation, its local version (clusters HH, LL, HL, LH), and Getis-Ord hot spots. Used in `notebooks/eda_espacial.ipynb`.

**FDR** — false discovery rate, a correction for the many simultaneous local tests.

**η² (eta squared)** — share of variance explained by a grouping, here the distrito.

**Investment score** — the project's composite output ranking region + property-profile combinations, adjusted for crime risk and tourist appeal.

**PySal** — Python Spatial Analysis Library; used for spatial statistics (Moran/LISA) in this project.

> Add terms as they come up during collection/modeling — link back with `[[07 - Glossary]]` from wherever the term is first used.
