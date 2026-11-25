import * as d3 from 'd3';

// One palette for the whole site. Blue = children do better than the
// reference point, red = worse, with a neutral grey midpoint (never a hue).
export const BLUE = '#2a78d6';
export const RED = '#d6422a';
export const NEUTRAL = '#ecebe6';
export const VIOLET = '#6250d6'; // reserved for "your county"
export const INK = '#1b2233';
// A second county the reader has chosen to compare against (pinned on the fan,
// or the twin in the twin finder). Amber is used for nothing else.
export const COMPARE = '#b06a00';
// The two parent groups, wherever they are drawn as marks rather than as a
// map ramp: warm for children of low-income parents, blue for high-income.
export const LOWC = '#b8341f';
export const HIGHC = '#1f62b8';
// Counties too small to estimate. Drawn as a hatched texture (see CountyMap),
// never a flat grey, so "no data" cannot be mistaken for a point on the ramp.
export const GREY_OUT = '#cfcfca';
export const NO_DATA_LABEL = 'No data: fewer than 1,000 children';

const divergingInterp = d3.piecewise(d3.interpolateLab, [RED, NEUTRAL, BLUE]);

/** Diverging scale, red below `mid`, blue above. */
export function divergingScale(lo, mid, hi) {
	return d3.scaleDiverging(divergingInterp).domain([lo, mid, hi]).clamp(true);
}

/** Centred on the group's own national mean, so the map shows within-group geography. */
export function levelScale(values) {
	const mean = d3.mean(values);
	const [lo, hi] = [d3.quantile(values, 0.02), d3.quantile(values, 0.98)];
	const half = Math.max(mean - lo, hi - mean);
	return divergingScale(mean - half, mean, mean + half);
}

/** Fixed scale shared by the twin maps and the "same scale" map toggle: 50 = the
 *  middle of the national income distribution, so blue literally means "ends up
 *  above the median adult". */
export const SHARED_SCALE = divergingScale(0.3, 0.5, 0.7);

/** Single-hue sequential ramp for the p75 - p25 gap (a magnitude, not a polarity). */
export function gapScale(values) {
	return d3
		.scaleSequential(d3.interpolateOranges)
		.domain([d3.quantile(values, 0.02), d3.quantile(values, 0.98)])
		.clamp(true);
}

/** Single-hue sequential ramp (light to dark teal) for a county characteristic
 *  such as the poverty rate. Teal is used nowhere else on the site, so "more of
 *  this thing" is never confused with "better outcome" (blue) or "worse" (red). */
export function seqScale(values) {
	return d3
		.scaleSequential(d3.interpolateLab('#eef2f1', '#0b5c5c'))
		.domain([d3.quantile(values, 0.02), d3.quantile(values, 0.98)])
		.clamp(true);
}

export const pct = d3.format('.0%');
export const pct1 = d3.format('.1%');
export const pts = (v) => `${Math.round(v * 100)} pts`;
export const ordinal = (n) => {
	const s = ['th', 'st', 'nd', 'rd'];
	const v = n % 100;
	return n + (s[(v - 20) % 10] || s[v] || s[0]);
};
/** 0.42 -> "42nd" (a percentile, written as a rank rather than a percent). */
export const pctile = (v) => ordinal(Math.round(v * 100));
export const rank = (v) => `${pctile(v)} percentile`;
