<script>
	// The mobility fan: every reliable county drawn as one line through three
	// axes (parents at the 25th, 50th and 75th percentile). Where the lines are
	// spread out, place matters; where they bunch, it does not. The whole
	// argument of the site is visible in the shape of this one figure.
	//
	// Two readings of the same lines:
	//   ranks     the raw outcome. Every line climbs, because parents' income
	//             matters everywhere; testers read this as the whole message.
	//   levelled  each axis re-centred on its median county, which removes the
	//             climb and leaves only what place adds or takes away. The
	//             narrowing from left to right is then impossible to miss.
	//
	// Three lines can be marked on top of the bundle, each in its own colour:
	//   yours    the reader's county, chosen at the top of the page (purple)
	//   pinned   a county the reader clicked here, kept in place to compare (amber)
	//   hovered  the county under the cursor (dark)
	import * as d3 from 'd3';
	import { SHARED_SCALE, VIOLET, INK, COMPARE, pctile } from '#lib/colors.js';
	import { PERCENTILES } from '#lib/data.js';

	let { data, summary, home = null, onhover = () => {}, onstats = () => {} } = $props();

	const width = 960;
	const height = 580;
	const margin = { top: 56, right: 190, bottom: 84, left: 190 };
	const iw = width - margin.left - margin.right;
	const ih = height - margin.top - margin.bottom;

	const keys = PERCENTILES.map((p) => p.key);
	const x = d3.scalePoint().domain(keys).range([0, iw]);

	const REGIONS = ['All', 'Northeast', 'Midwest', 'South', 'West'];
	let region = $state('All');
	let levelled = $state(false);
	let pinned = $state(null); // fips clicked on the fan
	let near = $state(null); // county under the cursor

	let rows = $derived(data.filter((d) => d.reliable && keys.every((k) => d[k] != null)));
	let byFips = $derived(new Map(rows.map((d) => [d.fips, d])));

	// The counties the filter keeps. Every statistic on this chart is computed
	// from this set, so choosing "South" redraws the brackets and the numbers,
	// not just the lines.
	let shown = $derived(region === 'All' ? rows : rows.filter((d) => d.region === region));
	let visible = $derived(region === 'All' ? null : new Set(shown.map((d) => d.fips)));

	// Spread brackets: the band 80% of the shown counties fall in, at each axis.
	let bands = $derived(
		keys.map((k) => {
			const v = shown.map((d) => d[k]).sort(d3.ascending);
			const p10 = d3.quantile(v, 0.1), p90 = d3.quantile(v, 0.9);
			return { k, p10, p90, median: d3.quantile(v, 0.5), spread: p90 - p10 };
		})
	);
	let med = $derived(Object.fromEntries(bands.map((b) => [b.k, b.median])));
	let lo = $derived(Math.round(bands[0].spread * 100));
	let hi = $derived(Math.round(bands[2].spread * 100));
	let gapMedian = $derived(d3.median(shown, (d) => d.gap));
	$effect(() => onstats({ region, n: shown.length, lo, hi, gap: gapMedian }));

	// What gets plotted: the rank itself, or its distance from the median county.
	let off = $derived(levelled ? med : { kfr25: 0, kfr50: 0, kfr75: 0 });
	let y = $derived(d3.scaleLinear().domain(levelled ? [-0.22, 0.22] : [0.25, 0.75]).range([ih, 0]).clamp(true));
	let ticks = $derived(levelled ? [-0.2, -0.1, 0, 0.1, 0.2] : [0.3, 0.4, 0.5, 0.6, 0.7]);
	const signed = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(Math.round(v * 100))}`;
	let tickFmt = $derived(levelled ? (t) => (t === 0 ? 'median' : signed(t)) : pctile);
	let line = $derived(d3.line().x((d) => x(d.k)).y((d) => y(d.v)));
	const pts = (d, o) => keys.map((k) => ({ k, v: d[k] - o[k], raw: d[k] }));
	let paths = $derived(rows.map((d) => ({ d, p: line(pts(d, off)), c: SHARED_SCALE(d.kfr25) })));

	// The reader's county may be too small to draw; `homeAny` lets the chart say so.
	let homeAny = $derived(home ? data.find((d) => d.fips === home) : null);
	let homeD = $derived(home ? byFips.get(home) : null);
	// A pin on the reader's own county would add nothing: it is always marked.
	let pin = $derived(pinned && pinned !== home ? byFips.get(pinned) : null);
	let hover = $derived(near && near.fips !== homeD?.fips && near.fips !== pin?.fips ? near : null);

	// The marked lines, back to front. A pinned line stays drawn while the cursor
	// moves on to other counties, which is what makes it possible to compare two.
	let marks = $derived.by(() => {
		const list = [];
		if (homeD) list.push({ d: homeD, kind: 'home', color: VIOLET, tag: 'your county' });
		if (pin) list.push({ d: pin, kind: 'pin', color: COMPARE, tag: 'pinned · click to unpin' });
		if (hover) list.push({ d: hover, kind: 'hover', color: INK, tag: 'click to pin' });
		for (const m of list) {
			m.pp = pts(m.d, off);
			// With the cursor on the chart, only the line under it carries its numbers;
			// otherwise every marked line does.
			m.vals = near ? near.fips === m.d.fips : true;
			m.ly = y(m.pp[2].v);
			// A pinned county just below the reader's own writes its numbers under its
			// dots instead of over them, so the two sets of numbers do not collide.
			for (const [i, q] of m.pp.entries()) {
				const gap = m.kind === 'pin' && homeD ? y(q.v) - y(homeD[q.k] - off[q.k]) : null;
				q.under = gap != null && gap >= 0 && gap < 24;
			}
		}
		// Name labels share the right-hand margin: push apart any that would collide.
		const stack = [...list].sort((a, b) => a.ly - b.ly);
		for (let i = 1; i < stack.length; i++) {
			if (stack[i].ly - stack[i - 1].ly < 28) stack[i].ly = stack[i - 1].ly + 28;
		}
		return list;
	});

	// Nearest line to the cursor: interpolate each county's y at the cursor x and
	// take the smallest vertical distance. 3,000 lines is cheap enough per move.
	function onmove(e) {
		const svg = e.currentTarget.ownerSVGElement;
		const pt = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM().inverse());
		const mx = Math.max(0, Math.min(iw, pt.x - margin.left));
		const my = pt.y - margin.top;
		const seg = mx < x('kfr50') ? ['kfr25', 'kfr50'] : ['kfr50', 'kfr75'];
		const t = (mx - x(seg[0])) / (x(seg[1]) - x(seg[0]));
		let best = null, bd = Infinity;
		for (const d of shown) {
			const a = d[seg[0]] - off[seg[0]], b = d[seg[1]] - off[seg[1]];
			const dy = Math.abs(y(a + t * (b - a)) - my);
			if (dy < bd) { bd = dy; best = d; }
		}
		near = bd < 14 ? best : null;
		onhover(near);
	}
	function onleave() { near = null; onhover(null); }
	/** Click a line to pin it; click the pinned line again to let it go. */
	function onclick(e) {
		onmove(e); // a tap or a click without a preceding move still finds its line
		if (!near || near.fips === home) return;
		pinned = pinned === near.fips ? null : near.fips;
	}

	const axisTitle = { kfr25: 'Low-income parents', kfr50: 'Middle-income parents', kfr75: 'High-income parents' };
	const axisSub = { kfr25: '25th percentile', kfr50: '50th percentile', kfr75: '75th percentile' };
	const where = $derived(region === 'All' ? 'the country' : `the ${region}`);
	const read = (d) => `children of low-income parents reached the ${pctile(d.kfr25)} percentile, middle-income the ${pctile(d.kfr50)}, high-income the ${pctile(d.kfr75)}`;
</script>

<div class="fan">
	<div class="controls">
		<div class="grp" role="group" aria-label="Filter by region">
			<span class="lbl">Show counties in</span>
			{#each REGIONS as r}
				<button class:on={region === r} onclick={() => (region = r)}>{r}</button>
			{/each}
		</div>
		<div class="grp" role="group" aria-label="How to draw the lines">
			<span class="lbl">Draw each county as</span>
			<button class:on={!levelled} onclick={() => (levelled = false)}>its income rank</button>
			<button class:on={levelled} onclick={() => (levelled = true)}>its distance from the median county</button>
		</div>
	</div>

	<p class="stats" aria-live="polite">
		<strong>{d3.format(',')(shown.length)} counties in {where}.</strong>
		Across the middle 80% of them, the county a child grows up in moves
		<b class="lo">low-income children by {lo} percentile points</b> but
		<b class="hi">high-income children by only {hi}</b>.
	</p>

	<!-- The marked counties, in words, so a pin is never only a coloured line. -->
	<div class="pinbar" aria-live="polite">
		{#if homeD}
			<p><i style="background:{VIOLET}"></i><span><b>{homeD.label} (yours):</b> {read(homeD)}.</span></p>
		{:else if homeAny}
			<p class="muted"><i style="background:{VIOLET}"></i><span>{homeAny.label} (yours) had too few children in the study to draw as a line.</span></p>
		{/if}
		{#if pin}
			<p>
				<i style="background:{COMPARE}"></i>
				<span><b>{pin.label} (pinned):</b> {read(pin)}.</span>
				<button class="mini" onclick={() => (pinned = null)}>Unpin</button>
			</p>
		{:else}
			<p class="muted"><i class="hollow"></i><span>Hover any line to read its county. <b>Click a line to pin it</b>, then hover others to compare against it.</span></p>
		{/if}
	</div>

	<svg viewBox="0 0 {width} {height}" role="img" aria-label="Every county's child outcomes at three parental income levels">
		<g transform="translate({margin.left},{margin.top})">
			<!-- y grid -->
			{#each ticks as t}
				<line class="grid" class:zero={levelled && t === 0} x1="0" x2={iw} y1={y(t)} y2={y(t)} />
				<text class="tick" x="-10" y={y(t)} dy="0.32em" text-anchor="end">{tickFmt(t)}</text>
			{/each}
			<text class="ylab" transform="translate(-60,{ih / 2}) rotate(-90)" text-anchor="middle">
				{levelled
					? 'Percentile points above or below the median county, same parents'
					: "Child's income rank as an adult (national percentile)"}
			</text>

			<!-- all county lines -->
			<g class="lines">
				{#each paths as p (p.d.fips)}
					<path
						d={p.p}
						stroke={p.c}
						class:faded={visible && !visible.has(p.d.fips)}
						class:ghost={near && near.fips !== p.d.fips}
					/>
				{/each}
			</g>

			<!-- axes + spread brackets -->
			{#each bands as b, i}
				{@const top = y(b.p90 - off[b.k])}
				{@const bot = y(b.p10 - off[b.k])}
				<line class="axis" x1={x(b.k)} x2={x(b.k)} y1="0" y2={ih} />
				<rect class="band" class:ends={i !== 1} x={x(b.k) - 5} width="10" y={top} height={bot - top} rx="3" />
				<line class="median" x1={x(b.k) - 9} x2={x(b.k) + 9} y1={y(b.median - off[b.k])} y2={y(b.median - off[b.k])} />
				<text class="axt" x={x(b.k)} y="-34" text-anchor="middle">{axisTitle[b.k]}</text>
				<text class="axs" x={x(b.k)} y="-20" text-anchor="middle">{axisSub[b.k]}</text>
				<!-- bracket caps and the spread label, read as one number per axis -->
				<line class="cap" x1={x(b.k) - 14} x2={x(b.k) + 14} y1={top} y2={top} />
				<line class="cap" x1={x(b.k) - 14} x2={x(b.k) + 14} y1={bot} y2={bot} />
				<text class="spread" class:big={i !== 1} x={x(b.k)} y={ih + 22} text-anchor="middle">{Math.round(b.spread * 100)} points</text>
				<text class="spreadsub" x={x(b.k)} y={ih + 36} text-anchor="middle">spanned by the middle 80% of counties</text>
			{/each}

			<!-- the comparison the chart exists to make -->
			<g class="compare" transform="translate(0,{ih + 58})">
				<line x1={x('kfr25') + 36} x2={x('kfr75') - 36} y1="0" y2="0" />
				<line x1={x('kfr25') + 36} x2={x('kfr25') + 36} y1="-5" y2="5" />
				<line x1={x('kfr75') - 36} x2={x('kfr75') - 36} y1="-5" y2="5" />
				<text x={(x('kfr25') + x('kfr75')) / 2} y="-6" text-anchor="middle">
					{lo} vs {hi} points: place moves a poor child's outcome {lo > hi ? `${lo - hi} point${lo - hi === 1 ? '' : 's'} more` : 'no more'} than a rich child's
				</text>
			</g>

			<!-- marked counties: yours, pinned, hovered -->
			{#each marks as m (m.kind)}
				<g class="mark {m.kind}">
					<path class="halo" d={line(m.pp)} />
					<path class="markline" d={line(m.pp)} stroke={m.color} />
					{#each m.pp as q}
						<circle cx={x(q.k)} cy={y(q.v)} r="4.5" fill={m.color} stroke="#fff" stroke-width="1.5" />
						{#if m.vals}
							<text class="val" x={x(q.k)} y={y(q.v) + (q.under ? 18 : -9)} text-anchor="middle" fill={m.color}>
								{levelled ? `${signed(q.v)} (${pctile(q.raw)})` : pctile(q.raw)}
							</text>
						{/if}
					{/each}
					<text class="name" x={x('kfr75') + 12} y={m.ly} dy="0.1em" fill={m.color}>{m.d.county}, {m.d.state}</text>
					<text class="nametag" x={x('kfr75') + 12} y={m.ly + 13} dy="0.1em" fill={m.color}>{m.tag}</text>
				</g>
			{/each}

			<!-- hit layer -->
			<rect class="hit" class:onaline={near && near.fips !== home} x="0" y="0" width={iw} height={ih}
				onmousemove={onmove} onmouseleave={onleave} onclick={onclick} role="presentation" />
		</g>
	</svg>

	<p class="caption">
		{#if levelled}
			Each line is one county, now measured against the median county (the middle one of the
			counties shown) for children with the same parents, so the climb that every county shares is
			gone. What is left is what place adds or takes away: a wide spray on the left, a tighter
			bundle on the right.
		{:else}
			Each line is one county. Every line climbs because parents' income matters everywhere; that
			part is not the news. The news is the width: the dark brackets mark where the middle 80% of
			the shown counties fall at each income level, and the tick inside each is the median county.
		{/if}
		Colour follows the left end: blue counties lift low-income children above the national median, red ones do not.
		A point is one percentile of the national income ranking.
	</p>
</div>

<style>
	.fan { font-family: var(--ui, system-ui); }
	svg { width: 100%; height: auto; display: block; overflow: visible; }
	.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 22px; margin-bottom: 10px; font-size: 13px; }
	.grp { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
	.lbl { color: var(--ink-2); margin-right: 4px; }
	button { font: inherit; font-size: 13px; padding: 5px 11px; border: 1px solid var(--rule); background: #fff; border-radius: 999px; cursor: pointer; color: var(--ink); }
	button.on { background: var(--ink); color: #fff; border-color: var(--ink); }
	button.mini { padding: 2px 9px; font-size: 12px; border-style: dashed; flex: none; }
	.stats { margin: 0 0 8px; font: 400 15px/1.45 var(--serif, Georgia, serif); color: var(--ink); }
	.stats b { font-weight: 600; }
	.stats .lo { color: #b8341f; }
	.stats .hi { color: #1f62b8; }
	.pinbar { display: grid; gap: 4px; margin: 0 0 6px; padding: 8px 12px; background: #f7f7f5; border: 1px solid var(--rule); border-radius: 6px; min-height: 2.9em; align-content: center; }
	.pinbar p { margin: 0; display: flex; align-items: baseline; gap: 8px; font-size: 13px; line-height: 1.45; color: var(--ink); }
	.pinbar p.muted { color: var(--ink-2); }
	.pinbar b { font-weight: 600; }
	.pinbar i { flex: none; width: 10px; height: 10px; border-radius: 50%; transform: translateY(1px); }
	.pinbar i.hollow { border: 1.5px dashed var(--ink-3); box-sizing: border-box; }
	.lines path { fill: none; stroke-width: 1; opacity: 0.2; transition: opacity 120ms; }
	.lines path.faded { opacity: 0.015; }
	.lines path.ghost { opacity: 0.05; }
	.grid { stroke: #ebeae6; }
	.grid.zero { stroke: #8a8f9c; stroke-dasharray: 4 3; }
	.tick { font-size: 11px; fill: #75746f; }
	.ylab { font-size: 12px; fill: var(--ink-2); }
	.axis { stroke: #c9c9c4; stroke-width: 1; }
	.band { fill: #1b2233; opacity: 0.14; }
	.band.ends { opacity: 0.3; }
	.cap { stroke: #1b2233; stroke-width: 1.5; }
	.median { stroke: #1b2233; stroke-width: 2; }
	.axt { font-size: 13px; font-weight: 600; fill: var(--ink); }
	.axs { font-size: 11px; fill: var(--ink-2); }
	.spread { font-size: 13px; font-weight: 600; fill: var(--ink); }
	.spread.big { font-size: 16px; }
	.spreadsub { font-size: 10px; fill: var(--ink-2); }
	.compare line { stroke: var(--ink); stroke-width: 1; }
	.compare text { font-size: 12px; font-weight: 500; fill: var(--ink); }
	.mark { pointer-events: none; }
	.halo { fill: none; stroke: #fff; stroke-width: 6; }
	.markline { fill: none; stroke-width: 2.5; }
	.mark.pin .markline { stroke-width: 3; }
	.name { font-size: 12px; font-weight: 600; }
	.nametag { font-size: 10px; opacity: 0.85; }
	.val { font-size: 11px; font-weight: 600; paint-order: stroke; stroke: #fff; stroke-width: 3px; }
	.hit { fill: transparent; cursor: crosshair; }
	.hit.onaline { cursor: pointer; }
	.caption { font-size: 13px; color: var(--ink-2); margin: 8px 0 0; max-width: 78ch; }
</style>
