# Data dictionary

Every data file the site uses, and every field in it. All three files live in
[`static/`](static/) and are loaded by the browser at runtime (`src/lib/data.js`).
They are built from the raw sources by the scripts in [`scripts/`](scripts/);
the raw sources themselves (about 210 MB) are not included.

| File | Rows | Size | Built by |
|---|---|---|---|
| `static/counties.json` | 3,131 counties | 1.8 MB | `scripts/build_counties.py`, `scripts/add_age_paths.py` |
| `static/derived.json` | one object | 9 KB | `scripts/derive_stats.py` |
| `static/places.json` | 29,708 cities and towns | 0.8 MB | `scripts/build_places.py` |

## Sources

| Source | What we took | Where |
|---|---|---|
| **Opportunity Atlas**, county outcomes (Table 5: All Outcomes by County, Race, Gender and Parental Income Percentile) | Children's adult outcomes by parental income percentile | US Census Bureau, Center for Economic Studies: https://www.census.gov/programs-surveys/ces/data/public-use-data/opportunity-atlas-data-tables.html |
| **Opportunity Atlas**, county covariates | County characteristics (poverty, single-parent share, etc.) | same page |
| **SEDA 6.0**, county pooled test scores (cohort-standardised scale) and county covariates | Mean test scores for grades 3-8 | Stanford Education Data Archive: https://edopportunity.org (email registration and data use agreement) |
| **US Atlas TopoJSON** | County and state boundaries | `us-atlas` npm package, from US Census Bureau cartographic boundary files |
| **US Cities Database** | City and town names with their county | https://github.com/kelvins/US-Cities-Database (MIT licence) |

The Atlas followed children born 1978-1983 and measured their household income
in 2014-15, at ages 31 to 37. The join key is the five-digit county FIPS code.
SEDA covers a strict subset of the Atlas's counties, so the joined file has
3,131 counties; Puerto Rico and a handful of very small counties drop out.

## How to read the outcome fields

- An **income rank** is a position in the national income distribution of people
  born the same year, stored as a fraction from 0 to 1. `0.42` means the 42nd
  percentile.
- A **point** is one percentile: a difference of `0.01` between two ranks.
- Fields ending `25`, `50`, `75` are the Atlas's estimate for children whose
  **parents** were at the 25th (low-income), 50th (middle) or 75th (high-income)
  percentile of the national parent income distribution.
- All outcomes are pooled across race and gender.
- `null` means the source did not report a value.

## `static/counties.json`

A JSON array with one object per county.

### Identity

| Field | Type | Meaning |
|---|---|---|
| `fips` | string | Five-digit county FIPS code (2-digit state + 3-digit county), zero-padded. The join key. |
| `county` | string | County name, e.g. `"Autauga County"` (from SEDA) |
| `state` | string | Two-letter state abbreviation |
| `cz` | string | Name of the commuting zone the county belongs to (Atlas) |

### Outcomes (Opportunity Atlas)

| Field | Atlas column | Meaning |
|---|---|---|
| `kfr25`, `kfr50`, `kfr75` | `kfr_pooled_pooled_p25/p50/p75` | Mean household income rank at ages 31-37 of children raised in the county, by parent percentile. **The site's main measure.** |
| `kfr24_25`, `kfr24_75` | `kfr_24_pooled_pooled_p25/p75` | Mean income rank at age 24 (rank among people the same age), low- and high-income parents |
| `kfr26_25`, `kfr26_75` | `kfr_26_pooled_pooled_p25/p75` | The same at age 26 |
| `kfr29_25`, `kfr29_75` | `kfr_29_pooled_pooled_p25/p75` | The same at age 29 |
| `top20_25`, `top20_75` | `kfr_top20_pooled_pooled_p25/p75` | Share of children who reached the top fifth of the national income distribution |
| `coll25`, `coll75` | `coll_pooled_pooled_p25/p75` | Share of children who attended college (not reported for 80 counties) |
| `jail25` | `jail_pooled_pooled_p25` | Share of children of low-income parents incarcerated on 1 April 2010 |
| `n` | `kid_pooled_pooled_n` | Number of children in the Atlas sample for the county. Counties with `n` below 1,000 are treated as "no data". |
| `n_low` | `kid_pooled_pooled_blw_p50_n` | Number of those children whose parents were below the median income |

The Atlas adds a small amount of random noise to protect privacy, so shares
(`top20_*`, `coll*`, `jail25`) can fall slightly below 0 or above 1 in very small
counties. The site clamps negative shares to 0 for display only; the file keeps
the published values.

