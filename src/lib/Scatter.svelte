<script>
	import * as d3 from 'd3';
	import { BLUE, RED, VIOLET, pctile } from '#lib/colors.js';

	let {
		data,
		xVar = 'poverty',
		yVar = 'kfr25',
		xLabel = '',
		yLabel = '',
		xFmt = null,
		highlighted = null,
		selected = null,
		home = null,
		brushable = false,
		showFit = true,
		showR = true,
		onhover = () => {},
		onselect = () => {},
		onbrush = () => {}
	} = $props();

	const width = 520;
	const height = 360;
	const margin = { top: 16, right: 16, bottom: 46, left: 54 };
	const iw = width - margin.left - margin.right;
	const ih = height - margin.top - margin.bottom;

	let points = $derived(data.filter((d) => d.reliable && d[xVar] != null && d[yVar] != null));

	let x = $derived(d3.scaleLinear().domain(d3.extent(points, (d) => d[xVar])).nice().range([0, iw]));
	let y = $derived(d3.scaleLinear().domain(d3.extent(points, (d) => d[yVar])).nice().range([ih, 0]));

	// Least-squares line and Pearson r, so the panel can say how strong the trend is.
	let fit = $derived.by(() => {
		if (points.length < 2) return null;
		const mx = d3.mean(points, (d) => d[xVar]);
		const my = d3.mean(points, (d) => d[yVar]);
		let sxy = 0, sxx = 0, syy = 0;
		for (const d of points) {
			sxy += (d[xVar] - mx) * (d[yVar] - my);
			sxx += (d[xVar] - mx) ** 2;
			syy += (d[yVar] - my) ** 2;
		}
		if (!sxx) return null;
		const b = sxy / sxx;
		const r = sxy / Math.sqrt(sxx * syy);
		const dom = x.domain();
		return { r, x1: dom[0], y1: my + b * (dom[0] - mx), x2: dom[1], y2: my + b * (dom[1] - mx) };
	});

	let homeD = $derived(home ? points.find((d) => d.fips === home) : null);

	let xAxisG = $state();
	let yAxisG = $state();
	let brushG = $state();

	$effect(() => {
		const ax = d3.axisBottom(x).ticks(5).tickSize(-ih).tickPadding(8);
		if (xFmt) ax.tickFormat(xFmt);
		d3.select(xAxisG).call(ax).select('.domain').remove();
	});
	$effect(() => {
		// Outcomes are percentiles: label them as ranks ("40th"), never as percents.
		d3.select(yAxisG)
			.call(d3.axisLeft(y).ticks(5).tickSize(-iw).tickPadding(8).tickFormat(pctile))
			.select('.domain')
			.remove();
	});

	$effect(() => {
		if (!brushable || !brushG) return;
		const brush = d3
			.brush()
			.extent([[0, 0], [iw, ih]])
			.on('brush end', ({ selection }) => {
				if (!selection) return onbrush(null);
				const [[x0, y0], [x1, y1]] = selection;
				const hit = new Set(
					points
						.filter((d) => x(d[xVar]) >= x0 && x(d[xVar]) <= x1 && y(d[yVar]) >= y0 && y(d[yVar]) <= y1)
						.map((d) => d.fips)
				);
				onbrush(hit);
			});
		d3.select(brushG).call(brush);
		return () => d3.select(brushG).on('.brush', null);
	});

	const rWord = (r) => {
		const a = Math.abs(r);
		return a > 0.55 ? 'strong' : a > 0.35 ? 'moderate' : a > 0.15 ? 'weak' : 'almost no';
	};
</script>

<svg viewBox="0 0 {width} {height}" role="img" aria-label="Scatterplot of county characteristic against outcome">
	<g transform="translate({margin.left},{margin.top})">
		<g class="axis" transform="translate(0,{ih})" bind:this={xAxisG}></g>
		<g class="axis" bind:this={yAxisG}></g>

		<g class="dots">
			{#each points as d (d.fips)}
				<circle
					cx={x(d[xVar])}
					cy={y(d[yVar])}
					r={selected === d.fips ? 5 : 2.4}
					class:sel={selected === d.fips}
					opacity={highlighted ? (highlighted.has(d.fips) ? 0.95 : 0.05) : 0.38}
					pointer-events="none"
				/>
			{/each}
		</g>

		{#if fit && showFit}
			<line class="fit" x1={x(fit.x1)} y1={y(fit.y1)} x2={x(fit.x2)} y2={y(fit.y2)} />
		{/if}

		{#if homeD}
			<g transform="translate({x(homeD[xVar])},{y(homeD[yVar])})" pointer-events="none">
				<circle r="7" fill="none" stroke="#fff" stroke-width="4" />
				<circle r="7" fill="none" stroke={VIOLET} stroke-width="2" />
				<circle r="2.5" fill={VIOLET} />
				<text class="homelab" x="11" y="4">{homeD.county}, {homeD.state}</text>
			</g>
		{/if}

		{#if brushable}
			<g class="brush" bind:this={brushG}></g>
		{:else}
			<!-- Generous hit targets sit above the visible dots, so hovering does not
			     require landing on a 2px mark. -->
			<g class="hits">
				{#each points as d (d.fips)}
					<circle
						cx={x(d[xVar])}
						cy={y(d[yVar])}
						r="6"
						onmouseenter={() => onhover(d)}
						onmouseleave={() => onhover(null)}
						onclick={() => onselect(d.fips === selected ? null : d.fips)}
						role="button"
						tabindex="-1"
					/>
				{/each}
			</g>
		{/if}

		{#if fit && showR}
			<text class="r" x={iw} y="-4" text-anchor="end">
				r = {d3.format('+.2f')(fit.r)}, {rWord(fit.r)} {fit.r < 0 ? 'negative' : 'positive'} relationship
			</text>
		{/if}

		<text class="lab" x={iw / 2} y={ih + 40} text-anchor="middle">{xLabel}</text>
		<text class="lab" transform="translate(-42,{ih / 2}) rotate(-90)" text-anchor="middle">{yLabel}</text>
	</g>
</svg>

<style>
	svg { width: 100%; height: auto; display: block; font-family: var(--ui, system-ui); }
	.dots circle { fill: #2a78d6; }
	.dots circle.sel { fill: #d6422a; stroke: #111; stroke-width: 1; opacity: 1 !important; }
	.hits circle { fill: transparent; cursor: pointer; }
	.fit { stroke: #1b2233; stroke-width: 1.5; }
	.lab { font-size: 12px; fill: var(--ink-2, #52514e); }
	.r { font-size: 12px; fill: var(--ink, #1b2233); font-weight: 500; }
	.homelab { font-size: 11px; fill: #6250d6; font-weight: 600; paint-order: stroke; stroke: #fff; stroke-width: 3px; }
	.axis :global(text) { font-size: 10px; fill: #75746f; }
	.axis :global(line) { stroke: #ebeae6; }
</style>
