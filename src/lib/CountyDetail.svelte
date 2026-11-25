<script>
	// The card that answers "Where did you grow up?": one county's mobility curve
	// (where its children ended up, for three levels of parent income) drawn
	// against the median U.S. county, followed by a short table of its numbers.
	import * as d3 from 'd3';
	import { PERCENTILES, LARGE_N } from '#lib/data.js';
	import { pctile, ordinal } from '#lib/colors.js';

	// `summary` (derived.json) draws the median county behind this one;
	// `peers` (all counties) gives the rank among large counties.
	let { county = null, summary = null, peers = [] } = $props();

	const width = 340;
	const height = 252;
	const margin = { top: 18, right: 20, bottom: 46, left: 60 };
	const iw = width - margin.left - margin.right;
	const ih = height - margin.top - margin.bottom;

	const pct = d3.format('.0%');
	// Mobility curve: mean child income rank at three parental percentiles.
	const xs = [25, 50, 75];
	const x = d3.scaleLinear().domain([25, 75]).range([0, iw]);
	const y = d3.scaleLinear().domain([0.24, 0.76]).range([ih, 0]).clamp(true);
	const mk = d3.line().x((d) => x(d.p)).y((d) => y(d.v));

	let pts = $derived(
		county
			? xs.map((p, i) => ({ p, v: county[PERCENTILES[i].key] })).filter((d) => d.v != null)
			: []
	);
	let line = $derived(mk(pts));
	// The median county: the middle county, nationally, at each parental percentile.
	let natPts = $derived(summary ? xs.map((p, i) => ({ p, v: summary.national[PERCENTILES[i].key].median })) : []);
	let natLine = $derived(natPts.length ? mk(natPts) : null);
	// The median line is labelled halfway along its left-hand segment, clear of
	// the numbers on the dots, on whichever side this county's line is not.
	const mid = (a) => (a[0].v + a[1].v) / 2;
	let natBelow = $derived(pts.length === 3 && natPts.length === 3 ? mid(pts) >= mid(natPts) : true);

	// Where this county sits among large counties (>= 20,000 children) for
	// children of low-income parents. 1 = best.
	let large = $derived.by(() => {
		if (!county || !county.reliable) return null;
		const big = peers.filter((d) => d.reliable && (d.n ?? 0) >= LARGE_N && d.kfr25 != null);
		if (!big.some((d) => d.fips === county.fips)) return { n: big.length, pos: null };
		const pos = 1 + big.filter((d) => d.kfr25 > county.kfr25).length;
		return { n: big.length, pos };
	});

	const diff = (v, m) => {
		const d = Math.round((v - m) * 100);
		return d === 0 ? 'the same as' : `${Math.abs(d)} point${Math.abs(d) === 1 ? '' : 's'} ${d > 0 ? 'above' : 'below'}`;
	};
</script>

