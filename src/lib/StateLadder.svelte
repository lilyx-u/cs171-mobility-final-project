<script>
	// One rung per state: a vertical bar from where its low-income children end up
	// to where its high-income children end up. Sorted, the bottom ends climb
	// steeply while the top ends barely move: the site's argument at state level.
	import * as d3 from 'd3';
	import { kfrAt } from '#lib/data.js';
	import { LOWC, HIGHC, VIOLET, pctile } from '#lib/colors.js';

	let {
		states,
		p = 25, // the parent percentile chosen on the map's slider
		homeState = null, // 2-digit state id of the reader's county
		active = null, // state id hovered here or on the map
		onhover = () => {},
		onpick = () => {}
	} = $props();

	const width = 1080, height = 300;
	const margin = { top: 26, right: 96, bottom: 34, left: 52 };
	const iw = width - margin.left - margin.right;
	const ih = height - margin.top - margin.bottom;

	const SORTS = [
		{ key: 'kfr25', label: 'low-income children' },
		{ key: 'kfr75', label: 'high-income children' },
		{ key: 'gap', label: 'gap between them' }
	];
	let sortBy = $state('kfr25');

	let order = $derived([...states].sort((a, b) => d3.ascending(a[sortBy], b[sortBy])).map((s) => s.id));
	let x = $derived(d3.scaleBand().domain(order).range([0, iw]).padding(0.25));
	const y = d3.scaleLinear().domain([0.3, 0.7]).range([ih, 0]);
	let act = $derived(active ? states.find((s) => s.id === active) : null);
	let showP = $derived(p > 26 && p < 74);
	// Spread across states at each end, quoted in the caption.
	const mid80 = (k) => {
		const v = states.map((s) => s[k]).sort(d3.ascending);
		return v.length ? Math.round((d3.quantile(v, 0.9) - d3.quantile(v, 0.1)) * 100) : 0;
	};
	let spreadLo = $derived(mid80('kfr25'));
	let spreadHi = $derived(mid80('kfr75'));
</script>

