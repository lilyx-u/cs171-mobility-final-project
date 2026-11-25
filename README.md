# Where you grow up shapes what you earn

CS 1710 final project by **Atul Julka, Liam Clower and Lily Xu**.

An interactive data story, built with SvelteKit and D3, that asks:

> **Does where you grow up matter beyond who your parents are, and for whom does
> it matter most?**

Main finding: place matters far more for children of low-income parents than
for children of high-income parents. The middle 80% of US counties span 14
percentile points of adult income for the former and 11 for the latter.

| | |
|---|---|
| **Project website** | https://lilyx-u.github.io/cs171-mobility-final-project/ |
| **Code repository** | https://github.com/lilyx-u/cs171-mobility-final-project |
| **Screencast (2 min)** | _TODO: paste the video link, or the file name of the video submitted alongside this folder_ |
| **Process book** | [`process-book/CS1710_Process_Book_Final.pdf`](process-book/CS1710_Process_Book_Final.pdf) |
| **Data, with field descriptions** | [`static/`](static/) and [`DATA.md`](DATA.md) |

## What is in this folder

```
README.md                    this file
DATA.md                      every data file and every field in it
package.json, vite.config.js project and build configuration
src/                         all of the website's code (ours; see "Our code and the libraries")
static/                      the data the site loads at runtime (counties.json, derived.json, places.json)
scripts/                     the Python data pipeline that produced static/, and the packaging script
process-book/                the final process book PDF, plus its sources, images and builder
.github/workflows/deploy.yml publishes the site to GitHub Pages
```

## Run it