{#if county}
	<div class="detail">
		<h3>{county.county}, {county.state}</h3>
		<p class="meta">{county.cz} &middot; n = {d3.format(',')(county.n ?? 0)} children</p>

		<p class="charttitle">Where children raised here ended up as adults</p>
		<svg viewBox="0 0 {width} {height}" role="img"
			aria-label="Mobility curve for {county.label}: children's average adult income percentile for parents at the 25th, 50th and 75th percentile, with the median U.S. county for comparison">
			<g transform="translate({margin.left},{margin.top})">
				{#each [0.3, 0.4, 0.5, 0.6, 0.7] as t}
					<line class="grid" x1="0" x2={iw} y1={y(t)} y2={y(t)} />
					<text class="tick" x="-6" y={y(t)} text-anchor="end" dy="0.32em">{pctile(t)}</text>
				{/each}
				<!-- y axis: the child's place in the national ranking, as an adult -->
				<text class="lab strong" transform="translate(-46,{ih / 2}) rotate(-90)" text-anchor="middle">
					<tspan x="0">Child's income percentile</tspan>
					<tspan x="0" dy="13">as an adult</tspan>
				</text>
				{#if natLine}
					<path d={natLine} class="nat" fill="none" />
					<text class="natlab" x={x(37.5)} y={y(mid(natPts)) + (natBelow ? 15 : -8)} text-anchor="middle">median U.S. county</text>
				{/if}
				<path d={line} class="curve" fill="none" />
				{#each pts as d}
					<circle cx={x(d.p)} cy={y(d.v)} r="4.5" />
					<!-- each dot says which percentile those children reached -->
					<text class="val" x={x(d.p)} y={y(d.v) - 9} text-anchor={d.p === 25 ? 'start' : d.p === 75 ? 'end' : 'middle'}
						dx={d.p === 25 ? -4 : d.p === 75 ? 4 : 0}>{pctile(d.v)}</text>
				{/each}
				{#each xs as p, i}
					<text class="tick" x={x(p)} y={ih + 15} text-anchor="middle">{ordinal(p)}</text>
					<text class="tick sub" x={x(p)} y={ih + 26} text-anchor={i === 0 ? 'start' : i === 2 ? 'end' : 'middle'}
						dx={i === 0 ? -12 : i === 2 ? 12 : 0}>{['low income', 'middle', 'high income'][i]}</text>
				{/each}
				<text class="lab strong" x={iw / 2} y={ih + 41} text-anchor="middle">Parents' income percentile</text>
			</g>
		</svg>
		<p class="how">
			<strong>How to read it.</strong> Each <span class="dot"></span> purple dot is the average income
			percentile, as adults, of children raised in {county.county} whose parents sat at that income
			percentile. A higher dot means those children earned more. The dashed grey line is the
			median U.S. county: half of all counties are above it, half below.
		</p>

		<dl>
			<div>
				<dt>Low-income children reach</dt>
				<dd>
					{pctile(county.kfr25)}
					{#if summary}<span class="vs">{diff(county.kfr25, summary.national.kfr25.median)} the median county ({pctile(summary.national.kfr25.median)})</span>{/if}
				</dd>
			</div>
			<div>
				<dt>High-income children reach</dt>
				<dd>
					{pctile(county.kfr75)}
					{#if summary}<span class="vs">median county {pctile(summary.national.kfr75.median)}</span>{/if}
				</dd>
			</div>
			<div>
				<dt>Gap, rich minus poor children</dt>
				<dd>
					{county.gap != null ? `${Math.round(county.gap * 100)} points` : '—'}
					{#if summary}<span class="vs">median county {Math.round(summary.national.gap.median * 100)} points</span>{/if}
				</dd>
			</div>
			{#if large}
				<div>
					<dt>Among {d3.format(',')(large.n)} large counties</dt>
					<dd>{large.pos ? `${ordinal(large.pos)} best for low-income children` : 'not large enough to rank'}</dd>
				</div>
			{/if}
			<div><dt>Share of low-income children reaching the top fifth</dt><dd>{county.top20_25 != null ? pct(county.top20_25) : '—'}</dd></div>
			<div><dt>Poverty rate</dt><dd>{county.poverty != null ? pct(county.poverty) : '—'}</dd></div>
			<div><dt>Test score (SD from national average)</dt><dd>{county.score != null ? d3.format('+.2f')(county.score) : '—'}</dd></div>
		</dl>
	</div>
{:else}
	<div class="detail empty"><p>Click a county to see its mobility curve.</p></div>
{/if}

<style>
	.detail { font-size: 13px; }
	.empty { color: #75746f; padding: 12px 0; }
	h3 { margin: 0; font-size: 15px; }
	.meta { margin: 2px 0 8px; color: #75746f; font-size: 12px; }
	.charttitle { margin: 0 0 2px; font-size: 12.5px; font-weight: 600; color: #1b2233; }
	svg { width: 100%; height: auto; display: block; }
	/* Purple is the site's "your county" colour; the card keeps the promise the intro makes. */
	.curve { stroke: #6250d6; stroke-width: 2.5; }
	circle { fill: #6250d6; stroke: #fff; stroke-width: 1.5; }
	.val { font-size: 11.5px; font-weight: 700; fill: #6250d6; paint-order: stroke; stroke: #fff; stroke-width: 3px; }
	.nat { stroke: #8a8f9c; stroke-width: 1.5; stroke-dasharray: 4 3; }
	.natlab { font-size: 10.5px; fill: #75746f; paint-order: stroke; stroke: #fff; stroke-width: 3px; }
	.grid { stroke: #ebeae6; }
	.tick { font-size: 10.5px; fill: #75746f; }
	.tick.sub { font-size: 9.5px; fill: #8a8f9c; }
	.lab { font-size: 11.5px; fill: #52514e; }
	.lab.strong { fill: #1b2233; font-weight: 500; }
	.how { margin: 6px 0 0; font-size: 12px; line-height: 1.45; color: #52514e; }
	.how strong { color: #1b2233; }
	.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #6250d6; }
	dl { margin: 10px 0 0; }
	dl div { display: flex; justify-content: space-between; gap: 12px; padding: 4px 0; border-bottom: 1px solid #ebeae6; }
	dt { color: #52514e; }
	dd { margin: 0; font-variant-numeric: tabular-nums; font-weight: 500; text-align: right; }
	.vs { display: block; font-weight: 400; font-size: 11px; color: #75746f; }
</style>
