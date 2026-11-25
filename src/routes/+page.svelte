<script>
	// The story page. One scrolling argument in five parts (see SECTIONS below),
	// with the reader's own county carried through every chart. This file holds
	// the prose, the page-level state that links charts to each other, and the
	// layout; each chart is its own component in src/lib.
	import { onMount, tick } from 'svelte';
	import * as d3 from 'd3';
	import SiteNav from '#lib/SiteNav.svelte';
	import CountyMap from '#lib/CountyMap.svelte';
	import Scatter from '#lib/Scatter.svelte';
	import CountyDetail from '#lib/CountyDetail.svelte';
	import CountySearch from '#lib/CountySearch.svelte';
	import MobilityFan from '#lib/MobilityFan.svelte';
	import TwinMaps from '#lib/TwinMaps.svelte';
	import PercentileRow from '#lib/PercentileRow.svelte';
	import StateLadder from '#lib/StateLadder.svelte';
	import CountyVsNation from '#lib/CountyVsNation.svelte';
	import DensityStrips from '#lib/DensityStrips.svelte';
	import AgePaths from '#lib/AgePaths.svelte';
	import TwinFinder from '#lib/TwinFinder.svelte';
	import { loadCounties, loadDerived, loadPlaces, rollupStates, kfrAt, parentWord, X_VARS, SCORE_UNIT, LARGE_N } from '#lib/data.js';
	import { story } from '#lib/story.svelte.js';
	import { SHARED_SCALE, pctile, rank, ordinal } from '#lib/colors.js';

	// The site's first sentence, shown in the corner of the navigation bar.
	const BRAND = 'Where you grow up shapes what you earn.';
	// The parts of the story. The same words label the navigation bar and the
	// small heading above each part, so the bar always says where you are.
	const SECTIONS = [
		{ id: 'your-county', label: 'Find your county' },
		{ id: 'map', label: 'The opportunity map' },
		{ id: 'predictors', label: 'What predicts mobility' },
		{ id: 'fan', label: 'Who place matters for' },
		{ id: 'twins', label: 'Rich vs. poor maps' },
		{ id: 'closer', label: 'Three closer looks' },
		{ id: 'data', label: 'About the data' }
	];
	const partLabel = (id) => SECTIONS.find((s) => s.id === id).label;
	// Every chart on the page, for the "Visualizations" menu. `fallback` is the
	// part to scroll to if the chart has not been drawn yet (the data is still loading).
	const CHARTS = [
		{ id: 'viz-percentile', label: 'What a percentile looks like', group: 'Start here', fallback: 'start' },
		{ id: 'your-county', label: "Your county's mobility curve", group: 'Start here', fallback: 'start' },
		{ id: 'viz-map', label: 'County and state map, with income slider', group: partLabel('map'), fallback: 'map' },
		{ id: 'viz-states', label: 'State-by-state chart', group: partLabel('map'), fallback: 'map' },
		{ id: 'viz-predictors', label: 'Scatterplot linked to a map', group: partLabel('predictors'), fallback: 'predictors' },
		{ id: 'viz-county-vs-nation', label: 'Your county against the nation', group: partLabel('predictors'), fallback: 'predictors' },
		{ id: 'viz-fan', label: 'The mobility fan', group: partLabel('fan'), fallback: 'fan' },
		{ id: 'viz-twin-maps', label: 'Two maps on one colour scale', group: partLabel('twins'), fallback: 'twins' },
		{ id: 'viz-density', label: 'Rural vs. urban counties', group: partLabel('closer'), fallback: 'closer' },
		{ id: 'viz-age', label: 'The gap by age, 24 to mid-thirties', group: partLabel('closer'), fallback: 'closer' },
		{ id: 'viz-twin-counties', label: 'Twin-county finder', group: partLabel('closer'), fallback: 'closer' }
	];

	let counties = $state([]);
	let places = $state([]);
	let summary = $state(null);

	// Section-local interaction state
	let parentP = $state(25); // parents' income percentile on the main map, 25 to 75
	let level = $state('county'); // 'county' | 'state'
	let zoomState = $state(null); // 2-digit state id the map has flown into
	let ladderHover = $state(null);
	let sameScale = $state(false);
	let mapHover = $state(null);
	let mapEl = $state();
	let xVar = $state('singlepar');
	let brushed = $state(null);
	let scatterHover = $state(null);
	let fanHover = $state(null);
	let fanStats = $state(null);
	let twinHover = $state(null);
	let densGroup = $state('kfr25');
	let densBand = $state(null);

	let home = $derived(story.home ? counties.find((d) => d.fips === story.home) : null);
	let homeState = $derived(story.home ? story.home.slice(0, 2) : null);
	let states = $derived(counties.length ? rollupStates(counties) : []);
	let zoomed = $derived(zoomState ? states.find((s) => s.id === zoomState) : null);
	let pWord = $derived(parentWord(parentP));
	// A new function each time the slider moves, so the map recolours.
	let mapGet = $derived.by(() => {
		const p = parentP;
		return (d) => kfrAt(d, p);
	});
	// Where the middle 80% of counties fall at the slider's position: the same
	// statistic the fan draws, so the map and the fan can be read against each other.
	let mapStats = $derived.by(() => {
		const v = counties.filter((d) => d.reliable).map((d) => kfrAt(d, parentP)).filter((x) => x != null).sort(d3.ascending);
		if (!v.length) return null;
		return { p10: d3.quantile(v, 0.1), p90: d3.quantile(v, 0.9), med: d3.quantile(v, 0.5) };
	});
	// The best and worst lists follow the slider, the state view and the zoom.
	let ranked = $derived.by(() => {
		const val = (d) => kfrAt(d, parentP);
		const desc = (a, b) => val(b) - val(a);
		if (level === 'state' && !zoomed) {
			const s = [...states].sort(desc);
			return { what: 'states', where: '', best: s.slice(0, 5), worst: s.slice(-5).reverse() };
		}
		const inState = (d) => !zoomed || d.fips.startsWith(zoomed.id);
		let pool = counties.filter((d) => d.reliable && (d.n ?? 0) >= LARGE_N && val(d) != null && inState(d));
		let what = 'large counties';
		if (zoomed && pool.length < 6) {
			pool = counties.filter((d) => d.reliable && val(d) != null && inState(d));
			what = 'counties';
		}
		pool.sort(desc);
		const k = Math.min(5, Math.floor(pool.length / 2));
		return { what, where: zoomed ? ` in ${zoomed.name}` : '', best: pool.slice(0, k), worst: pool.slice(-k).reverse() };
	});
	// The rung to light on the state chart: whatever is hovered there or on the map.
	let activeState = $derived(ladderHover ?? (mapHover ? (mapHover.isState ? mapHover.id : mapHover.fips.slice(0, 2)) : zoomState));

	let xMeta = $derived(X_VARS.find((v) => v.key === xVar));
	let isScore = $derived(xVar.startsWith('score'));
	let brushedSet = $derived(brushed && brushed.size ? brushed : null);
	let brushStats = $derived.by(() => {
		if (!brushedSet) return null;
		const sel = counties.filter((d) => brushedSet.has(d.fips));
		return { n: sel.length, kfr25: d3.mean(sel, (d) => d.kfr25), gap: d3.mean(sel, (d) => d.gap) };
	});
	let corrFor = $derived(summary?.correlations.find((c) => c.key === xVar));
	// The headline spread, quoted in the intro and drawn on the fan, from one source.
	let spread25 = $derived(summary ? Math.round(summary.national.kfr25.spread * 100) : 14);
	let spread75 = $derived(summary ? Math.round(summary.national.kfr75.spread * 100) : 11);

	// Clicking a map changes the pinned county. Say so, and offer an undo, so it
	// never happens silently.
	let notice = $state(null);
	let noticeTimer;
	function pinFromMap(f) {
		if (!f || f === story.home) return;
		const prev = story.home;
		story.home = f;
		notice = { prev, next: f };
		clearTimeout(noticeTimer);
		noticeTimer = setTimeout(() => (notice = null), 25000);
	}
	function undoPin() {
		if (notice) story.home = notice.prev;
		notice = null;
	}
	const nameOf = (f) => counties.find((d) => d.fips === f)?.label ?? 'that county';

	function setLevel(l) {
		level = l;
		zoomState = null;
	}
	function openState(id) {
		level = 'state';
		zoomState = id;
		mapEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
	}

	let restored = $state(false); // true once the saved county has been read back
	onMount(async () => {
		[counties, summary] = await Promise.all([loadCounties(), loadDerived()]);
		// Remember the reader's county between visits (a per-viewer convenience only).
		try {
			const saved = localStorage.getItem('home-county');
			if (saved && !story.home && counties.some((d) => d.fips === saved)) story.home = saved;
		} catch {}
		restored = true;
		// A link straight to one chart (.../#viz-fan) arrives before that chart exists.
		// Now that the charts are drawn and the page has its full height, go there.
		await tick();
		if (location.hash.length > 1) document.getElementById(location.hash.slice(1))?.scrollIntoView();
		// The city list is large and only needed once someone types, so it loads last.
		places = await loadPlaces();
	});
	$effect(() => {
		// Not before the saved county has been read, or this would erase it on load.
		if (!restored) return;
		try {
			if (story.home) localStorage.setItem('home-county', story.home);
			else localStorage.removeItem('home-county');
		} catch {}
	});

	const fmtN = d3.format(',');
	const fmtR = d3.format('+.2f');
	const nat = (k) => summary?.national[k];
	const homeSentence = (h) => {
		if (!h) return '';
		if (!h.reliable) return `${h.label} had fewer than 1,000 children in the study, so its estimates are too noisy to show. Pick a nearby, larger county to follow the story.`;
		const lo = Math.round(h.kfr25 * 100), hi = Math.round(h.kfr75 * 100);
		const typ = summary ? Math.round(nat('kfr25').median * 100) : null;
		return `A child raised in ${h.label} by parents at the 25th income percentile reached, on average, the ${ordinal(lo)} percentile as an adult${typ != null ? ` (in the median U.S. county: the ${ordinal(typ)})` : ''}. A child from the same county whose parents were at the 75th percentile reached the ${ordinal(hi)}. That gap of ${hi - lo} percentile points is ${summary && h.gap > nat('gap').median ? 'wider' : 'narrower'} than in the median county.`;
	};
	// The worked example in the definition of a "point": the median county's two groups.
	let exLo = $derived(summary ? Math.round(nat('kfr25').median * 100) : 42);
	let exHi = $derived(summary ? Math.round(nat('kfr75').median * 100) : 59);
	// The same arithmetic at age 24, for the age chart's own definition.
	let age24 = $derived(summary ? { lo: Math.round(summary.ages.kfr24_25 * 100), hi: Math.round(summary.ages.kfr24_75 * 100) } : null);
	const rSentence = (r) => {
		const a = Math.abs(r);
		const strength = a > 0.55 ? 'strong' : a > 0.35 ? 'moderate' : a > 0.15 ? 'weak' : 'almost no';
		return r < 0
			? `${strength} and negative: counties with more of it had lower outcomes`
			: `${strength} and positive: counties with more of it had higher outcomes`;
	};
