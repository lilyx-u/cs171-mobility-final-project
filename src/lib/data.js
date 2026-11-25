import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import usTopo from 'us-atlas/counties-10m.json';
// `asset()` prefixes a file in static/ with the path the site is served from,
// so the data loads both at the domain root and under /<repo>/ on GitHub Pages.
import { asset } from '$app/paths';

// Minimum sample size. Below this the Opportunity Atlas estimates are too noisy
// to read, so we grey the county out rather than colouring it.
export const MIN_N = 1000;
// "Large" county, as used by the best/worst lists and the county card's rank.
export const LARGE_N = 20000;

// SEDA scores are on the cohort-standardised (cs) scale: standard deviations of
// the national student distribution, 0 = the national average student.
export const SCORE_UNIT = 'standard deviations from the national average student';

export const X_VARS = [
	{ key: 'singlepar', label: 'Single-parent share', fmt: d3.format('.0%'), unit: 'share of children in single-parent households' },
	{ key: 'poverty', label: 'Poverty rate', fmt: d3.format('.0%'), unit: 'share of residents below the poverty line' },
	{ key: 'score', label: 'Test score (SEDA, grades 3-8)', fmt: d3.format('+.2f'), unit: SCORE_UNIT },
	{ key: 'score_ecd', label: 'Test score, low-income students', fmt: d3.format('+.2f'), unit: SCORE_UNIT },
	{ key: 'collshare', label: 'Share of adults with a BA', fmt: d3.format('.0%'), unit: 'share of adults with a bachelor’s degree' },
	{ key: 'medinc', label: 'Median household income', fmt: d3.format('$,.0f'), unit: 'dollars per year' }
];

export const PERCENTILES = [
	{ key: 'kfr25', label: 'Low-income (25th pct)', short: 'p25', plain: 'low-income' },
	{ key: 'kfr50', label: 'Middle-income (50th pct)', short: 'p50', plain: 'middle-income' },
	{ key: 'kfr75', label: 'High-income (75th pct)', short: 'p75', plain: 'high-income' }
];

let countiesCache = null;
let derivedCache = null;
let placesCache = null;

export async function loadCounties() {
	if (countiesCache) return countiesCache;
	const [rows, derived] = await Promise.all([d3.json(asset('counties.json')), loadDerived()]);
	for (const r of rows) {
		// Privacy noise can push shares slightly below zero; clamp for display only.
		for (const k of ['top20_25', 'top20_75', 'coll25', 'coll75', 'jail25']) {
			if (r[k] != null && r[k] < 0) r[k] = 0;
		}
		r.gap = r.kfr75 != null && r.kfr25 != null ? r.kfr75 - r.kfr25 : null;
		r.reliable = r.n != null && r.n >= MIN_N;
		r.region = derived.regions[r.state] ?? 'Other';
		r.label = `${r.county}, ${r.state}`;
	}
	countiesCache = rows;
	return rows;
}

/** Stage-2 pipeline output: national summaries, correlations, twins, examples. */
export async function loadDerived() {
	if (derivedCache) return derivedCache;
	derivedCache = await d3.json(asset('derived.json'));
	return derivedCache;
}

/** Cities and towns mapped to their county, for the search box. Each entry is
 *  [name, state, fips]. Built by scripts/build_places.py from a public
 *  city-to-county list; a town that straddles two counties is listed in both. */
export async function loadPlaces() {
	if (placesCache) return placesCache;
	const rows = await d3.json(asset('places.json'));
	placesCache = rows.map(([name, state, fips]) => ({ name, state, fips, label: `${name}, ${state}` }));
	return placesCache;
}

let shapeCache = null;
export function countyShapes() {
	shapeCache ??= topojson.feature(usTopo, usTopo.objects.counties).features;
	return shapeCache;
}

/** Average adult income rank of children whose parents sat at percentile `p`
 *  (25 to 75). The Atlas publishes each county's outcomes as a straight line in
 *  parent rank: across all reliable counties the published 50th-percentile value
 *  is within 0.35 points of the midpoint of the 25th and 75th. Reading values
 *  between the three published points is therefore reading the Atlas's own
 *  line, not inventing data. We do not extrapolate outside 25 to 75. */
export function kfrAt(d, p) {
	if (!d || d.kfr25 == null || d.kfr50 == null || d.kfr75 == null) return null;
	return p <= 50
		? d.kfr25 + ((p - 25) / 25) * (d.kfr50 - d.kfr25)
		: d.kfr50 + ((p - 50) / 25) * (d.kfr75 - d.kfr50);
}
export const parentWord = (p) => (p < 40 ? 'low-income' : p <= 60 ? 'middle-income' : 'high-income');

/** Population density band (people per square mile, by order of magnitude). */
export const DENSITY_BANDS = ['Under 10', '10 to 100', '100 to 1,000', '1,000 to 10,000', 'Over 10,000'];
export const densityBand = (d) =>
	d.popdens == null ? null : Math.min(4, Math.max(0, Math.floor(Math.log10(Math.max(d.popdens, 1)))));

export function stateFeatures() {
	return topojson.feature(usTopo, usTopo.objects.states).features;
}

/** One row per state: the average of its reliable counties, weighted by the
 *  number of children each county contributed, so a state reads as "the average
 *  child raised here" rather than "the average county here". */
export function rollupStates(counties) {
	const names = new Map(stateFeatures().map((f) => [f.id, f.properties.name]));
	const ok = counties.filter((d) => d.reliable && d.kfr25 != null && d.kfr50 != null && d.kfr75 != null);
	return Array.from(d3.group(ok, (d) => d.fips.slice(0, 2)), ([id, rows]) => {
		const tot = d3.sum(rows, (d) => d.n);
		const w = (k) => d3.sum(rows, (d) => d[k] * d.n) / tot;
		const name = names.get(id) ?? rows[0].state;
		const s = {
			id, fips: id, isState: true, state: rows[0].state, name, label: name, county: name,
			kfr25: w('kfr25'), kfr50: w('kfr50'), kfr75: w('kfr75'),
			n: tot, counties: rows.length, reliable: true, region: rows[0].region
		};
		s.gap = s.kfr75 - s.kfr25;
		return s;
	});
}

/** The county containing a longitude/latitude, for "use my location". Runs in
 *  the browser against the boundary file already loaded: nothing is sent anywhere. */
let boxes = null;
export function countyAt(lon, lat) {
	const feats = countyShapes();
	boxes ??= feats.map((f) => d3.geoBounds(f));
	for (let i = 0; i < feats.length; i++) {
		const [[x0, y0], [x1, y1]] = boxes[i];
		if (lat < y0 || lat > y1) continue;
		if (x0 <= x1 ? lon < x0 || lon > x1 : lon < x0 && lon > x1) continue;
		if (d3.geoContains(feats[i], [lon, lat])) return feats[i].id;
	}
	return null;
}

export function stateShapes() {
	return topojson.mesh(usTopo, usTopo.objects.states, (a, b) => a !== b);
}
