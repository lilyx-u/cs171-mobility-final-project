<script>
	// Ages 24 to the mid-thirties: where each county's children stood in the
	// national income ranking as they aged, for low-income and high-income
	// parents. Nationally the two groups start 11 points apart and end 17 apart.
	import * as d3 from 'd3';
	import { LOWC, HIGHC, VIOLET, pctile } from '#lib/colors.js';

	let { data, summary, home = null } = $props();

	const width = 640, height = 400;
	const margin = { top: 22, right: 150, bottom: 46, left: 52 };
	const iw = width - margin.left - margin.right;
	const ih = height - margin.top - margin.bottom;

	// The last point is the Atlas's headline measure (income in 2014-15, when the
	// children were 31 to 37), drawn at 34 and labelled as a range.
	const STEPS = [
		{ age: 24, lab: '24', k25: 'kfr24_25', k75: 'kfr24_75' },
		{ age: 26, lab: '26', k25: 'kfr26_25', k75: 'kfr26_75' },
		{ age: 29, lab: '29', k25: 'kfr29_25', k75: 'kfr29_75' },
		{ age: 34, lab: '31 to 37', k25: 'kfr25', k75: 'kfr75' }
	];
	const x = d3.scaleLinear().domain([24, 34]).range([0, iw]);
	const y = d3.scaleLinear().domain([0.25, 0.75]).range([ih, 0]).clamp(true);
	const line = d3.line().x((p) => x(p.age)).y((p) => y(p.v));
	const series = (d, g) => STEPS.map((s) => ({ age: s.age, v: d[g === 25 ? s.k25 : s.k75] }));

	let upto = $state(3); // index of the last age shown; the scrubber moves it
	let playing = $state(false);
	let timer;
	function play() {
		clearInterval(timer);
		upto = 0;
		playing = true;
		timer = setInterval(() => {
			if (upto >= 3) { clearInterval(timer); playing = false; } else upto += 1;
		}, 900);
	}
	$effect(() => () => clearInterval(timer));

	let rows = $derived(
		data.filter((d) => d.reliable && STEPS.every((s) => d[s.k25] != null && d[s.k75] != null))
	);
	// A random-looking but stable sample keeps the background light: 3,000 pairs
	// of lines would hide the two averages the chart is about.
	let sample = $derived(rows.filter((d) => parseInt(d.fips, 10) % 4 === 0));
	let nat = $derived({
		25: STEPS.map((s) => ({ age: s.age, v: d3.mean(rows, (d) => d[s.k25]) })),
		75: STEPS.map((s) => ({ age: s.age, v: d3.mean(rows, (d) => d[s.k75]) }))
	});
	let homeD = $derived(home ? rows.find((d) => d.fips === home) : null);
	let near = $state(null);
	let focus = $derived(near ?? homeD);
	const cut = (pp) => pp.slice(0, upto + 1);
	let gapNow = $derived(nat[75].length ? Math.round((nat[75][upto].v - nat[25][upto].v) * 100) : 0);
	let gapStart = $derived(nat[75].length ? Math.round((nat[75][0].v - nat[25][0].v) * 100) : 0);

	function onmove(e) {
		const svg = e.currentTarget.ownerSVGElement;
		const pt = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM().inverse());
		const mx = pt.x - margin.left, my = pt.y - margin.top;
		const i = d3.minIndex(STEPS.slice(0, upto + 1), (s) => Math.abs(x(s.age) - mx));
		let best = null, bd = 12;
		for (const d of rows) {
			for (const k of [STEPS[i].k25, STEPS[i].k75]) {
				const dy = Math.abs(y(d[k]) - my);
				if (dy < bd) { bd = dy; best = d; }
			}
		}
		near = best;
	}
</script>

