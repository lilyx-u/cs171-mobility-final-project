<script>
	import * as d3 from 'd3';
	import { pctile, GREY_OUT, NO_DATA_LABEL } from '#lib/colors.js';

	// `fmt` formats the end and middle ticks; the default writes percentiles as
	// ranks ("30th", "50th", "70th"), never as percents.
	let { scale, title = '', lowLabel = '', highLabel = '', fmt = pctile, noData = true } = $props();

	const w = 180;
	const h = 10;
	const stops = d3.range(0, 1.0001, 1 / 24);

	let dom = $derived(scale.domain());
	let lo = $derived(dom[0]);
	let hi = $derived(dom[dom.length - 1]);
	let mid = $derived(dom.length === 3 ? dom[1] : null);
	let f = $derived(fmt ?? pctile);
	let id = `lg${Math.random().toString(36).slice(2, 8)}`;
</script>

<div class="lg">
	{#if title}<div class="t">{title}</div>{/if}
	<svg width={w} height={h + 16} viewBox="0 0 {w} {h + 16}">
		<defs>
			<linearGradient id={id}>
				{#each stops as s}
					<stop offset="{s * 100}%" stop-color={scale(lo + s * (hi - lo))} />
				{/each}
			</linearGradient>
		</defs>
		<rect x="0" y="0" width={w} height={h} rx="2" fill="url(#{id})" />
		<text x="0" y={h + 12}>{lowLabel || f(lo)}</text>
		{#if mid != null}
			<line x1={w * (mid - lo) / (hi - lo)} x2={w * (mid - lo) / (hi - lo)} y1="0" y2={h} stroke="#fff" stroke-width="1.5" />
			<text x={w * (mid - lo) / (hi - lo)} y={h + 12} text-anchor="middle">{f(mid)}</text>
		{/if}
		<text x={w} y={h + 12} text-anchor="end">{highLabel || f(hi)}</text>
	</svg>
	{#if noData}
		<div class="nd">
			<svg width="18" height="12" viewBox="0 0 18 12" aria-hidden="true">
				<defs>
					<pattern id="{id}nd" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
						<rect width="4" height="4" fill="#fbfbfa" />
						<line x1="0" y1="0" x2="0" y2="4" stroke={GREY_OUT} stroke-width="2" />
					</pattern>
				</defs>
				<rect width="18" height="12" rx="2" fill="url(#{id}nd)" stroke={GREY_OUT} stroke-width="1" />
			</svg>
			<span>{NO_DATA_LABEL}</span>
		</div>
	{/if}
</div>

<style>
	.lg { font: 11px var(--ui, system-ui); color: var(--ink-2, #555); }
	.t { margin-bottom: 2px; font-weight: 500; color: var(--ink, #1b2233); }
	text { font-size: 10px; fill: var(--ink-2, #555); }
	.nd { display: flex; align-items: center; gap: 6px; margin-top: 2px; font-size: 10px; }
</style>
