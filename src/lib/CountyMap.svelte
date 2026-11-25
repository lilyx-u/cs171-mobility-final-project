<script>
	import * as d3 from 'd3';
	import { countyShapes, stateShapes, stateFeatures } from '#lib/data.js';
	import { levelScale, gapScale, seqScale, GREY_OUT, VIOLET, rank } from '#lib/colors.js';
	import Legend from '#lib/Legend.svelte';

	let {
		data,
		colorBy = 'kfr25',
		accessor = null, // optional (d) => value; overrides colorBy (used by the parent-income slider)
		scheme = 'level', // 'level' | 'gap' | 'seq'
		scale = null, // pass a d3 scale to override the automatic one (shared scales)
		fmt = rank, // formats the hovered value; outcomes read as percentiles by default
		highlighted = null, // Set of fips to keep bright; others dim
		selected = null, // fips drawn with a heavy outline
		home = null, // fips drawn with the "your county" ring
		// State view: `level="state"` paints one shape per state from `states`
		// (see rollupStates). `zoom` is a 2-digit state id; when set, the map flies
		// to that state and shows its counties. `outline` rings one state.
		level = 'county',
		states = [],
		zoom = null,
		outline = null,
		onstate = () => {},
		legend = true,
		legendTitle = '',
		legendFmt = undefined,
		legendLow = '',
		legendHigh = '',
		tooltip = true,
		onhover = () => {},
		onselect = () => {}
	} = $props();

	const width = 975;
	const height = 610;
	const features = countyShapes();
	const statesMesh = stateShapes();
	const stFeatures = stateFeatures();
	// This build of us-atlas ships raw lon/lat, not pre-projected coordinates,
	// so the projection has to be applied here.
	const projection = d3
		.geoAlbersUsa()
		.fitSize([width, height], { type: 'FeatureCollection', features });
	const path = d3.geoPath(projection);
	const shapes = features.map((f) => ({ id: f.id, st: f.id.slice(0, 2), d: path(f) }));
	const stShapes = stFeatures.map((f) => ({ id: f.id, d: path(f), box: path.bounds(f) })).filter((s) => s.d);
	const meshD = path(statesMesh);
	const centroid = new Map(features.map((f) => [f.id, path.centroid(f)]));
	// One hatch pattern per map instance: "no data" is a texture, not a colour.
	const hatchId = `hatch${Math.random().toString(36).slice(2, 8)}`;

	let get = $derived(accessor ?? ((d) => d[colorBy]));
	let byFips = $derived(new Map(data.map((d) => [d.fips, d])));
	let stById = $derived(new Map(states.map((s) => [s.id, s])));

	// The colour scale always comes from the counties, so switching to the state
	// view or flying into a state never changes what a colour means.
	let color = $derived.by(() => {
		if (scale) return scale;
		const vals = data
			.filter((d) => d.reliable && get(d) != null)
			.map((d) => get(d))
			.sort(d3.ascending);
		return scheme === 'gap' ? gapScale(vals) : scheme === 'seq' ? seqScale(vals) : levelScale(vals);
	});

	const hatch = `url(#${hatchId})`;
	function fill(id) {
		const d = byFips.get(id);
		const v = d && d.reliable ? get(d) : null;
		return v == null ? hatch : color(v);
	}
	function stateFill(id) {
		const s = stById.get(id);
		const v = s ? get(s) : null;
		return v == null ? hatch : color(v);
	}

	let showStates = $derived(level === 'state' && !zoom);
	let view = $derived.by(() => {
		const s = zoom ? stShapes.find((x) => x.id === zoom) : null;
		if (!s) return { k: 1, x: 0, y: 0 };
		const [[x0, y0], [x1, y1]] = s.box;
		const k = Math.min(9, 0.86 / Math.max((x1 - x0) / width, (y1 - y0) / height));
		return { k, x: width / 2 - (k * (x0 + x1)) / 2, y: height / 2 - (k * (y0 + y1)) / 2 };
	});
	let outlineD = $derived(outline ? stShapes.find((s) => s.id === outline)?.d : null);

	let hover = $state(null); // { d, x, y } in CSS pixels relative to wrapper
	let wrap = $state();

	function move(e, d) {
		if (!tooltip || !wrap) return;
		const r = wrap.getBoundingClientRect();
		hover = d ? { d, x: e.clientX - r.left, y: e.clientY - r.top } : null;
	}
	function leave() {
		onhover(null);
		hover = null;
	}

	let homePt = $derived(home ? centroid.get(home) : null);
</script>

