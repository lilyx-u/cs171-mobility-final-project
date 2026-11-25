# Milestone 11: Prototype V3

This folder is the full site with the rest of the Milestone 10 test-session feedback
applied. `MILESTONE10.md` lists the 13 changes made for V2; this file lists what V3 adds.
The process-book write-up is `process-book/PROTOTYPE_V3.md`.

Run it with `npm install` then `npm run dev`.

## What changed since V2

| Feedback | Change | Where |
|---|---|---|
| State-level view | Counties / States switch on the main map; click a state to fly into its counties; linked state chart (one bar per state, three sort orders) | `CountyMap.svelte`, `StateLadder.svelte`, `data.js` (`rollupStates`) |
| Continuous parent-income slider | Slider from the 25th to the 75th percentile; map, legend, readout, spread sentence and best/worst lists follow it | `+page.svelte`, `data.js` (`kfrAt`) |
| Picture of a percentile | Row of 100 figures under the definition, before the first chart | `PercentileRow.svelte` |
| "Your county vs the nation" card | Six characteristic strips for the pinned county under the scatterplot | `CountyVsNation.svelte` |
| "Use my location" | Button beside the search; county found in the browser, nothing sent | `CountySearch.svelte`, `data.js` (`countyAt`) |
| Paragraph and table follow the tab | Lists and spread sentence are computed for the current slider, level and zoom | `+page.svelte` |
| Fan reads as "rich parents, rich kids" | Second reading: distance from the typical county | `MobilityFan.svelte` |
| Drafts section not for the viewer; views feel redundant | Drafts removed; all three built as "Three closer looks" | `DensityStrips.svelte`, `AgePaths.svelte`, `TwinFinder.svelte` |
| Alaska looks like an error | Note directly under the main map | `+page.svelte` |
| (found in testing) saved county never restored | Fixed the load order | `+page.svelte` |

## Data

- New pipeline stage `scripts/add_age_paths.py` adds income rank at ages 24, 26 and 29
  (low-income and high-income parents) to `static/counties.json` from the public Atlas
  file, and checks the join against the columns already there before writing.
- `scripts/derive_stats.py` now writes the age averages for both groups.
- The slider reads values between the published 25th, 50th and 75th percentiles along
  each county's own line. The published 50th is within 0.35 points of the midpoint of
  the other two in every reliable county. It does not go outside 25 to 75.

## Removed

`src/lib/DraftCard.svelte` and `static/drafts/` (the sketches are still in
`process-book/drafts/` as a record of the designs).

## Still open

Keyboard access to map shapes, phone-width polish for the fan and state chart, and a
think-aloud pass on the new views.
