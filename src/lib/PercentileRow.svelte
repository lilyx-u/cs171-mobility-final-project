<script>
	// What a percentile is, drawn rather than defined: 100 people born the same
	// year, lined up from the lowest household income to the highest. One marker
	// shows where the parents stood, the other where their child ended up.
	import { ordinal, VIOLET, INK } from '#lib/colors.js';

	// `lo` / `hi`: the child's adult rank (0 to 1) for parents at the 25th / 75th.
	// `place`: whose numbers these are ("the median U.S. county", "Cook County, IL").
	// `mine`: true when the place is the reader's own county (drawn in purple).
	let { lo = 0.42, hi = 0.59, place = 'the median U.S. county', mine = false } = $props();

	let group = $state(25);
	let hovered = $state(null);

	const W = 720, H = 116, step = W / 100, top = 40;
	const xOf = (r) => (r - 0.5) * step;

	let child = $derived(Math.max(1, Math.min(100, Math.round((group === 25 ? lo : hi) * 100))));
	let delta = $derived(child - group);
	let accent = $derived(mine ? VIOLET : INK);
</script>

<figure class="prow">
	<div class="pick" role="group" aria-label="Which parents to show">
		<span>Show a child whose parents were</span>
		<button class:on={group === 25} onclick={() => (group = 25)}>low-income (25th)</button>
		<button class:on={group === 75} onclick={() => (group = 75)}>high-income (75th)</button>
	</div>

	<svg viewBox="0 0 {W} {H}" role="img"
		aria-label="One hundred people in a row from lowest to highest income. Parents stand at position {group}; their child, as an adult, at position {child}.">
		<!-- child's label, above -->
		<g class="mark" style="transform: translateX({xOf(child)}px)">
			<text class="lab strong" y="12" fill={accent}
				text-anchor={child > 78 ? 'end' : child < 22 ? 'start' : 'middle'}>
				their child, as an adult: {ordinal(child)}
			</text>
			<line y1="18" y2={top - 6} stroke={accent} stroke-width="1.5" />
		</g>

		{#each Array(100) as _, i}
			{@const r = i + 1}
			<g transform="translate({xOf(r)},{top})" class="person"
				class:parent={r === group} class:child={r === child} class:hov={r === hovered}
				style={r === child ? `color:${accent}` : ''}>
				<circle cy="4" r="2.9" />
				<path d="M-3.1,28 L-3.1,13 Q0,7.6 3.1,13 L3.1,28 Z" />
			</g>
		{/each}

		<!-- the move from the parents' place to the child's -->
		{#if delta !== 0}
			<path class="arc" stroke={accent}
				d="M{xOf(group)},{top - 3} Q{(xOf(group) + xOf(child)) / 2},{top - 16 - Math.min(14, Math.abs(delta))} {xOf(child)},{top - 3}" />
		{/if}

		<!-- parents' label, below -->
		<g class="mark" style="transform: translateX({xOf(group)}px)">
			<line y1={top + 32} y2={top + 42} stroke="#555b6b" stroke-width="1.5" />
			<text class="lab" y={top + 54} text-anchor="middle">parents: {ordinal(group)}</text>
		</g>
		<text class="end" x="0" y={H - 2}>1st &middot; lowest income</text>
		<text class="end" x={W} y={H - 2} text-anchor="end">highest income &middot; 100th</text>

		<!-- one hit column per person -->
		{#each Array(100) as _, i}
			<rect x={i * step} y={top - 4} width={step} height="38" fill="transparent"
				onmouseenter={() => (hovered = i + 1)} onmouseleave={() => (hovered = null)} role="presentation" />
		{/each}
	</svg>

	<figcaption>
		{#if hovered}
			<strong>The {ordinal(hovered)} percentile:</strong> this person's household earns more than
			{hovered - 1} of the 100 people born the same year, and less than {100 - hovered}.
		{:else}
			<strong>Each figure is one percentile.</strong> In {place}, a child whose parents stood
			{ordinal(group)} in this line ended up {ordinal(child)} on average:
			{delta === 0 ? 'the same place' : `${Math.abs(delta)} place${Math.abs(delta) === 1 ? '' : 's'} ${delta > 0 ? 'higher' : 'lower'}`}
			than their parents. Hover a figure to read its position.
		{/if}
	</figcaption>
</figure>

<style>
	.prow { margin: 0 0 30px; font-family: var(--ui, system-ui); }
	.pick { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 13px; color: var(--ink-2); margin-bottom: 6px; }
	button { font: inherit; padding: 4px 10px; border: 1px solid var(--rule); background: #fff; border-radius: 999px; cursor: pointer; color: var(--ink); }
	button.on { background: var(--ink); color: #fff; border-color: var(--ink); }
	svg { width: 100%; height: auto; display: block; overflow: visible; }
	.person { color: #c4c4be; fill: currentColor; }
	.person.parent { color: #555b6b; }
	.person.hov { color: #2a78d6; }
	.mark { transition: transform 450ms cubic-bezier(0.3, 0, 0.2, 1); }
	.arc { fill: none; stroke-width: 1.2; stroke-dasharray: 3 3; opacity: 0.7; }
	.lab { font-size: 12px; fill: var(--ink-2); }
	.lab.strong { font-weight: 600; }
	.end { font-size: 10px; fill: var(--ink-3); }
	figcaption { font-size: 13px; line-height: 1.5; color: var(--ink-2); margin-top: 6px; min-height: 3em; }
	figcaption strong { color: var(--ink); }
</style>