<div class="wrap" bind:this={wrap}>
	<svg viewBox="0 0 {width} {height}" role="img" aria-label="US {showStates ? 'states' : 'counties'} coloured by outcome">
		<defs>
			<pattern id={hatchId} width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
				<rect width="5" height="5" fill="#fbfbfa" />
				<line x1="0" y1="0" x2="0" y2="5" stroke={GREY_OUT} stroke-width="2" />
			</pattern>
		</defs>
		<g class="zoomer" style="transform: translate({view.x}px, {view.y}px) scale({view.k})">
			<g role="group" onmouseleave={leave}>
				{#each shapes as f (f.id)}
					{@const d = byFips.get(f.id)}
					<path
						d={f.d}
						fill={fill(f.id)}
						class="county"
						class:dim={(highlighted && !highlighted.has(f.id)) || (zoom && f.st !== zoom)}
						class:hit={highlighted && highlighted.has(f.id)}
						class:sel={selected === f.id}
						onmouseenter={(e) => { onhover(d ?? null); move(e, d); }}
						onmousemove={(e) => move(e, d)}
						onclick={() => d && onselect(d.fips === selected ? null : d.fips)}
						role="button"
						tabindex="-1"
					/>
				{/each}
			</g>
			{#if showStates}
				<g role="group" onmouseleave={leave}>
					{#each stShapes as s (s.id)}
						{@const d = stById.get(s.id)}
						<path
							d={s.d}
							fill={stateFill(s.id)}
							class="state"
							onmouseenter={(e) => { onhover(d ?? null); move(e, d); }}
							onmousemove={(e) => move(e, d)}
							onclick={() => d && onstate(s.id)}
							role="button"
							tabindex="-1"
						/>
					{/each}
				</g>
			{/if}
			<path d={meshD} class="mesh" fill="none" pointer-events="none" />
			{#if outlineD}
				<path d={outlineD} class="outline" fill="none" pointer-events="none" />
			{/if}
			{#if homePt}
				<g class="home" transform="translate({homePt[0]},{homePt[1]}) scale({1 / view.k})" pointer-events="none">
					<circle r="11" fill="none" stroke="#fff" stroke-width="5" />
					<circle r="11" fill="none" stroke={VIOLET} stroke-width="2.5" />
					<circle r="2.5" fill={VIOLET} />
				</g>
			{/if}
		</g>
	</svg>

	{#if hover}
		<div class="tip" style="left:{hover.x}px; top:{hover.y}px">
			<strong>{hover.d.isState ? hover.d.name : `${hover.d.county}, ${hover.d.state}`}</strong>
			{#if hover.d.reliable && get(hover.d) != null}
				<span>{fmt(get(hover.d))}</span>
				{#if hover.d.isState}<span class="muted">average of {hover.d.counties} counties &middot; click to open</span>{/if}
			{:else}
				<span class="muted">no data: too few children to estimate</span>
			{/if}
		</div>
	{/if}

	{#if legend}
		<div class="legend">
			<Legend scale={color} title={legendTitle} fmt={legendFmt} lowLabel={legendLow} highLabel={legendHigh} />
		</div>
	{/if}
</div>

<style>
	.wrap { position: relative; overflow: hidden; }
	svg { width: 100%; height: auto; display: block; }
	.zoomer { transform-origin: 0 0; transition: transform 650ms cubic-bezier(0.3, 0, 0.2, 1); }
	.county { stroke: #fff; stroke-width: 0.15; cursor: pointer; vector-effect: non-scaling-stroke; }
	.county:hover { stroke: #111; stroke-width: 1; }
	.state { stroke: #fff; stroke-width: 0.8; cursor: zoom-in; vector-effect: non-scaling-stroke; }
	.state:hover { stroke: #111; stroke-width: 1.6; }
	.mesh { stroke: #fff; stroke-width: 0.7; vector-effect: non-scaling-stroke; }
	.outline { stroke: #111; stroke-width: 2; vector-effect: non-scaling-stroke; }
	/* Keep the base map readable when only a handful of counties are selected. */
	.dim { opacity: 0.22; }
	.hit { stroke: #111; stroke-width: 0.9; }
	.sel { stroke: #111; stroke-width: 1.6; }
	.tip {
		position: absolute;
		transform: translate(14px, -50%);
		background: var(--ink, #1b2233);
		color: #fff;
		font: 12px/1.3 var(--ui, system-ui);
		padding: 6px 9px;
		border-radius: 4px;
		pointer-events: none;
		white-space: nowrap;
		display: grid;
		gap: 2px;
		z-index: 5;
	}
	.tip .muted { color: #c9cbd3; }
	.legend { position: absolute; left: 8px; bottom: 8px; background: rgba(255, 255, 255, 0.85); padding: 4px 6px; border-radius: 4px; }
	@media (max-width: 640px) {
		.legend { position: static; margin-top: 6px; background: none; padding: 0; }
	}
</style>
