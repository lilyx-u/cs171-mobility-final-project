<script>
	// Typeahead over all 3,131 counties and ~30,000 cities and towns. A city
	// match resolves to the county that contains it, so a reader who knows
	// "Somerville" but not "Middlesex County" still finds their place.
	import { countyAt } from '#lib/data.js';

	let { data, places = [], value = null, onpick = () => {} } = $props();

	let q = $state('');
	let open = $state(false);
	let active = $state(0);
	let input = $state();

	let current = $derived(value ? data.find((d) => d.fips === value) : null);
	let byFips = $derived(new Map(data.map((d) => [d.fips, d])));

	let matches = $derived.by(() => {
		const s = q.trim().toLowerCase();
		if (s.length < 2) return [];
		// Bigger counties first within each tier: they are the ones people mean.
		const big = (a, b) => (b.n ?? 0) - (a.n ?? 0);

		const starts = [], contains = [];
		for (const d of data) {
			const l = d.label.toLowerCase();
			if (l.startsWith(s)) starts.push(d);
			else if (l.includes(s)) contains.push(d);
		}
		const countyHits = [...starts.sort(big), ...contains.sort(big)].map((d) => ({ county: d, via: null }));

		// Cities and towns: prefix match on "Name, ST", resolved to their county.
		// Skip a place whose county already matched by name, and skip duplicates.
		const seen = new Set(countyHits.map((h) => h.county.fips));
		const placeHits = [];
		if (s.length >= 3) {
			for (const p of places) {
				if (!p.label.toLowerCase().startsWith(s)) continue;
				const c = byFips.get(p.fips);
				if (!c || seen.has(c.fips)) continue;
				seen.add(c.fips);
				placeHits.push({ county: c, via: p });
			}
			placeHits.sort((a, b) => big(a.county, b.county));
		}
		return [...countyHits.slice(0, 5), ...placeHits].slice(0, 8);
	});

	function pick(h) {
		onpick(h.county.fips);
		q = '';
		open = false;
	}
	// "Use my location": the browser asks permission, then the county is found
	// by testing the coordinates against the county boundaries already on the
	// page. The coordinates never leave the browser.
	let locating = $state(false);
	let locError = $state('');
	function locate() {
		locError = '';
		if (!('geolocation' in navigator)) { locError = 'This browser cannot share a location. Type a county or town instead.'; return; }
		locating = true;
		navigator.geolocation.getCurrentPosition(
			(pos) => {
				locating = false;
				const f = countyAt(pos.coords.longitude, pos.coords.latitude);
				if (f && byFips.has(f)) onpick(f);
				else locError = 'Your location is not inside a US county we have data for. Type a county or town instead.';
			},
			() => { locating = false; locError = 'Location was not shared. Type a county or town instead.'; },
			{ timeout: 10000, maximumAge: 600000 }
		);
	}
	function key(e) {
		if (!open || !matches.length) return;
		if (e.key === 'ArrowDown') { active = (active + 1) % matches.length; e.preventDefault(); }
		else if (e.key === 'ArrowUp') { active = (active - 1 + matches.length) % matches.length; e.preventDefault(); }
		else if (e.key === 'Enter') { pick(matches[active]); e.preventDefault(); }
		else if (e.key === 'Escape') { open = false; }
	}
</script>

<div class="search">
	<label>
		<span class="sr">Search for the county, city or town you grew up in</span>
		<input
			bind:this={input}
			bind:value={q}
			type="search"
			placeholder={current ? `Change from ${current.label}` : 'Type a county, city or town, e.g. Somerville, MA'}
			autocomplete="off"
			onfocus={() => (open = true)}
			oninput={() => { open = true; active = 0; }}
			onkeydown={key}
			onblur={() => setTimeout(() => (open = false), 120)}
		/>
	</label>
	{#if open && matches.length}
		<ul role="listbox">
			{#each matches as h, i}
				<li role="option" aria-selected={i === active} class:active={i === active}
					onmousedown={() => pick(h)} onmouseenter={() => (active = i)}>
					{#if h.via}
						<span>{h.via.label} <small class="in">is in {h.county.label}</small></span>
					{:else}
						<span>{h.county.label}</span>
					{/if}
					<small>{h.county.reliable ? '' : 'too small to estimate'}</small>
				</li>
			{/each}
		</ul>
	{:else if open && q.trim().length >= 2}
		<ul><li class="none">No county, city or town matches "{q}". Check the spelling, or add the state, e.g. "Austin, TX".</li></ul>
	{/if}
	<button class="clear" onclick={locate} disabled={locating} title="Finds your county in the browser; your location is not sent anywhere">
		{locating ? 'Locating…' : 'Use my location'}
	</button>
	{#if current}
		<button class="clear" onclick={() => onpick(null)}>Clear</button>
	{/if}
</div>
{#if locError}<p class="locerr" role="status">{locError}</p>{/if}

<style>
	.search { position: relative; display: flex; gap: 8px; align-items: stretch; font-family: var(--ui, system-ui); }
	label { flex: 1; }
	.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
	input {
		width: 100%;
		box-sizing: border-box;
		font: 17px var(--ui, system-ui);
		padding: 12px 14px;
		border: 1.5px solid var(--ink, #1b2233);
		border-radius: 6px;
		background: #fff;
		color: var(--ink);
	}
	input:focus { outline: 3px solid rgba(98, 80, 214, 0.35); outline-offset: 1px; }
	ul {
		position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 20;
		list-style: none; margin: 0; padding: 4px; background: #fff;
		border: 1px solid var(--rule, #e3e3df); border-radius: 6px;
		box-shadow: 0 8px 24px rgba(27, 34, 51, 0.12);
	}
	li { display: flex; justify-content: space-between; gap: 8px; padding: 8px 10px; border-radius: 4px; cursor: pointer; font-size: 15px; }
	li.active { background: #efeefc; }
	li small { color: var(--ink-3, #8a8f9c); }
	li small.in { color: var(--ink-2, #555b6b); font-size: 13px; }
	li.none { color: var(--ink-2); cursor: default; font-size: 14px; }
	.clear { font: 14px var(--ui); background: none; border: 1px solid var(--rule); border-radius: 6px; padding: 0 12px; cursor: pointer; color: var(--ink-2); white-space: nowrap; }
	.clear:disabled { opacity: 0.6; cursor: default; }
	.locerr { margin: 8px 0 0; font: 13px var(--ui, system-ui); color: #b8341f; }
	@media (max-width: 560px) { .search { flex-wrap: wrap; } label { flex-basis: 100%; } .clear { padding: 8px 12px; } }
</style>
