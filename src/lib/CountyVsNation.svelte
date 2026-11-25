<script>
	// "Your county versus the nation": where the pinned county sits, among all
	// reliable counties, on each characteristic the scatterplot can show. Ties
	// the predictors section back to the reader's own place.
	import * as d3 from 'd3';
	import { X_VARS } from '#lib/data.js';
	import { ordinal } from '#lib/colors.js';

	let { data, county = null, correlations = [], active = null, onpick = () => {} } = $props();

	const W = 240, H = 26;

	let rows = $derived.by(() => {
		const rel = data.filter((d) => d.reliable);
		return X_VARS.map((v) => {
			const vals = rel.map((d) => d[v.key]).filter((x) => x != null).sort(d3.ascending);
			const x = d3.scaleLinear().domain([d3.quantile(vals, 0.02), d3.quantile(vals, 0.98)]).range([4, W - 4]).clamp(true);
			const mine = county?.[v.key];
			const r = correlations.find((c) => c.key === v.key)?.r25 ?? null;
			return {
				...v, x, mine, r,
				p10: d3.quantile(vals, 0.1), p90: d3.quantile(vals, 0.9), med: d3.quantile(vals, 0.5),
				// share of counties with a lower value, as a percentile among counties
				pos: mine == null ? null : Math.max(1, Math.min(99, Math.round((d3.bisectLeft(vals, mine) / vals.length) * 100)))
			};
		});
	});
	const lean = (r) =>
		r == null || Math.abs(r) < 0.15 ? 'says little about outcomes' : r < 0 ? 'more of it goes with lower outcomes' : 'more of it goes with higher outcomes';
</script>

<div class="cvn">
	{#if county}
		<h3><span class="dot"></span>{county.label} against every other county</h3>
		<p class="sub">
			The grey band holds the middle 80% of counties and the black tick is the median county (half of all counties are higher, half lower). Click a row to put it on the chart above.
		</p>
		<div class="rows">
			{#each rows as r}
				<button class="row" class:on={active === r.key} onclick={() => onpick(r.key)}>
					<span class="name">{r.label}<small>{lean(r.r)}</small></span>
					<svg viewBox="0 0 {W} {H}" aria-hidden="true">
						<line class="track" x1="4" x2={W - 4} y1={H / 2} y2={H / 2} />
						<rect class="band" x={r.x(r.p10)} width={r.x(r.p90) - r.x(r.p10)} y={H / 2 - 5} height="10" rx="3" />
						<line class="med" x1={r.x(r.med)} x2={r.x(r.med)} y1={H / 2 - 8} y2={H / 2 + 8} />
						{#if r.mine != null}
							<circle cx={r.x(r.mine)} cy={H / 2} r="6" />
						{/if}
					</svg>
					<span class="val">
						{#if r.mine != null}
							<b>{r.fmt(r.mine)}</b>
							<small>higher than {r.pos}% of counties &middot; median county {r.fmt(r.med)}</small>
						{:else}
							<small>not reported</small>
						{/if}
					</span>
				</button>
			{/each}
		</div>
	{:else}
		<p class="empty">
			<strong>See your own county here.</strong> Pick a county at the top of the page and this panel
			shows where it sits on each of these characteristics, against every other county.
		</p>
	{/if}
</div>

<style>
	.cvn { font-family: var(--ui, system-ui); margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--rule); }
	h3 { margin: 0; font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
	.dot { width: 10px; height: 10px; border-radius: 50%; background: #6250d6; display: inline-block; }
	.sub { margin: 2px 0 8px; font-size: 13px; color: var(--ink-2); }
	.rows { display: grid; grid-template-columns: 1fr 1fr; gap: 0 28px; }
	.row { display: grid; grid-template-columns: 170px 1fr 150px; align-items: center; gap: 10px; padding: 5px 6px; font: inherit; text-align: left; background: none; border: 0; border-bottom: 1px solid var(--rule); cursor: pointer; color: var(--ink); border-radius: 4px; }
	.row:hover { background: #f7f7f5; }
	.row.on { background: #efeefc; }
	.name { font-size: 13px; font-weight: 500; display: grid; }
	small { font-size: 11px; font-weight: 400; color: var(--ink-2); }
	svg { width: 100%; height: 26px; display: block; }
	.track { stroke: #e1e1dc; stroke-width: 1; }
	.band { fill: #1b2233; opacity: 0.16; }
	.med { stroke: #1b2233; stroke-width: 1.5; }
	circle { fill: #6250d6; stroke: #fff; stroke-width: 2; }
	.val { display: grid; text-align: right; font-size: 13px; font-variant-numeric: tabular-nums; }
	.empty { margin: 0; font-size: 14px; color: var(--ink-2); }
	.empty strong { color: var(--ink); }
	@media (max-width: 980px) { .rows { grid-template-columns: 1fr; } }
	@media (max-width: 560px) { .row { grid-template-columns: 1fr 1fr; } .row svg { grid-column: 1 / -1; order: 3; } }
</style>