### County characteristics (Opportunity Atlas covariates)

| Field | Atlas column | Meaning | Unit |
|---|---|---|---|
| `poverty` | `poor_share2010` | Share of residents below the federal poverty line, 2010 | fraction 0-1 |
| `collshare` | `frac_coll_plus2010` | Share of adults 25+ with a bachelor's degree or more, 2010 | fraction 0-1 |
| `singlepar` | `singleparent_share2010` | Share of children living in single-parent households, 2010 | fraction 0-1 |
| `medinc` | `med_hhinc2016` | Median household income, 2016 | dollars per year |
| `popdens` | `popdensity2010` | Population density, 2010 | people per square mile |
| `jobdens` | `job_density_2013` | Job density, 2013 | jobs per square mile |

### Test scores (SEDA 6.0)

Scores are on SEDA's cohort-standardised scale: standard deviations of the
national student distribution, where 0 is the national average student. They
pool grades 3-8, mathematics and reading, across the available years.

| Field | SEDA column | Meaning |
|---|---|---|
| `score` | `cs_mn_avg_eb`, subgroup `all` | Mean test score, all students |
| `score_ecd` | `cs_mn_avg_eb`, subgroup `ecd` | Mean test score, economically disadvantaged students |
| `score_nec` | `cs_mn_avg_eb`, subgroup `nec` | Mean test score, students who are not economically disadvantaged |
| `learn` | `cs_mn_lrn_eb`, subgroup `all` | Average learning rate: change in score per grade, in the same units |
| `ses` | `sesavgall` | SEDA's composite socioeconomic status index for the county (standardised) |

### Fields added in the browser

`src/lib/data.js` adds these when the file is loaded; they are not in the JSON.

| Field | Meaning |
|---|---|
| `gap` | `kfr75 − kfr25`: the gap, in rank, between children of high- and low-income parents raised in the same county |
| `reliable` | `true` when `n` is at least 1,000 |
| `region` | Census region of the county's state (Northeast, Midwest, South, West) |
| `label` | `"<county>, <state>"`, for display |

## `static/derived.json`

Summary numbers the prose and chart annotations quote, computed once by
`scripts/derive_stats.py` over the 2,916 "reliable" counties (`n` ≥ 1,000).

| Key | Meaning |
|---|---|
| `counties_total` | Number of counties in `counties.json` (3,131) |
| `counties_reliable` | Number with at least `min_n` children (2,916) |
| `min_n` | The reliability threshold (1,000) |
| `national` | For each of `kfr25`, `kfr50`, `kfr75`: `mean`, `median`, `sd`, `p10`, `p90`, `min`, `max` across counties, and `spread` = `p90 − p10` (the "middle 80% of counties" figure). `national.gap` has `mean`, `median`, `p10`, `p90` of the within-county gap. The `median` values are what the site calls **the median county**. |
| `correlations` | A list, one entry per county characteristic: `key`, `label`, and Pearson *r* across counties with `kfr25` (`r25`) and with `kfr75` (`r75`) |
| `density_bins` | Counties grouped by order of magnitude of population density: `bin` (0-4), `label`, `n` counties, mean `kfr25` and `kfr75` |
| `ages` | Mean rank across counties at each age for both parent groups: `kfr24_25` … `kfr29_75`, plus `adult_25` / `adult_75` (ages 31-37) and `n` counties used |
| `regions` | Map from state abbreviation to Census region |
| `twins` | Up to 12 pairs of large counties (`n` ≥ 20,000) whose `kfr25` is within half a point but whose gaps differ by at least 8 points: `flat` and `steep` (each with `fips`, `name`, `kfr25`, `kfr75`) and `gap_diff` |
| `examples` | A few named counties (`fips`, `name`, `kfr25`, `kfr75`, `gap`, `n`) |
| `extremes` | The five best and five worst large counties for children of low-income parents (`best_p25`, `worst_p25`) |

## `static/places.json`

A JSON array of `[name, state, fips]` triples, for example
`["Aaronsburg", "PA", "42027"]`. It lets the search box accept a city or town and
resolve it to the county that contains it. A town that straddles two counties
appears once for each.

| Position | Meaning |
|---|---|
| 0 | City or town name |
| 1 | Two-letter state abbreviation |
| 2 | Five-digit FIPS code of the county it is in (matches `fips` in `counties.json`) |

## County and state boundaries

Boundaries are not a file in `static/`: they are imported from the `us-atlas`
package (`us-atlas/counties-10m.json`, TopoJSON at 1:10,000,000) and projected
in the browser with D3's Albers USA projection.
