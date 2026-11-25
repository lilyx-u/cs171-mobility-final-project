<script>
	// Twin counties: two places that give children of low-income parents the same
	// outcome, but children of high-income parents very different ones. Pick any
	// county and the finder searches the large counties for its closest "twin
	// with a different ceiling".
	import * as d3 from 'd3';
	import { LARGE_N } from '#lib/data.js';
	import { VIOLET, INK, COMPARE, pctile, ordinal } from '#lib/colors.js';

	let { data, summary, home = null } = $props();

	const width = 640, height = 380;
	const margin = { top: 24, right: 150, bottom: 44, left: 52 };
	const iw = width - margin.left - margin.right;
	const ih = height - margin.top - margin.bottom;
	const KEYS = ['kfr25', 'kfr50', 'kfr75'];
	const x = d3.scalePoint().domain(KEYS).range([0, iw]);
	const y = d3.scaleLinear().domain([0.25, 0.75]).range([ih, 0]).clamp(true);
	const line = d3.line().x((p) => x(p.k)).y((p) => y(p.v));
	const curve = (d) => KEYS.map((k) => ({ k, v: d[k] }));

	let pool = $derived(data.filter((d) => d.reliable && (d.n ?? 0) >= LARGE_N && KEYS.every((k) => d[k] != null)));
	let byFips = $derived(new Map(data.map((d) => [d.fips, d])));
	let picked = $state(null); // fips chosen in this panel; falls back to the reader's county
	let baseFips = $derived(picked ?? home ?? summary?.twins?.[0]?.flat.fips ?? null);
	let base = $derived(baseFips ? byFips.get(baseFips) : null);
	let usable = $derived(base && base.reliable && KEYS.every((k) => base[k] != null));

	// The twin: among large counties whose low-income outcome is within one
	// point of the base county's, the one whose rich-poor gap differs the most.
	let twin = $derived.by(() => {
		if (!usable) return null;
		const close = pool.filter((d) => d.fips !== base.fips && Math.abs(d.kfr25 - base.kfr25) <= 0.01);
		if (!close.length) return null;
		return close[d3.maxIndex(close, (d) => Math.abs(d.gap - base.gap))];
	});
	let ceilDiff = $derived(twin ? Math.round(Math.abs(twin.kfr75 - base.kfr75) * 100) : 0);
	let higher = $derived(twin && twin.kfr75 > base.kfr75 ? twin : base);

	// A few striking pairs from stage 2 of the pipeline, offered as starting points.
	let examples = $derived(
		(summary?.twins ?? [])
			.filter((t, i, a) => a.findIndex((u) => u.flat.fips === t.flat.fips) === i)
			.slice(0, 4)
			.map((t) => t.flat)
	);
	let options = $derived([...pool].sort((a, b) => d3.ascending(a.label, b.label)));
</script>

