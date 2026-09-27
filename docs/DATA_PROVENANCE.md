# Data provenance and presentation principles

## Every important value carries

source · model · run/issue time · valid time · location · variable · unit · processing method ·
licence (where relevant) · spread/range (where applicable). CORE already returns most of this
(`Provenance` objects, `source`/`model`/`issue_time` on grids). V2 must pass it through to the
screen. It must not drop it.

## Never

- Fabricate data or use mock data where a real source exists.
- Silently replace a failed source. If CORE or a provider fails, show the source as unavailable
  (the V2 client raises `CoreApiError` with the endpoint), or show a labelled fallback such as
  "coarse fallback grid" as CORE does.
- Present historical values that were not retrieved from a named dataset.

## Official vs system-derived

The distinction must be visually and semantically obvious, and never merged into one statement.

| | OFFICIAL WARNING | SYSTEM ASSESSMENT |
|---|---|---|
| Who | IMD, CWC, NDMA/SACHET, SDMAs, other government authorities | Bharat Weather Intelligence analysis |
| Text | Verbatim, with issuer and validity | Our wording, with the rule, period and sources |
| Style | Red "Official warning" label (`--color-official`) | Blue-grey "System assessment" label (`--color-system`) |
| Words | "Warning", "Alert" as issued | "Elevated risk", "Indicator", "Potential". Never "warning" |

Farmer indicators are labelled **SYSTEM-DERIVED INDICATOR (unvalidated)** until reviewed by an
agricultural authority. **OFFICIAL AGRICULTURAL ADVISORY** content appears in its own block,
with links and dates.

## Specific wording rules

| Topic | Say | Never say |
|---|---|---|
| Lightning | "Thunderstorm potential — model derived", plus official lightning alerts where they exist | "Lightning", "lightning strikes", as if observed |
| Satellite (until point values exist) | "Satellite imagery available" | "Satellite confirms" |
| Rain vs normal | "vs IMD 1991–2020 normal" once implemented; until then "vs NASA POWER (MERRA-2) reference, indicative" | "vs normal" with no baseline named |
| Temperature vs normal | "vs NASA POWER 1991–2020" | — |
| Cyclone | Official IMD / RSMC information only | Any system-generated cyclone track or risk |