Needs [Node.js](https://nodejs.org) (LTS: v20.19+, v22.12+ or newer).

```bash
npm install
npm run dev
```

Then open the URL Vite prints (usually http://localhost:5173). Nothing else is
needed: no API keys, no accounts, no database. The data is committed in
`static/`; the only network request at runtime is for the two Google Fonts.

To build the static site that gets published:

```bash
npm run build      # writes plain HTML, JS and data files to build/
npm run preview    # serves build/ locally to check it
```

## Publish it (GitHub Pages)

The site builds to static files, so any static host works. For GitHub Pages:

1. Create a public GitHub repository and push this folder to its `main` branch.
2. In the repository: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. The included workflow (`.github/workflows/deploy.yml`) builds and publishes on
   every push. The site appears at `https://<user>.github.io/<repository>/`.

This project is published from https://github.com/lilyx-u/cs171-mobility-final-project at https://lilyx-u.github.io/cs171-mobility-final-project/.

## The site, section by section

The page is one scrolling argument. The bar at the top names each part, underlines
the part being read, and has a **Visualizations** menu that jumps to any single chart.

| Part | What it shows | Charts |
|---|---|---|
| Start | The claim, three definitions (income rank, point, median county), and "Where did you grow up?" | Percentile picture (100 figures); the chosen county's mobility curve |
| 1 · The opportunity map | Outcomes are not scattered at random | County/state choropleth with a parent-income slider, click a state to fly into it; one bar per state; best and worst lists |
| 2 · What predicts mobility | Which characteristics of a county go with mobility | Brushable scatterplot linked to a map; the chosen county against every other county |
| 3 · Who place matters for | **The main message:** place matters most for children who have the least | The mobility fan (our novel view): every county as a line across three parent-income levels |
| 4 · Rich vs. poor maps | The same fact, on the map | Two choropleths on one shared colour scale |
| 5 · Three closer looks | Rural vs. urban; the gap by age; twin counties | Density strips linked to a map; animated age paths; twin-county finder |
| About the data | Sources, definitions and caveats | |

### Features that are easy to miss

- **Your county follows you.** Pick a county, city or town at the top (or use your
  location) and it is marked in purple in every chart below. It is remembered on
  your device between visits; "Clear" forgets it.
- **Clicking a county on the first map makes it your county** (with an Undo).
- **The parent-income slider** on the first map recolours the map and rewrites the
  spread sentence, the state chart and the best/worst lists.
- **States view.** Switch the first map to "States", click a state to fly into its
  counties; the state chart below is linked to the map in both directions.
- **Brush the scatterplot** (drag a box) to outline those counties on the map beside it.
- **The fan can be filtered by region and redrawn** as distance from the median
  county. **Click any line to pin that county** and compare others against it.
- **Press play on the age chart** to watch the gap between the two groups open.
- **Deep links.** Every part and chart has its own address (for example `…/#viz-fan`).

## Our code and the libraries

Everything in `src/`, `scripts/` and `process-book/*.py` was written by the team
for this project. No chart comes from a charting library: each one is an SVG
drawn in a Svelte component, using D3 for scales, shapes, projections and brushing.

```
src/routes/+page.svelte      the story page: prose, page-level state, layout
src/routes/+layout.svelte    fonts, colours, global styles
src/routes/+layout.js        tells SvelteKit to prerender the page to static HTML
src/lib/SiteNav.svelte       sticky navigation: section links, scroll spy, Visualizations menu, smooth scroll
src/lib/PercentileRow.svelte 100 figures: what a percentile is
src/lib/CountySearch.svelte  typeahead over 3,131 counties and 29,700 cities and towns; "use my location"
src/lib/CountyDetail.svelte  one county's mobility curve and numbers
src/lib/CountyMap.svelte     choropleth (county or state level, zoom into a state, tooltip, legend)
src/lib/Legend.svelte        gradient legend for any D3 scale
src/lib/StateLadder.svelte   one bar per state, low-income to high-income children; linked to the map
src/lib/Scatter.svelte       scatterplot with fit line, r, and a brush
src/lib/CountyVsNation.svelte  the chosen county on six characteristics
src/lib/MobilityFan.svelte   the novel view: every county as a line across p25/p50/p75; pin and compare
src/lib/TwinMaps.svelte      two choropleths on one shared scale
src/lib/DensityStrips.svelte counties by population-density band
src/lib/AgePaths.svelte      income rank at 24, 26, 29 and the mid-thirties
src/lib/TwinFinder.svelte    same outcome for poor children, different for rich
src/lib/data.js              loading and light cleaning; variable lists; state roll-up
src/lib/colors.js            the palette and scale constructors
src/lib/story.svelte.js      shared state (the reader's county)
```

Libraries and outside resources (not our code):

| Library | Version | Used for |
|---|---|---|
| [SvelteKit](https://svelte.dev/docs/kit) / [Svelte](https://svelte.dev) | 3 / 5 | components, reactivity, the build |
| [Vite](https://vite.dev) | 8 | dev server and bundler |
| [@sveltejs/adapter-static](https://svelte.dev/docs/kit/adapter-static) | 4 | builds the site to static files |
| [D3](https://d3js.org) | 7.9 | scales, line/area generators, Albers USA projection, brush, colour interpolation |
| [topojson-client](https://github.com/topojson/topojson-client) | 3.1 | turns TopoJSON into drawable shapes |
| [us-atlas](https://github.com/topojson/us-atlas) | 3.0 | county and state boundaries |
| Google Fonts | | Source Serif 4, IBM Plex Sans |
| Python standard library | 3.x | the data pipeline in `scripts/` (no third-party packages) |
| pypdf, reportlab, svglib | | only for building the process book PDF |

## Data

See [`DATA.md`](DATA.md) for every file and field. In short, `static/counties.json`
(3,131 counties) joins:

- **Opportunity Atlas** (US Census Bureau; Chetty, Friedman, Hendren, Jones and
  Porter): county outcomes by parental income percentile, and county characteristics.
- **SEDA 6.0** (Stanford Education Data Archive): county mean test scores, grades 3-8.

`static/derived.json` holds the summary numbers the prose quotes, and
`static/places.json` maps cities and towns to counties for the search box.

### Rebuilding the data

The site does not need this; the built files are committed. The raw sources are
about 210 MB and are **not** in this folder:

```bash
python scripts/build_counties.py [source_dir]   # raw Atlas + SEDA -> static/counties.json (defaults to ~/Downloads)
python scripts/add_age_paths.py [source_dir]    # optional: refresh only the age columns from the public Atlas file
python scripts/derive_stats.py                  # static/counties.json -> static/derived.json
python scripts/build_places.py us_cities.csv static/counties.json static/places.json
```

Each script's docstring lists the files to download and where from.
`build_counties.py` prints a regression check against two published figures
(Charlotte and Salt Lake) so a broken join fails loudly rather than silently.

## Caveats that affect what the charts can claim

- **Everything is aggregated to counties.** There are no individual records in
  either source, so any relationship shown is between *places*, not people.
- **The cohorts don't line up.** Atlas children were born 1978-1983; SEDA
  students were born roughly 1996-2010. The honest claim is "places where
  children score well now are also places where an earlier generation earned
  more", not that these test scores caused these incomes.
- **Counties with fewer than 1,000 children are hatched as "no data"** (215 of them);
  the Atlas estimates are too noisy below that.
- **Privacy noise** can push a share slightly below zero; `loadCounties()`
  clamps those for display.

## Process book and submission

```bash
python process-book/build_process_book.py   # -> process-book/CS1710_Process_Book_Final.pdf
python scripts/package_submission.py        # -> submission/cs1710_final_<date>.zip
```

See `process-book/README.md` for how the process book is assembled.