<div class="tf">
	<div class="controls">
		<label>
			Start from
			<select value={baseFips} onchange={(e) => (picked = e.currentTarget.value)}>
				{#if base && !options.some((d) => d.fips === base.fips)}<option value={base.fips}>{base.label}</option>{/if}
				{#each options as d}<option value={d.fips}>{d.label}</option>{/each}
			</select>
		</label>
		{#if home && baseFips !== home}<button onclick={() => (picked = null)}>Use my county</button>{/if}
		<span class="eg">
			Try:
			{#each examples as e}<button class="chip" onclick={() => (picked = e.fips)}>{e.name}</button>{/each}
		</span>
	</div>

	{#if usable && twin}
		<svg viewBox="0 0 {width} {height}" role="img" aria-label="Mobility curves of {base.label} and {twin.label}">
			<g transform="translate({margin.left},{margin.top})">
				{#each [0.3, 0.4, 0.5, 0.6, 0.7] as t}
					<line class="grid" x1="0" x2={iw} y1={y(t)} y2={y(t)} />
					<text class="tick" x="-8" y={y(t)} dy="0.32em" text-anchor="end">{pctile(t)}</text>
				{/each}
				{#each KEYS as k, i}
					<text class="tick" x={x(k)} y={ih + 16} text-anchor="middle">{ordinal([25, 50, 75][i])}</text>
				{/each}
				<text class="lab" x={iw / 2} y={ih + 34} text-anchor="middle">Parents' income percentile</text>
				<text class="lab" transform="translate(-40,{ih / 2}) rotate(-90)" text-anchor="middle">Child's adult income rank</text>

				<!-- the difference between the two ceilings, shaded -->
				<path class="wedge" d={d3.area().x((p) => x(p.k)).y0((p) => y(p.v)).y1((p, i) => y(curve(twin)[i].v))(curve(base))} />
				<path class="ln twin" d={line(curve(twin))} stroke={COMPARE} />
				<path class="ln base" d={line(curve(base))} style="stroke:{baseFips === home ? VIOLET : INK}" />
				{#each curve(twin) as p}<circle cx={x(p.k)} cy={y(p.v)} r="4" fill={COMPARE} />{/each}
				{#each curve(base) as p}<circle cx={x(p.k)} cy={y(p.v)} r="4" fill={baseFips === home ? VIOLET : INK} />{/each}

				<text class="val" x={x('kfr25') + 4} y={y(Math.max(base.kfr25, twin.kfr25)) - 12}>both about the {pctile(base.kfr25)}</text>
				{#each [base, twin].sort((a, b) => b.kfr75 - a.kfr75) as d, i}
					<g transform="translate({x('kfr75') + 10},{y(d.kfr75) + (Math.abs(base.kfr75 - twin.kfr75) < 0.025 ? (i ? 9 : -9) : 0)})">
						<text class="name" dy="0.32em" style={d === twin ? `fill:${COMPARE}` : d === base && baseFips === home ? `fill:${VIOLET}` : ''}>{d.county}, {d.state}</text>
						<text class="sub" y="13" dy="0.32em">{pctile(d.kfr75)} percentile</text>
					</g>
				{/each}
				<text class="floor" x={x('kfr25') + 4} y={y(Math.min(base.kfr25, twin.kfr25)) + 20}>same floor</text>
			</g>
		</svg>
		<p class="caption">
			<strong>{base.label}</strong> and <strong>{twin.label}</strong> both land children of low-income parents at about the
			{pctile(base.kfr25)} percentile. For children of high-income parents they are {ceilDiff} percentile points apart, with
			{higher.label} the higher. A single county average would file these two places together.
		</p>
	{:else if base && !usable}
		<p class="caption empty">{base.label} has too few children in the study to compare. Choose another county above.</p>
	{:else if base}
		<p class="caption empty">No large county gives low-income children the same outcome as {base.label} (within one point). Choose another county above.</p>
	{/if}
</div>

<style>
	.tf { font-family: var(--ui, system-ui); }
	svg { width: 100%; height: auto; display: block; }
	.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 13px; color: var(--ink-2); }
	label { display: flex; align-items: center; gap: 6px; }
	select { font: inherit; padding: 5px 8px; border: 1px solid var(--rule); border-radius: 4px; background: #fff; max-width: 220px; }
	button { font: inherit; padding: 4px 10px; border: 1px solid var(--rule); background: #fff; border-radius: 999px; cursor: pointer; color: var(--ink); }
	.eg { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
	.chip { border-style: dashed; font-size: 12px; }
	.grid { stroke: #ebeae6; }
	.tick { font-size: 10px; fill: #75746f; }
	.lab { font-size: 11.5px; fill: var(--ink-2); }
	.wedge { fill: #e8a33d; opacity: 0.22; }
	.ln { fill: none; stroke-width: 2.5; }
	circle { stroke: #fff; stroke-width: 1.5; }
	.val { font-size: 11px; font-weight: 600; fill: var(--ink); paint-order: stroke; stroke: #fff; stroke-width: 3px; }
	.name { font-size: 11.5px; font-weight: 600; fill: var(--ink); }
	.sub { font-size: 10.5px; fill: var(--ink-2); }
	.floor { font-size: 10.5px; fill: var(--ink-2); font-style: italic; }
	.caption { font-size: 13px; color: var(--ink-2); margin: 6px 0 0; min-height: 4.4em; }
	.caption strong { color: var(--ink); }
</style>
