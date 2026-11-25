<script>
	// The density gradient: counties grouped by how crowded they are, one strip
	// per band, with the band's average drawn through for both parent groups.
	// Hovering a band reports its counties so the page can light them on a map.
	import * as d3 from 'd3';
	import { DENSITY_BANDS, densityBand } from '#lib/data.js';
	import { LOWC, HIGHC, VIOLET, pctile } from '#lib/colors.js';

	let { data, home = null, group = 'kfr25', onband = () => {} } = $props();

	const width = 560, height = 380;
	const margin = { top: 20, right: 92, bottom: 58, left: 52 };
	const iw = width - margin.left - margin.right;
	const ih = height - margin.top - margin.bottom;

	const x = d3.scaleBand().domain(d3.range(5)).range([0, iw]).padding(0.14);
	const y = d3.scaleLinear().domain([0.25, 0.75]).range([ih, 0]).clamp(true);
	// Stable horizontal jitter from the county code, so dots do not jump on redraw.
	const jitter = (fips) => ((parseInt(fips, 10) * 9301 + 49297) % 233280) / 233280 - 0.5;

	let rows = $derived(
		data
			.filter((d) => d.reliable && d.kfr25 != null && d.kfr75 != null && densityBand(d) != null)
			.map((d) => ({ d, b: densityBand(d), j: jitter(d.fips) }))
	);
	let bands = $derived(
		d3.range(5).map((b) => {
			const r = rows.filter((q) => q.b === b);
			return { b, n: r.length, kfr25: d3.mean(r, (q) => q.d.kfr25), kfr75: d3.mean(r, (q) => q.d.kfr75), set: new Set(r.map((q) => q.d.fips)) };
		})
	);
	let active = $state(null);
	let homeRow = $derived(home ? rows.find((q) => q.d.fips === home) : null);
	const mk = (k) => d3.line().x((b) => x(b.b) + x.bandwidth() / 2).y((b) => y(b[k]));
	let drop25 = $derived(Math.round((bands[0].kfr25 - bands[3].kfr25) * 100));
	let drop75 = $derived(Math.round((bands[0].kfr75 - bands[3].kfr75) * 100));

	function enter(b) { active = b; onband(bands[b].set); }
	function leave() { active = null; onband(null); }
</script>