<div class="ap">
	<div class="controls">
		<button class="play" onclick={play} disabled={playing}>{playing ? 'Playing…' : '▶ Play from age 24'}</button>
		<label>
			<span>Show up to age {STEPS[upto].lab}</span>
			<input type="range" min="0" max="3" step="1" bind:value={upto} aria-label="Last age shown" />
		</label>
	</div>

	<svg viewBox="0 0 {width} {height}" role="img" aria-label="Average income rank by age for children of low-income and high-income parents">
		<g transform="translate({margin.left},{margin.top})">
			{#each [0.3, 0.4, 0.5, 0.6, 0.7] as t}
				<line class="grid" x1="0" x2={iw} y1={y(t)} y2={y(t)} />
				<text class="tick" x="-8" y={y(t)} dy="0.32em" text-anchor="end">{pctile(t)}</text>
			{/each}
			{#each STEPS as s, i}
				<line class="vgrid" x1={x(s.age)} x2={x(s.age)} y1="0" y2={ih} />
				<text class="tick" class:dimmed={i > upto} x={x(s.age)} y={ih + 16} text-anchor="middle">{s.lab}</text>
			{/each}
			<text class="lab" x={iw / 2} y={ih + 36} text-anchor="middle">Age when income was measured</text>
			<text class="lab" transform="translate(-40,{ih / 2}) rotate(-90)" text-anchor="middle">Income percentile among people the same age</text>

			<g class="bg">
				{#each sample as d (d.fips)}
					<path d={line(cut(series(d, 75)))} stroke={HIGHC} />
					<path d={line(cut(series(d, 25)))} stroke={LOWC} />
				{/each}
			</g>

			<!-- the widening gap, shaded between the two national averages -->
			{#if upto > 0}
				<path class="wedge" d={d3.area().x((p) => x(p.age)).y0((p, i) => y(nat[25][i].v)).y1((p) => y(p.v))(cut(nat[75]))} />
			{/if}
			<path class="nat" d={line(cut(nat[75]))} stroke={HIGHC} />
			<path class="nat" d={line(cut(nat[25]))} stroke={LOWC} />
			{#each cut(nat[75]) as p, i}
				<circle cx={x(p.age)} cy={y(p.v)} r="4" fill={HIGHC} class="ndot" />
				<circle cx={x(p.age)} cy={y(nat[25][i].v)} r="4" fill={LOWC} class="ndot" />
			{/each}
			<text class="val" x={x(24) + 8} y={y(nat[75][0].v) - 10}>{pctile(nat[75][0].v)}</text>
			<text class="val" x={x(24) + 8} y={y(nat[25][0].v) + 18}>{pctile(nat[25][0].v)}</text>
			{#if upto > 0}
				<text class="val" x={x(STEPS[upto].age)} y={y(nat[75][upto].v) - 10} text-anchor="middle">{pctile(nat[75][upto].v)}</text>
				<text class="val" x={x(STEPS[upto].age)} y={y(nat[25][upto].v) + 18} text-anchor="middle">{pctile(nat[25][upto].v)}</text>
			{/if}
			<g transform="translate({x(STEPS[upto].age) + 12},0)">
				<text class="key" y={y(nat[75][upto].v)} dy="0.32em" fill={HIGHC}>high-income parents</text>
				<text class="key" y={y(nat[25][upto].v)} dy="0.32em" fill={LOWC}>low-income parents</text>
				{#if upto > 0}
					<text class="gap" y={y((nat[75][upto].v + nat[25][upto].v) / 2)} dy="0.32em">{gapNow} points apart</text>
					<text class="gapsub" y={y((nat[75][upto].v + nat[25][upto].v) / 2) + 12} dy="0.32em">({Math.round(nat[75][upto].v * 100)} − {Math.round(nat[25][upto].v * 100)})</text>
				{/if}
			</g>

			{#if focus}
				{@const mine = homeD && focus.fips === homeD.fips}
				<g class="focus" style="color:{mine ? VIOLET : '#1b2233'}">
					<path d={line(cut(series(focus, 75)))} />
					<path d={line(cut(series(focus, 25)))} />
					{#each cut(series(focus, 75)) as p}<circle cx={x(p.age)} cy={y(p.v)} r="3" />{/each}
					{#each cut(series(focus, 25)) as p}<circle cx={x(p.age)} cy={y(p.v)} r="3" />{/each}
				</g>
			{/if}

			<rect x="0" y="0" width={iw} height={ih} fill="transparent" style="cursor:crosshair"
				onmousemove={onmove} onmouseleave={() => (near = null)} role="presentation" />
		</g>
	</svg>

	<p class="caption">
		{#if focus}
			{@const a = series(focus, 25)}
			{@const b = series(focus, 75)}
			<strong style="color:{homeD && focus.fips === homeD.fips ? VIOLET : 'inherit'}">{focus.label}{homeD && focus.fips === homeD.fips ? ' (yours)' : ''}:</strong>
			low-income children went from the {pctile(a[0].v)} at 24 to the {pctile(a[upto].v)} by {STEPS[upto].lab};
			high-income children from the {pctile(b[0].v)} to the {pctile(b[upto].v)}. The gap moved from
			{Math.round((b[0].v - a[0].v) * 100)} to {Math.round((b[upto].v - a[upto].v) * 100)} percentile points.
		{:else}
			At 24 the two groups are {gapStart} percentile points apart on average; by {STEPS[upto].lab} they are {gapNow} apart.
			A point is one percentile, so the gap is simply the upper line's rank minus the lower line's.
			The thick lines are the average county, the faint ones a quarter of all counties. Hover to read one county.
		{/if}
	</p>
</div>

<style>
	.ap { font-family: var(--ui, system-ui); }
	svg { width: 100%; height: auto; display: block; }
	.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin-bottom: 6px; font-size: 13px; }
	.controls label { display: flex; align-items: center; gap: 8px; color: var(--ink-2); }
	.controls label span { min-width: 12.5em; }
	.play { font: inherit; padding: 5px 12px; border: 1px solid var(--ink); background: var(--ink); color: #fff; border-radius: 999px; cursor: pointer; }
	.play:disabled { opacity: 0.6; cursor: default; }
	input[type='range'] { accent-color: #1b2233; width: 140px; }
	.grid { stroke: #ebeae6; }
	.vgrid { stroke: #ebeae6; }
	.tick { font-size: 10px; fill: #75746f; }
	.tick.dimmed { fill: #c4c4be; }
	.lab { font-size: 11.5px; fill: var(--ink-2); }
	.bg path { fill: none; stroke-width: 0.8; opacity: 0.1; }
	.wedge { fill: #1b2233; opacity: 0.06; }
	.nat { fill: none; stroke-width: 3; }
	.ndot { stroke: #fff; stroke-width: 1.5; }
	.val { font-size: 11px; font-weight: 600; fill: var(--ink); paint-order: stroke; stroke: #fff; stroke-width: 3px; }
	.key { font-size: 11px; font-weight: 600; }
	.gap { font-size: 11px; font-weight: 600; fill: var(--ink); }
	.gapsub { font-size: 10px; fill: var(--ink-2); }
	.focus path { fill: none; stroke: currentColor; stroke-width: 2; stroke-dasharray: 5 3; }
	.focus circle { fill: currentColor; stroke: #fff; stroke-width: 1; }
	.caption { font-size: 13px; color: var(--ink-2); margin: 6px 0 0; min-height: 5.8em; }
</style>