<div class="ladder">
	<div class="controls" role="group" aria-label="Sort states">
		<span class="lbl">Sort states by</span>
		{#each SORTS as s}
			<button class:on={sortBy === s.key} onclick={() => (sortBy = s.key)}>{s.label}</button>
		{/each}
		<span class="hint">Hover a state to find it on the map. Click to open its counties.</span>
	</div>

	<svg viewBox="0 0 {width} {height}" role="img" aria-label="Each state's outcomes for children of low-income and high-income parents">
		<g transform="translate({margin.left},{margin.top})">
			{#each [0.3, 0.4, 0.5, 0.6, 0.7] as t}
				<line class="grid" class:mid={t === 0.5} x1="0" x2={iw} y1={y(t)} y2={y(t)} />
				<text class="tick" x="-8" y={y(t)} dy="0.32em" text-anchor="end">{pctile(t)}</text>
			{/each}
			<text class="tick" x={iw + 6} y={y(0.5)} dy="0.32em">median adult</text>
			<text class="ylab" transform="translate(-40,{ih / 2}) rotate(-90)" text-anchor="middle">Child's adult income rank</text>

			{#each states as s (s.id)}
				<g class="rung" class:on={active === s.id} class:home={homeState === s.id}
					style="transform: translateX({x(s.id) + x.bandwidth() / 2}px)">
					<line class="bar" y1={y(s.kfr25)} y2={y(s.kfr75)} />
					<circle cy={y(s.kfr75)} r="3.6" fill={HIGHC} />
					<circle cy={y(s.kfr25)} r="3.6" fill={LOWC} />
					{#if showP}<line class="pmark" x1="-5" x2="5" y1={y(kfrAt(s, p))} y2={y(kfrAt(s, p))} />{/if}
					<text class="abbr" y={ih + 14} text-anchor="middle">{s.state}</text>
					<rect class="hitbox" x={-x.step() / 2} width={x.step()} y="-6" height={ih + 26}
						onmouseenter={() => onhover(s.id)} onmouseleave={() => onhover(null)}
						onclick={() => onpick(s.id)} role="button" tabindex="-1" />
				</g>
			{/each}

			<!-- direct labels instead of a legend -->
			<g class="key" transform="translate({iw + 10},0)">
				<circle cy={y(0.66)} r="3.6" fill={HIGHC} /><text x="8" y={y(0.66)} dy="0.32em">high-income</text>
				<text x="8" y={y(0.66) + 12} dy="0.32em">parents (75th)</text>
				<circle cy={y(0.36)} r="3.6" fill={LOWC} /><text x="8" y={y(0.36)} dy="0.32em">low-income</text>
				<text x="8" y={y(0.36) + 12} dy="0.32em">parents (25th)</text>
			</g>

			{#if act}
				{@const cx = x(act.id) + x.bandwidth() / 2}
				<text class="val" x={cx} y={y(act.kfr75) - 8} text-anchor="middle">{pctile(act.kfr75)}</text>
				<text class="val" x={cx} y={y(act.kfr25) + 16} text-anchor="middle">{pctile(act.kfr25)}</text>
			{/if}
		</g>
	</svg>

	<p class="caption">
		{#if act}
			<strong>{act.name}:</strong> children of low-income parents reached the {pctile(act.kfr25)} percentile,
			children of high-income parents the {pctile(act.kfr75)}, a gap of {Math.round(act.gap * 100)} points
			({act.counties} counties, weighted by the number of children in each).
		{:else}
			Each bar is one state, from its low-income children (red dot) up to its high-income children (blue dot).
			The middle 80% of states span {spreadLo} points for low-income children and {spreadHi} for high-income children:
			the same narrowing as the counties, one level up.
			{#if showP}The short black tick is the parent percentile chosen on the slider ({p}th).{/if}
		{/if}
	</p>
</div>

<style>
	.ladder { font-family: var(--ui, system-ui); margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--rule); }
	svg { width: 100%; height: auto; display: block; }
	.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-bottom: 4px; font-size: 13px; }
	.lbl { color: var(--ink-2); margin-right: 4px; }
	.hint { margin-left: 12px; color: var(--ink-2); }
	button { font: inherit; font-size: 13px; padding: 5px 11px; border: 1px solid var(--rule); background: #fff; border-radius: 999px; cursor: pointer; color: var(--ink); }
	button.on { background: var(--ink); color: #fff; border-color: var(--ink); }
	.grid { stroke: #ebeae6; }
	.grid.mid { stroke: #b9b9b4; stroke-dasharray: 3 3; }
	.tick { font-size: 10px; fill: #75746f; }
	.ylab { font-size: 11px; fill: var(--ink-2); }
	.rung { transition: transform 600ms cubic-bezier(0.3, 0, 0.2, 1); }
	.bar { stroke: #c4c4be; stroke-width: 3; stroke-linecap: round; }
	.rung circle { stroke: #fff; stroke-width: 1; }
	.pmark { stroke: #1b2233; stroke-width: 2; }
	.abbr { font-size: 9.5px; fill: #75746f; }
	.rung.on .bar { stroke: #1b2233; }
	.rung.on .abbr { fill: #1b2233; font-weight: 700; }
	.rung.home .bar { stroke: #6250d6; }
	.rung.home .abbr { fill: #6250d6; font-weight: 700; }
	.hitbox { fill: transparent; cursor: zoom-in; }
	.key text { font-size: 10.5px; fill: var(--ink-2); }
	.val { font-size: 11px; font-weight: 600; fill: var(--ink); paint-order: stroke; stroke: #fff; stroke-width: 3px; pointer-events: none; }
	.caption { font-size: 13px; color: var(--ink-2); margin: 6px 0 0; min-height: 3em; max-width: 90ch; }
	.caption strong { color: var(--ink); }
</style>
