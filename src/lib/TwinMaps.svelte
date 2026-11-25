<script>
	// Two maps on one shared scale. Centre = the national median adult, so blue
	// means "children from this county end up above the median" and red below.
	// The p75 map is blue almost everywhere; the p25 map is where the geography is.
	import CountyMap from '#lib/CountyMap.svelte';
	import Legend from '#lib/Legend.svelte';
	import { SHARED_SCALE } from '#lib/colors.js';

	let { data, home = null, onhover = () => {} } = $props();
</script>

<div class="twins">
	<div class="pair">
		<figure>
			<figcaption>
				<strong>Children of low-income parents</strong>
				<span>parents at the 25th percentile</span>
			</figcaption>
			<CountyMap {data} colorBy="kfr25" scale={SHARED_SCALE} {home} legend={false} {onhover} />
		</figure>
		<figure>
			<figcaption>
				<strong>Children of high-income parents</strong>
				<span>parents at the 75th percentile</span>
			</figcaption>
			<CountyMap {data} colorBy="kfr75" scale={SHARED_SCALE} {home} legend={false} {onhover} />
		</figure>
	</div>
	<div class="legend">
		<Legend scale={SHARED_SCALE} title="Children's average adult income rank (percentile)" lowLabel="30th or below" highLabel="70th or above" />
		<span class="note">Same colour scale on both maps. The white tick marks the national median adult (50th percentile).</span>
	</div>
</div>

<style>
	.twins { font-family: var(--ui, system-ui); }
	.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
	figure { margin: 0; }
	figcaption { display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px; font-size: 14px; }
	figcaption span { color: var(--ink-2); font-size: 12px; }
	.legend { display: flex; align-items: flex-end; gap: 16px; margin-top: 10px; flex-wrap: wrap; }
	.note { font-size: 12px; color: var(--ink-2); max-width: 44ch; }
	@media (max-width: 760px) { .pair { grid-template-columns: 1fr; } }
</style>