<div class="ds">
	<svg viewBox="0 0 {width} {height}" role="img" aria-label="Counties by population density band against children's adult income rank">
		<g transform="translate({margin.left},{margin.top})">
			{#each [0.3, 0.4, 0.5, 0.6, 0.7] as t}
				<line class="grid" x1="0" x2={iw} y1={y(t)} y2={y(t)} />
				<text class="tick" x="-8" y={y(t)} dy="0.32em" text-anchor="end">{pctile(t)}</text>
			{/each}
			<text class="lab" transform="translate(-40,{ih / 2}) rotate(-90)" text-anchor="middle">Child's adult income rank</text>

			{#each bands as b}
				<rect class="col" class:on={active === b.b} x={x(b.b)} width={x.bandwidth()} y="0" height={ih} rx="4" />
			{/each}

			<g class="dots" style="color:{group === 'kfr25' ? LOWC : HIGHC}">
				{#each rows as q (q.d.fips)}
					<circle cx={x(q.b) + x.bandwidth() / 2 + q.j * x.bandwidth() * 0.82} cy={y(q.d[group])} r="1.7"
						class:off={active != null && active !== q.b} />
				{/each}
			</g>

			<!-- band averages for both groups, so the two gradients can be compared -->
			<path class="mean" d={mk('kfr75')(bands)} stroke={HIGHC} class:quiet={group !== 'kfr75'} />
			<path class="mean" d={mk('kfr25')(bands)} stroke={LOWC} class:quiet={group !== 'kfr25'} />
			{#each bands as b}
				<circle class="mdot" cx={x(b.b) + x.bandwidth() / 2} cy={y(b.kfr75)} r="4" fill={HIGHC} />
				<circle class="mdot" cx={x(b.b) + x.bandwidth() / 2} cy={y(b.kfr25)} r="4" fill={LOWC} />
				{#if active === b.b || active == null}
					<text class="mval" x={x(b.b) + x.bandwidth() / 2} y={y(b.kfr75) - 9} text-anchor="middle">{pctile(b.kfr75)}</text>
					<text class="mval" x={x(b.b) + x.bandwidth() / 2} y={y(b.kfr25) + 17} text-anchor="middle">{pctile(b.kfr25)}</text>
				{/if}
				<text class="tick" x={x(b.b) + x.bandwidth() / 2} y={ih + 16} text-anchor="middle">{DENSITY_BANDS[b.b]}</text>
				<text class="n" x={x(b.b) + x.bandwidth() / 2} y={ih + 29} text-anchor="middle">{d3.format(',')(b.n)} counties</text>
			{/each}
			<text class="lab" x={iw / 2} y={ih + 48} text-anchor="middle">People per square mile: rural on the left, dense cities on the right</text>
			<text class="key" x={iw + 8} y={y(bands[4].kfr75)} dy="0.32em" fill={HIGHC}>high-income</text>
			<text class="key" x={iw + 8} y={y(bands[4].kfr75) + 12} dy="0.32em" fill={HIGHC}>parents, average</text>
			<text class="key" x={iw + 8} y={y(bands[4].kfr25)} dy="0.32em" fill={LOWC}>low-income</text>
			<text class="key" x={iw + 8} y={y(bands[4].kfr25) + 12} dy="0.32em" fill={LOWC}>parents, average</text>

			{#if homeRow}
				<g transform="translate({x(homeRow.b) + x.bandwidth() / 2 + homeRow.j * x.bandwidth() * 0.82},{y(homeRow.d[group])})" pointer-events="none">
					<circle r="6" fill="none" stroke="#fff" stroke-width="4" />
					<circle r="6" fill="none" stroke={VIOLET} stroke-width="2" />
					<circle r="2" fill={VIOLET} />
				</g>
			{/if}

			{#each bands as b}
				<rect x={x(b.b) - x.step() * 0.07} width={x.step()} y="0" height={ih + 34} fill="transparent"
					onmouseenter={() => enter(b.b)} onmouseleave={leave} role="presentation" />
			{/each}
		</g>
	</svg>
	<p class="caption">
		{#if active != null}
			<strong>{DENSITY_BANDS[active]} people per square mile: {d3.format(',')(bands[active].n)} counties.</strong>
			Low-income children there reached the {pctile(bands[active].kfr25)} percentile on average, high-income
			children the {pctile(bands[active].kfr75)}. These counties are lit on the map.
		{:else}
			From the emptiest counties to ordinary cities, the average outcome for low-income children falls
			{drop25} points; for high-income children it falls {drop75}. Hover a band to see where those counties are.
		{/if}
	</p>
</div>

<style>
	.ds { font-family: var(--ui, system-ui); }
	svg { width: 100%; height: auto; display: block; }
	.grid { stroke: #ebeae6; }
	.tick { font-size: 10px; fill: #75746f; }
	.n { font-size: 9.5px; fill: #8a8f9c; }
	.lab { font-size: 11.5px; fill: var(--ink-2); }
	.col { fill: #1b2233; opacity: 0; }
	.col.on { opacity: 0.05; }
	.dots circle { fill: currentColor; opacity: 0.3; }
	.dots circle.off { opacity: 0.05; }
	.mean { fill: none; stroke-width: 2.5; }
	.mean.quiet { stroke-width: 1.5; stroke-dasharray: 4 3; }
	.mdot { stroke: #fff; stroke-width: 1.5; }
	.mval { font-size: 11px; font-weight: 600; fill: var(--ink); paint-order: stroke; stroke: #fff; stroke-width: 3px; }
	.key { font-size: 10.5px; font-weight: 600; }
	.caption { font-size: 13px; color: var(--ink-2); margin: 6px 0 0; min-height: 3.2em; }
	.caption strong { color: var(--ink); }
</style>