</script>

<svelte:head>
	<title>Where you grow up shapes what you earn — the geography of economic mobility</title>
	<meta name="description" content="How much does the county you grew up in shape what you earn as an adult? An interactive story built on the Opportunity Atlas and SEDA." />
</svelte:head>

<SiteNav brand={BRAND} sections={SECTIONS} charts={CHARTS} />

<main>
	<!-- ───────────── HOOK ───────────── -->
	<header id="start" class="hero">
		<p class="kicker">An interactive story about economic mobility in 3,131 US counties</p>
		<h1>Where you grow up<br /><span>shapes what you earn.</span><br />But not for everyone equally.</h1>
		<p class="lede">
			Children of well-off parents do well almost everywhere in America. Children of low-income
			parents do not: for them, the county they were raised in can move their adult income by
			{spread25} percentile points, against {spread75} for children of high-income parents. This
			page follows that difference from the map down to the specific things about a place that
			seem to matter.
		</p>
		<div class="define">
			<p class="definehead">Three terms, used everywhere below</p>
			<dl>
				<div>
					<dt>Income rank (a percentile)</dt>
					<dd>
						Where a person's household income falls among everyone born the same year, from the
						1st percentile (lowest) to the 100th (highest). A child who reaches the 50th percentile
						as an adult out-earns half of their generation.
					</dd>
				</div>
				<div>
					<dt>A point</dt>
					<dd>
						One percentile: one step along that 1-to-100 ranking. Every gap and every difference
						on this page is measured in points, by subtracting one rank from another. Children who
						average the {ordinal(exHi)} percentile and children who average the {ordinal(exLo)} are
						{exHi} − {exLo} = <strong>{exHi - exLo} points</strong> apart.
					</dd>
				</div>
				<div>
					<dt>The median county</dt>
					<dd>
						Our stand-in for an ordinary American county. Line up all
						{summary ? fmtN(summary.counties_reliable) : '2,916'} counties that have enough data from
						the lowest value to the highest and take the one in the middle: half of counties are
						above it, half below. It is worked out separately for each measure.
					</dd>
				</div>
			</dl>
			<p class="definefoot">Here is the first of those, the income rank, as a picture:</p>
		</div>
		{#if summary}
			<div id="viz-percentile">
				<PercentileRow
					lo={home?.reliable ? home.kfr25 : nat('kfr25').median}
					hi={home?.reliable ? home.kfr75 : nat('kfr75').median}
					place={home?.reliable ? home.label : 'the median U.S. county'}
					mine={!!home?.reliable}
				/>
			</div>
		{/if}

		<div class="hook" id="your-county">
			<h2>Where did you grow up?</h2>
			<p>Type a county, city or town. Your county will stay pinned, in purple, through every chart below.</p>
			{#if counties.length}
				<CountySearch data={counties} {places} value={story.home} onpick={(f) => (story.home = f)} />
			{:else}
				<p class="loading">Loading 3,131 counties…</p>
			{/if}
			{#if home}
				<div class="homecard">
					<p class="sentence">{homeSentence(home)}</p>
					{#if home.reliable}
						<div class="curve"><CountyDetail county={home} {summary} peers={counties} /></div>
					{/if}
				</div>
			{/if}
		</div>
	</header>

	<!-- ───────────── ACT 1: THE MAP ───────────── -->
	<section id="map" class="act">
		<div class="prose">
			<p class="actlabel">Part 1 · {partLabel('map')}</p>
			<h2>Outcomes are not scattered at random</h2>
			<p>
				The Opportunity Atlas followed every American child born between 1978 and 1983 into
				their mid-thirties and asked, county by county, where they ended up in the national
				income distribution. The map colours each county by the average adult income rank of
				children whose parents sat at a given point on the income ladder. Blue counties lifted
				those children higher than the national average for their group, red counties lower.
			</p>
			<p>
				Start with children of low-income parents. The Great Plains and the upper Midwest are a
				wall of blue. The Deep South, the Appalachian coalfields and the Native American
				reservations of the Southwest are red. Then drag the slider towards richer parents and
				watch the spread between places shrink.
			</p>
		</div>

		{#if counties.length}
			<div class="viz wide" id="viz-map" bind:this={mapEl}>
				<div class="controls">
					<div class="togglewrap">
						<span class="lbl">Parents' income percentile: <strong>{ordinal(parentP)}</strong> ({pWord})</span>
						<div class="slider">
							<span>25th</span>
							<input type="range" min="25" max="75" step="1" bind:value={parentP}
								aria-label="Parents' income percentile, from the 25th to the 75th" />
							<span>75th</span>
							<div class="toggle small" role="group" aria-label="Jump to a published percentile">
								{#each [[25, 'Low'], [50, 'Middle'], [75, 'High']] as [p, l]}
									<button class:on={parentP === p} onclick={() => (parentP = p)}>{l}</button>
								{/each}
							</div>
						</div>
						<span class="explain">The slider picks the <strong>parents</strong>. The colour shows where their <strong>children</strong> ended up.</span>
					</div>
					<div class="togglewrap">
						<span class="lbl">Show</span>
						<div class="toggle" role="group" aria-label="Counties or states">
							<button class:on={level === 'county'} onclick={() => setLevel('county')}>Counties</button>
							<button class:on={level === 'state'} onclick={() => setLevel('state')}>States</button>
						</div>
						<label class="check">
							<input type="checkbox" bind:checked={sameScale} />
							Same colour scale at every income level
						</label>
					</div>
				</div>
				{#if mapStats}
					<p class="spreadline">
						For children of parents at the {ordinal(parentP)} percentile, the middle 80% of counties run from the
						<strong>{pctile(mapStats.p10)}</strong> to the <strong>{pctile(mapStats.p90)}</strong> percentile:
						<span class="meter" aria-hidden="true"><i style="width:{((mapStats.p90 - mapStats.p10) / 0.16) * 100}%"></i></span>
						<strong>{Math.round((mapStats.p90 - mapStats.p10) * 100)} percentile points apart.</strong>
					</p>
				{/if}
				{#if notice}
					<div class="notice" role="status">
						Your county is now <strong>{nameOf(notice.next)}</strong>, because you clicked it on the map.
						<button class="ghost" onclick={undoPin}>Undo</button>
					</div>
				{/if}
				{#if zoomed}
					<div class="notice plain">
						<span>Showing the counties of <strong>{zoomed.name}</strong>.</span>
						<button class="ghost" onclick={() => (zoomState = null)}>← Back to all states</button>
					</div>
				{/if}
				<p class="readout">
					{#if mapHover}
						<strong>{mapHover.label}</strong>
						{#if mapHover.reliable}
							children of {pWord} parents ({ordinal(parentP)}) reached the {rank(kfrAt(mapHover, parentP))} on average
							({mapHover.isState ? `${mapHover.counties} counties, ` : ''}n = {fmtN(Math.round(mapHover.n))})
						{:else}
							no data: too few children to estimate
						{/if}
					{:else}
						{#if sameScale}
							Shared scale: blue means those children ended up above the national median adult (50th), red below, wherever the slider is.
						{:else}
							Colours are centred on the national average for the chosen parents, so they show geography within that group.
						{/if}
						{#if level === 'state' && !zoomed}
							Hover a state to read it; click to open its counties.
						{:else}
							Hover a county to read it; click to make it your county.
						{/if}
					{/if}
				</p>
				<CountyMap
					data={counties}
					accessor={mapGet}
					scale={sameScale ? SHARED_SCALE : null}
					home={story.home}
					{level}
					{states}
					zoom={zoomState}
					outline={ladderHover}
					legendTitle="Children of parents at the {ordinal(parentP)} percentile: average adult income rank"
					legendLow={sameScale ? '30th or below' : ''}
					legendHigh={sameScale ? '70th or above' : ''}
					onhover={(d) => (mapHover = d)}
					onselect={pinFromMap}
					onstate={(id) => (zoomState = id)}
				/>
				<p class="fine note">
					Alaska's large red areas are real, not an error: its rural census areas are each the size of a state,
					so one low estimate colours an enormous shape. Hatched counties have too few children to estimate.
				</p>
				{#if states.length}
					<div id="viz-states">
						<StateLadder {states} p={parentP} {homeState} active={activeState}
							onhover={(id) => (ladderHover = id)} onpick={openState} />
					</div>
				{/if}
			</div>
			{#if summary}
				<div class="prose">
					<div class="extremes">
						<div>
							<h3>Best {ranked.what}{ranked.where} for children of {pWord} parents</h3>
							<ol>
								{#each ranked.best as e (e.fips)}
									<li><span>{e.label}</span><b>{pctile(kfrAt(e, parentP))}</b></li>
								{/each}
							</ol>
						</div>
						<div>
							<h3>Worst {ranked.what}{ranked.where} for children of {pWord} parents</h3>
							<ol>
								{#each ranked.worst as e (e.fips)}
									<li><span>{e.label}</span><b>{pctile(kfrAt(e, parentP))}</b></li>
								{/each}
							</ol>
						</div>
					</div>
					<p class="fine">
						These lists follow the slider and the map above (parents at the {ordinal(parentP)} percentile).
						{#if ranked.what === 'large counties'}Large means at least 20,000 children in the sample.{/if}
						{#if ranked.what === 'states'}A state's figure is the average of its counties, weighted by the number of children in each.{/if}
						{#if mapStats}For comparison, the median county (half of all counties are higher, half lower) is the {pctile(mapStats.med)}.{/if}
					</p>
				</div>
			{/if}
		{/if}
	</section>

	<!-- ───────────── ACT 2: PREDICTORS ───────────── -->
	<section id="predictors" class="act">
		<div class="prose">
			<p class="actlabel">Part 2 · {partLabel('predictors')}</p>
			<h2>Some things about a county predict mobility. Some don't.</h2>
			<p>
				If place matters, which parts of it? We joined each county's outcomes to its
				characteristics from the Atlas and to its school test scores from the Stanford
				Education Data Archive. Each dot below is a county; the line is the best fit, and
				<em>r</em> says how tightly the dots follow it.
			</p>
			<p>
				The surprise is which predictors are strong. The share of children raised in
				single-parent households is the strongest single predictor in the data, stronger
				than the poverty rate. The share of adults with a bachelor's degree, the thing most
				people would guess first, barely predicts how a low-income child will do at all.
			</p>
		</div>

		{#if summary}
			<div class="stats prose">
				{#each summary.correlations.filter((c) => ['singlepar', 'poverty', 'score', 'collshare'].includes(c.key)) as c}
					<button class="tile" class:on={xVar === c.key} onclick={() => (xVar = c.key)}>
						<span class="num">{fmtR(c.r25)}</span>
						<span class="lab">{c.label}</span>
						<span class="sub">r with low-income children's adult income rank</span>
					</button>
				{/each}
			</div>
			<div class="prose">
				<p class="caveat">
					<strong>Read these as correlations, not causes.</strong> Each <em>r</em> runs from −1 to +1
					and says how tightly counties line up, across places, not for any one child. A
					<strong>negative</strong> <em>r</em> means counties with more of the characteristic had
					<em>lower</em> outcomes for low-income children; a positive one, higher. Test scores are
					in {SCORE_UNIT}, so +0.48 means the county's students score about half a standard
					deviation above average. The test takers were born a generation after the children
					whose incomes we measure.
				</p>
			</div>
		{/if}

		{#if counties.length}
			<div class="viz wide" id="viz-predictors">
				<div class="split">
					<div class="left">
						<div class="controls">
							<label>
								County characteristic
								<select bind:value={xVar}>
									{#each X_VARS as v}<option value={v.key}>{v.label}</option>{/each}
								</select>
							</label>
							{#if brushedSet}<button class="ghost" onclick={() => (brushed = null)}>Clear selection</button>{/if}
						</div>
						<Scatter
							data={counties}
							{xVar}
							yVar="kfr25"
							xLabel={isScore ? `${xMeta.label}, standard deviations from the national average` : xMeta.label}
							xFmt={xMeta.fmt}
							yLabel="Child's adult income rank, low-income parents"
							brushable={true}
							highlighted={brushedSet}
							home={story.home}
							selected={scatterHover?.fips ?? null}
							onbrush={(s) => (brushed = s)}
						/>
						<p class="readout">
							{#if brushStats}
								<strong>{brushStats.n} counties selected.</strong>
								Their low-income children reached the {rank(brushStats.kfr25)} on average, against the
								{rank(summary.national.kfr25.mean)} nationally. Average gap between rich and poor
								children: {Math.round(brushStats.gap * 100)} percentile points.
							{:else}
								Drag a box over the dots to outline those counties on the map.
							{/if}
						</p>
					</div>
					<div class="right">
						<CountyMap
							data={counties}
							colorBy={xVar}
							scheme="seq"
							fmt={xMeta.fmt}
							highlighted={brushedSet}
							home={story.home}
							legendTitle="{xMeta.label} (darker = more)"
							legendFmt={xMeta.fmt}
							onhover={(d) => (scatterHover = d)}
						/>
						<p class="readout">
							The map is coloured by <strong>{xMeta.label.toLowerCase()}</strong>, {xMeta.unit}.
							{#if corrFor}
								Its relationship with outcomes is <em>r</em> = {fmtR(corrFor.r25)} for low-income
								children ({rSentence(corrFor.r25)}) and {fmtR(corrFor.r75)} for high-income children.
								Every predictor matters more for the poor child than the rich one.
							{/if}
						</p>
					</div>
				</div>
				<div id="viz-county-vs-nation">
					<CountyVsNation data={counties} county={home?.reliable ? home : null}
						correlations={summary?.correlations ?? []} active={xVar} onpick={(k) => (xVar = k)} />
				</div>
			</div>
		{/if}
	</section>

	<!-- ───────────── CLIMAX: THE FAN ───────────── -->
	<section id="fan" class="act climax">
		<div class="prose">
			<p class="actlabel">Part 3 · {partLabel('fan')} · the main message</p>
			<h2>Place matters most for the children who have the least</h2>
			<p>
				This is the view we built the site around. Every reliable county is one line. It starts
				on the left at the average adult income rank of that county's children of low-income
				parents, passes through middle-income parents, and ends at high-income parents.
			</p>
			<p>
				Every line climbs, because richer parents mean higher-earning children in every county
				in America. That is true, and it is not the point. The point is the <em>width</em> of
				the bundle. On the left the lines fan wide: the middle 80% of counties span
				{spread25} percentile points for low-income children. On the right they converge: for
				high-income children the same band is {spread75} points. To see the width without the
				climb, switch the chart to <strong>distance from the median county</strong>. Hover any
				line to read its county, and click it to pin that county in place while you compare others.
			</p>
			<p>
				Being born well-off buys a good outcome nearly anywhere. Being born poor makes the
				county you land in one of the biggest facts of your life.
			</p>
		</div>

		{#if counties.length && summary}
			<div class="viz wide" id="viz-fan">
				<MobilityFan data={counties} {summary} home={story.home} onhover={(d) => (fanHover = d)} onstats={(s) => (fanStats = s)} />
			</div>
			{#if fanStats}
				<div class="prose tiles">
					<div class="tile static">
						<span class="num">{fanStats.lo} points</span>
						<span class="lab">spread between counties for low-income children</span>
						<span class="sub">{fanStats.region === 'All' ? 'all regions' : fanStats.region}, {fmtN(fanStats.n)} counties</span>
					</div>
					<div class="tile static">
						<span class="num">{fanStats.hi} points</span>
						<span class="lab">spread between counties for high-income children</span>
						<span class="sub">{fanStats.region === 'All' ? 'all regions' : fanStats.region}, {fmtN(fanStats.n)} counties</span>
					</div>
					<div class="tile static">
						<span class="num">{Math.round(fanStats.gap * 100)} points</span>
						<span class="lab">gap between rich and poor children raised in the same county</span>
						<span class="sub">{fanStats.region === 'All' ? 'all regions' : fanStats.region}, in the median county</span>
					</div>
				</div>
			{/if}
		{/if}
	</section>

	<!-- ───────────── TWO MAPS ───────────── -->
	<section id="twins" class="act">
		<div class="prose">
			<p class="actlabel">Part 4 · {partLabel('twins')}</p>
			<h2>Affluent children do well everywhere. Poor children depend on where they grow up.</h2>
			<p>
				Put the two ends of the fan back on the map, on one shared colour scale where blue means
				a child ended up above the national median adult and red means below. The right-hand map
				is blue coast to coast. The left-hand map is where the geography of opportunity lives.
			</p>
		</div>
		{#if counties.length}
			<div class="viz wide" id="viz-twin-maps">
				<TwinMaps data={counties} home={story.home} onhover={(d) => (twinHover = d)} />
				<p class="readout">
					{#if twinHover}
						<strong>{twinHover.label}</strong>
						{#if twinHover.reliable}
							low-income children reached the {rank(twinHover.kfr25)}, high-income children the {rank(twinHover.kfr75)}
						{:else}
							no data: too few children to estimate
						{/if}
					{:else}
						Hover either map; both show the same county.
					{/if}
				</p>
			</div>
		{/if}
		<div class="prose">
			<p class="sowhat">
				<strong>So what?</strong> If place-based policy wants the biggest return, it should be
				aimed at low-income children, because they are the ones whose outcomes place actually
				moves. And because two counties can give poor children the same outcome while giving
				rich children very different ones, mobility is better reported by parent income than as
				a single county average.
			</p>
		</div>
	</section>

	<!-- ───────────── CLOSER LOOKS ───────────── -->
	<section id="closer" class="act">
		<div class="prose">
			<p class="actlabel">Part 5 · {partLabel('closer')}</p>
			<h2>Where the pattern is strongest, when it opens up, and what an average hides</h2>
			<p>
				The argument is made above. These three views each press on one part of it: the kind of
				place, the age at which the gap appears, and the claim in the box above that a single
				county average is not enough.
			</p>
		</div>

		{#if counties.length && summary}
			<div class="viz wide look" id="viz-density">
				<div class="lookhead">
					<div>
						<p class="q">Do rural or urban counties give low-income children the better start?</p>
						<h3>The emptiest counties do best, and it matters more for poor children</h3>
					</div>
					<div class="togglewrap">
						<span class="lbl">Dots and map show children of</span>
						<div class="toggle" role="group" aria-label="Which children to show">
							<button class:on={densGroup === 'kfr25'} onclick={() => (densGroup = 'kfr25')}>Low-income parents</button>
							<button class:on={densGroup === 'kfr75'} onclick={() => (densGroup = 'kfr75')}>High-income parents</button>
						</div>
					</div>
				</div>
				<div class="split even">
					<DensityStrips data={counties} home={story.home} group={densGroup} onband={(s) => (densBand = s)} />
					<div>
						<CountyMap data={counties} colorBy={densGroup} scale={SHARED_SCALE} highlighted={densBand}
							home={story.home} legendTitle="Average adult income rank (shared scale)"
							legendLow="30th or below" legendHigh="70th or above" />
						<p class="readout">
							{densBand ? `${fmtN(densBand.size)} counties in this density band are lit; the rest are dimmed.` : 'Hover a band on the left to light up its counties here.'}
						</p>
					</div>
				</div>
			</div>

			<div class="viz wide look two" id="viz-age">
				<div class="looktext">
					<p class="q">Does the gap between rich and poor children grow after they start work?</p>
					<h3>At 24 they are {Math.round((summary.ages.kfr24_75 - summary.ages.kfr24_25) * 100)} percentile points apart. By their mid-thirties, {Math.round((summary.ages.adult_75 - summary.ages.adult_25) * 100)}.</h3>
					<p class="pointdef">
						<strong>How the gap is measured.</strong> A point is one percentile of the national
						income ranking. At 24, children of high-income parents average the
						{ordinal(age24.hi)} percentile and children of low-income parents the {ordinal(age24.lo)}:
						{age24.hi} − {age24.lo} = {age24.hi - age24.lo} points apart.
					</p>
					<p>
						The Atlas measured the same children's incomes at 24, 26 and 29, and again at 31 to 37.
						Children of low-income parents slide down the national ranking through their twenties
						while children of high-income parents hold or climb, as longer educations start to pay.
					</p>
					<p>
						So a snapshot at 24 understates how much parents' income matters, in every county.
						Press play, or drag the slider, to watch the wedge open.
					</p>
				</div>
				<AgePaths data={counties} {summary} home={story.home} />
			</div>

			<div class="viz wide look two" id="viz-twin-counties">
				<div class="looktext">
					<p class="q">Can two places treat poor children alike and rich children differently?</p>
					<h3>Same floor, different ceiling</h3>
					<p>
						Yes, and that is why we report mobility by parent income rather than as one number per
						county. Choose a county and the finder looks through the {fmtN(counties.filter((d) => d.reliable && (d.n ?? 0) >= LARGE_N).length)}
						large counties for its twin: the same outcome for children of low-income parents
						(within one percentile point), and the most different outcome for children of high-income parents.
					</p>
					<p>The shaded wedge is the part of the story a county average throws away.</p>
				</div>
				<TwinFinder data={counties} {summary} home={story.home} />
			</div>
		{/if}
	</section>

	<!-- ───────────── DATA ───────────── -->
	<section id="data" class="act">
		<div class="prose">
			<p class="actlabel">{partLabel('data')}</p>
			<h2>What these numbers can and cannot say</h2>
			<ul class="notes">
				<li>
					<strong>Sources.</strong> Opportunity Atlas county outcomes and neighborhood characteristics
					(US Census Bureau, Chetty, Friedman, Hendren, Jones and Porter), and the Stanford Education
					Data Archive 6.0 county test scores. Boundaries from the US Atlas TopoJSON. Joined on the
					five-digit county code into {summary ? fmtN(summary.counties_total) : '3,131'} counties.
					City and town names in the search come from a public city-to-county list and resolve to the county that contains them.
				</li>
				<li>
					<strong>"Income rank" means</strong> the child's household income at age 31 to 37, ranked against
					everyone born the same year and written as a percentile. The 50th percentile is the median adult.
				</li>
				<li>
					<strong>The parent-income slider</strong> runs from the 25th to the 75th percentile. The Atlas
					publishes each county at the 25th, 50th and 75th, and its estimates are a straight line in
					parents' rank: the published 50th-percentile figure is within half a point of the midpoint of
					the other two in every county. Positions in between read that same line. We do not go
					beyond the 25th or the 75th, where the Atlas itself is less certain.
				</li>
				<li>
					<strong>State figures</strong> are averages of a state's counties, weighted by the number of
					children each contributed, and leave out counties with too few children to estimate.
				</li>
				<li>
					<strong>Incomes at 24, 26 and 29</strong> are the Atlas's ranks among people of the same age in
					that year. They are for the same children as the main measure, taken earlier in their lives.
				</li>
				<li>
					<strong>Test scores</strong> are SEDA's cohort-standardised county means for grades 3 to 8,
					in standard deviations of the national student distribution; 0 is the national average student.
				</li>
				<li>
					<strong>Everything is a county average.</strong> There are no individual people in the data.
					A blue county does not promise any one child a good outcome; it says children like them,
					on average, did better there.
				</li>
				<li>
					<strong>The cohorts do not line up.</strong> Atlas children were born 1978 to 1983; the test
					scores are from students born around 1996 to 2010. The honest claim is that places where
					children score well now are also places where an earlier generation earned more.
				</li>
				<li>
					<strong>{summary ? fmtN(summary.counties_total - summary.counties_reliable) : '215'} counties are hatched as "no data"</strong>
					because fewer than {summary ? fmtN(summary.min_n) : '1,000'} children were in the sample and
					the Atlas estimates are too noisy below that.
				</li>
				<li>
					<strong>Alaska is not a bug.</strong> Its rural census areas are each the size of a state but
					hold only a few thousand children, so one estimate colours an enormous shape. The deep red is
					real: Bethel, Nome, the North Slope and the Northwest Arctic are among the lowest-mobility
					places in the country for children of low-income parents, who reached about the 25th percentile.
				</li>
				<li>
					<strong>Your location,</strong> if you choose to share it, is matched to a county inside your
					browser and is not sent or stored anywhere. Your chosen county is remembered on this device only.
				</li>
			</ul>
			<p class="team">
				Built by Atul Julka, Liam Clower and Lily Xu for CS 1710 at Harvard.
			</p>
		</div>
	</section>
</main>

<style>
	/* ---- layout ---- */
	main { padding-bottom: 80px; }
	.prose { max-width: 680px; margin: 0 auto; padding: 0 20px; }
	.wide { max-width: 1120px; margin: 28px auto; padding: 0 20px; }
	.act { padding: 56px 0 24px; scroll-margin-top: 48px; }
	.act + .act { border-top: 1px solid var(--rule); }

	/* ---- hero ---- */
	.hero { max-width: 760px; margin: 0 auto; padding: 72px 20px 48px; }
	.kicker { margin: 0 0 18px; font-size: 14px; color: var(--ink-2); }
	h1 { font: 500 clamp(36px, 6vw, 60px)/1.04 var(--serif); letter-spacing: -0.015em; margin: 0 0 24px; color: var(--ink); }
	h1 span { color: var(--blue); }
	.lede { font: 400 20px/1.5 var(--serif); color: var(--ink); max-width: 62ch; margin: 0 0 20px; }
	.define { font: 400 16px/1.5 var(--serif); color: var(--ink-2); max-width: 66ch; margin: 0 0 18px; padding-left: 16px; border-left: 3px solid var(--rule); }
	.define strong { color: var(--ink); font-weight: 600; }
	.definehead { margin: 0 0 8px; font: 600 13px var(--ui); color: var(--ink); }
	.define dl { margin: 0; display: grid; gap: 8px; }
	.define dt { font-weight: 600; color: var(--ink); }
	.define dd { margin: 0; }
	.definefoot { margin: 10px 0 0; }
	.hook { background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 22px 24px 24px; }
	.hook h2 { font: 500 26px/1.2 var(--serif); margin: 0 0 4px; }
	.hook > p { margin: 0 0 14px; color: var(--ink-2); font-size: 15px; }
	.loading { color: var(--ink-3); }
	.homecard { margin-top: 18px; display: grid; grid-template-columns: 1fr 340px; gap: 20px; align-items: start; border-top: 1px solid var(--rule); padding-top: 16px; }
	.sentence { font: 400 17px/1.5 var(--serif); margin: 0; }
	.curve { font-size: 13px; }
	@media (max-width: 700px) { .homecard { grid-template-columns: 1fr; } }

	/* ---- prose ---- */
	.actlabel { margin: 0 0 8px; font-size: 14px; color: var(--blue); font-weight: 500; }
	.act h2 { font: 500 clamp(26px, 3.6vw, 36px)/1.15 var(--serif); letter-spacing: -0.01em; margin: 0 0 18px; }
	.act .prose p { font: 400 18px/1.55 var(--serif); margin: 0 0 16px; color: var(--ink); }
	.act .prose p.fine { font: 400 13px/1.5 var(--ui); color: var(--ink-2); }
	.act .prose p.caveat { font: 400 14px/1.5 var(--ui); color: var(--ink-2); margin: 12px 0 0; padding: 10px 14px; background: #fff; border: 1px dashed var(--rule); border-radius: 6px; }
	.caveat strong { color: var(--ink); }
	.sowhat { border-left: 3px solid var(--blue); padding-left: 16px; }
	.team { margin-top: 28px !important; font-size: 16px !important; color: var(--ink-2) !important; }
	.notes { padding-left: 20px; margin: 0; }
	.notes li { font: 400 16px/1.5 var(--serif); margin-bottom: 10px; }

	/* ---- viz panels ---- */
	.viz { background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 18px; }
	.split { display: grid; grid-template-columns: 500px 1fr; gap: 20px; align-items: start; }
	.split.even { grid-template-columns: 1fr 1fr; }
	@media (max-width: 980px) { .split, .split.even { grid-template-columns: 1fr; } }
	.controls { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 12px; }
	.controls label { font-size: 13px; color: var(--ink-2); display: flex; flex-direction: column; gap: 4px; }
	.controls label.check { flex-direction: row; align-items: center; gap: 6px; cursor: pointer; }
	.togglewrap { display: grid; gap: 5px; }
	.togglewrap .lbl { font-size: 12px; color: var(--ink-2); }
	.togglewrap .lbl strong { color: var(--ink); font-size: 14px; }
	.explain { font-size: 12px; color: var(--ink-2); }
	.explain strong { color: var(--ink); font-weight: 600; }
	.slider { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 12px; color: var(--ink-2); }
	.slider input { width: min(300px, 46vw); accent-color: #1b2233; }
	select { font: inherit; font-size: 13px; padding: 5px 8px; border: 1px solid var(--rule); border-radius: 4px; background: #fff; }
	.toggle { display: flex; }
	.toggle button, .ghost { font: inherit; font-size: 13px; padding: 6px 12px; background: #fff; border: 1px solid var(--rule); cursor: pointer; color: var(--ink); }
	.toggle.small button { padding: 3px 9px; font-size: 12px; }
	.toggle button:first-child { border-radius: 6px 0 0 6px; }
	.toggle button:last-child { border-radius: 0 6px 6px 0; }
	.toggle button + button { border-left: 0; }
	.toggle button.on { background: var(--ink); color: #fff; border-color: var(--ink); }
	.ghost { border-radius: 6px; border-style: dashed; }
	.readout { margin: 8px 0 0; font-size: 13px; color: var(--ink-2); min-height: 1.5em; }
	.readout strong { color: var(--ink); }
	.spreadline { margin: 0 0 10px; font: 400 15px/1.5 var(--serif); color: var(--ink); }
	.meter { display: inline-block; vertical-align: middle; width: 90px; height: 8px; margin: 0 4px; background: #ecebe6; border-radius: 4px; overflow: hidden; }
	.meter i { display: block; height: 100%; background: var(--ink); border-radius: 4px; transition: width 120ms; }
	.fine.note { margin: 8px 0 0; font-size: 12px; color: var(--ink-2); }
	.notice { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 0 0 10px; padding: 8px 12px; font-size: 13px; color: var(--ink); background: #efeefc; border: 1px solid #cfc9f3; border-radius: 6px; }
	.notice.plain { background: #f5f5f3; border-color: var(--rule); }
	.notice .ghost { padding: 3px 10px; }

	/* ---- extremes lists ---- */
	.extremes { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 20px; }
	.extremes h3 { font: 500 15px var(--ui); margin: 0 0 8px; }
	.extremes ol { margin: 0; padding-left: 20px; font-size: 14px; }
	.extremes li { display: flex; justify-content: space-between; gap: 8px; padding: 3px 0; border-bottom: 1px solid var(--rule); }
	.extremes b { font-weight: 500; font-variant-numeric: tabular-nums; }
	@media (max-width: 600px) { .extremes { grid-template-columns: 1fr; } }

	/* ---- stat tiles ---- */
	.stats, .tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 8px; }
	.tiles { grid-template-columns: repeat(3, 1fr); margin-top: 18px; }
	.tile { display: grid; gap: 2px; text-align: left; background: #fff; border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; font: inherit; cursor: pointer; color: var(--ink); }
	.tile.static { cursor: default; }
	.tile.on { border-color: var(--ink); box-shadow: inset 0 0 0 1px var(--ink); }
	.tile .num { font-size: 28px; font-weight: 500; line-height: 1.1; }
	.tile .lab { font-size: 13px; font-weight: 500; }
	.tile .sub { font-size: 11px; color: var(--ink-3); }
	@media (max-width: 700px) { .stats, .tiles { grid-template-columns: 1fr 1fr; } }

	/* ---- closer looks ---- */
	.look .q { margin: 0 0 4px; font-size: 13px; color: var(--blue); font-weight: 500; }
	.look h3 { font: 500 22px/1.25 var(--serif); margin: 0 0 10px; color: var(--ink); }
	.lookhead { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 14px; margin-bottom: 12px; }
	.look.two { display: grid; grid-template-columns: 300px 1fr; gap: 28px; align-items: start; }
	.looktext p:not(.q) { font: 400 15.5px/1.55 var(--serif); margin: 0 0 12px; color: var(--ink); }
	.looktext p.pointdef { font: 400 13px/1.5 var(--ui); color: var(--ink-2); padding: 8px 12px; background: #f7f7f5; border: 1px dashed var(--rule); border-radius: 6px; }
	.pointdef strong { color: var(--ink); }
	@media (max-width: 860px) { .look.two { grid-template-columns: 1fr; } }

	.climax { background: linear-gradient(180deg, #fff 0%, var(--paper) 100%); }
</style>
