# Milestone 10: Prototype V2, responding to user testing

This folder is a complete copy of the site with the user-testing feedback applied.
Run it with `npm install` then `npm run dev` (the dependencies are already installed
if you are reading this on the machine it was built on).

## How the feedback was triaged

Two testers produced 24 requests. We ranked them by (1) things that are wrong on
screen, (2) things both testers misread, (3) things that weaken the main argument,
and (4) cheap fixes with a clear payoff. The 13 below made the cut; the 11 that did
not are listed at the end with the reason.

## The 13 changes, in order of importance

| # | Feedback | What changed | Where |
|---|---|---|---|
| 1 | Fan stats stay national when a region is chosen | Every number on the fan (brackets, median ticks, spread labels, the sentence above it and the three stat tiles) is now computed from the counties the filter keeps. "South" reads 1,367 counties, 10 vs 9 points. | `MobilityFan.svelte`, `+page.svelte` |
| 2 | "Fifteen percentiles" in the intro vs "14 points" on the fan | The intro quotes the same derived number as the fan (14, and 11 for high-income children). One source, no drift. | `+page.svelte` |
| 3 | Grey counties read as "worst" | Counties with fewer than 1,000 children are drawn as a diagonal hatch, not a flat grey, and every legend has a "No data" swatch. Tooltips say "no data" explicitly. | `CountyMap.svelte`, `Legend.svelte`, `colors.js` |
| 4 | Define "income rank" and "percentile" before the first chart | One sentence under the lede, before the county search. | `+page.svelte` |
| 5 | Map toggle names the parents but colours the children | The toggle is labelled "Parents' income", with the line "The buttons pick the parents. The colour shows where their children ended up." The legend title says "Children of low-income parents: average adult income rank". | `+page.svelte`, `data.js` |
| 6 | Predictor map ignores the chosen characteristic | The right-hand map is coloured by the selected characteristic on a single-hue teal ramp (light to dark = less to more), with a legend in the characteristic's own units. Brushed counties are outlined on top of it. | `+page.svelte`, `CountyMap.svelte`, `colors.js` |
| 7 | Fan brackets are two grey bars to eyeball | The outer brackets are darker with end caps, each carries its spread in large type, and a connector under the chart states the comparison ("14 vs 11 points: place moves a poor child's outcome 3 points more than a rich child's"). The hover/click hint moved from the caption to the control row above the chart. | `MobilityFan.svelte` |
| 8 | County card curve is red; "48th" has no context | The curve is purple, the typical county is drawn behind it as a dashed line, and every number carries its national comparison ("6 points above the typical county (42nd)"). A new line gives the rank among the 646 large counties. | `CountyDetail.svelte` |
| 9 | Map clicks silently change the pinned county | A clearly visible notice appears above the map ("Your county is now Stearns County, MN, because you clicked it on the map") with an Undo button; it stays for 25 seconds. The readout also says "click to make it your county". | `+page.svelte` |
| 10 | Correlation tiles read like causes; negative r unexplained; score units unclear | A caveat box sits directly under the tiles: correlations across places, not causes; what a negative r means; test scores are standard deviations from the national average student. The r readout now says "strong and negative: counties with more of it had lower outcomes". The scatter's x-axis label and the county card name the units. | `+page.svelte`, `Scatter.svelte`, `data.js` |
| 11 | Percentiles everywhere, no percent signs | Every outcome axis, legend tick, tooltip and card value is written as a rank ("42nd"), never "42%". Shares that really are percentages (poverty rate, single-parent share) keep their sign so the two are never confused. | `colors.js` (`pctile`), all components |
| 12 | Cities and towns in the search | A third pipeline stage, `scripts/build_places.py`, joins a public list of 29,700 US cities and towns to their county and writes `static/places.json`. Typing "Somerville" offers "Somerville, MA is in Middlesex County, MA". Counties still match first; places are ranked by county size. | `CountySearch.svelte`, `data.js`, `scripts/build_places.py` |
| 13 | The three map tabs are not comparable | A "Same colour scale on all three" checkbox puts the tabs on the fixed scale the twin maps use (blue = above the national median adult). The readout explains which mode is on. | `+page.svelte` |

Small extras done while in the same files: the drafts section is marked "not yet
built" with a badge and a hatched background; a data note explains why Alaska looks
like one giant red block (it is real: Bethel, Nome, the North Slope and the Northwest
Arctic are among the lowest-mobility places in the country, each drawn as a shape the
size of a state).

## Not done, and why

- **"Your county vs the nation" card in the predictors section.** Good idea, but the
  county card at the top now carries the national comparison, and the pinned county is
  already drawn on the scatter and the predictor map.
- **Alaska inset.** The AlbersUSA projection already insets Alaska; the "bug" was the
  reading, which the data note now addresses.
- **Reduce overlap between the maps.** The twin maps and the main map now differ in
  purpose (within-group geography vs a shared scale), and the predictor map shows a
  characteristic rather than outcomes, so the three no longer repeat each other.
- **State-level view.** A real feature, not a fix; it would need its own aggregation
  and design pass.
- **Continuous parental-income slider.** The Atlas publishes outcomes at three parent
  percentiles. A slider would interpolate between them and show movement that is not
  in the data.
- Hide the drafts section entirely: we marked it instead, since the drafts are part
  of the milestone submission.

## Files added or changed

```
MILESTONE10.md                 this file
scripts/build_places.py        new: cities and towns -> counties (pipeline stage 3)
static/places.json             new: 29,708 places, 0.77 MB
src/lib/colors.js              pctile(), seqScale(), NO_DATA_LABEL, hatched grey
src/lib/data.js                loadPlaces(), LARGE_N, SCORE_UNIT, units on X_VARS
src/lib/Legend.svelte          rank formatting, "No data" swatch
src/lib/CountyMap.svelte       hatch pattern, 'seq' scheme, fmt/legendFmt props
src/lib/CountyDetail.svelte    purple curve, typical-county line, national comparison, large-county rank
src/lib/CountySearch.svelte    place matches resolved to counties
src/lib/MobilityFan.svelte     region-aware statistics, labelled brackets, comparison connector, hint above chart
src/lib/Scatter.svelte         percentile y-axis, signed r wording
src/lib/TwinMaps.svelte        percentile legend labels
src/routes/+page.svelte        definition sentence, toggle wording, same-scale toggle, pin notice, caveat box, drafts badge
```

The two Milestone 6 lab prototypes at `/a` and `/b` are untouched.
