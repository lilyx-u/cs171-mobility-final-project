<script>
	// The sticky bar at the top of the page.
	//
	//   brand      the site's first sentence; clicking it returns to the top
	//   sections   one link per part of the story, named exactly as the part is
	//              named on the page, with the part being read underlined
	//   charts     a "Visualizations" menu that jumps straight to any one chart
	//
	// Every link scrolls smoothly to its target and then plays a short "arrival"
	// animation on it (the `nav-arrive` class, styled in +layout.svelte), so the
	// reader can see where they have landed. Readers who ask their system for
	// reduced motion get an instant jump and no animation.
	import { onMount } from 'svelte';
	import { replaceState } from '$app/navigation';

	let {
		brand = '',
		sections = [], // [{ id, label }]
		charts = [] // [{ id, label, group, fallback }]; `fallback` is the section to use while the chart is still loading
	} = $props();

	let open = $state(null); // which menu is open: 'sections' | 'charts' | null
	let active = $state(null); // id of the section currently being read
	let navEl = $state();

	// The charts menu is grouped under the part of the story each chart belongs to.
	let groups = $derived.by(() => {
		const out = [];
		for (const c of charts) {
			let g = out.find((x) => x.name === c.group);
			if (!g) out.push((g = { name: c.group, items: [] }));
			g.items.push(c);
		}
		return out;
	});

	const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	let pendingArrive = null;
	let arriveTimer;
	/** Play the arrival animation on `el` once the smooth scroll has finished. */
	function arrive(el) {
		// A whole section is too big to animate: animate its opening text instead.
		const target = el.matches('section') ? (el.querySelector('.prose') ?? el) : el.matches('header') ? (el.querySelector('h1') ?? el) : el;
		if (pendingArrive) window.removeEventListener('scrollend', pendingArrive);
		clearTimeout(arriveTimer);
		const run = () => {
			window.removeEventListener('scrollend', run);
			clearTimeout(arriveTimer);
			pendingArrive = null;
			target.classList.remove('nav-arrive');
			void target.offsetWidth; // restart the animation if it is still running
			target.classList.add('nav-arrive');
			target.addEventListener('animationend', () => target.classList.remove('nav-arrive'), { once: true });
		};
		pendingArrive = run;
		window.addEventListener('scrollend', run, { once: true });
		// Fallback for browsers without `scrollend`, and for a target already in view.
		arriveTimer = setTimeout(run, 1100);
	}

	function go(id, fallback) {
		open = null;
		const el = document.getElementById(id) ?? (fallback ? document.getElementById(fallback) : null);
		if (!el) return;
		const reduce = reducedMotion();
		el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
		// Keep the address bar in step, so a link to one chart can be copied and shared.
		try { replaceState(`#${el.id}`, {}); } catch {}
		if (!reduce) arrive(el);
	}

	/** Action for in-page links. The listener sits on the link itself so that it
	 *  runs before SvelteKit's own link handling, which would jump without animating. */
	function jump(node, target) {
		const onclick = (e) => {
			if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
			e.preventDefault();
			go(target.id, target.fallback);
		};
		node.addEventListener('click', onclick);
		return { destroy: () => node.removeEventListener('click', onclick) };
	}

	onMount(() => {
		// Scroll spy: the active section is the last one whose top has passed under the bar.
		let frame = 0;
		const spy = () => {
			frame = 0;
			let current = null;
			for (const s of sections) {
				const el = document.getElementById(s.id);
				if (el && el.getBoundingClientRect().top <= 150) current = s.id;
			}
			active = current;
		};
		const onscroll = () => { if (!frame) frame = requestAnimationFrame(spy); };
		const onkey = (e) => { if (e.key === 'Escape') open = null; };
		const ondown = (e) => { if (open && navEl && !navEl.contains(e.target)) open = null; };
		window.addEventListener('scroll', onscroll, { passive: true });
		window.addEventListener('resize', onscroll);
		window.addEventListener('keydown', onkey);
		window.addEventListener('pointerdown', ondown);
		spy();
		return () => {
			cancelAnimationFrame(frame);
			clearTimeout(arriveTimer);
			window.removeEventListener('scroll', onscroll);
			window.removeEventListener('resize', onscroll);
			window.removeEventListener('keydown', onkey);
			window.removeEventListener('pointerdown', ondown);
		};
	});
</script>

<nav class="top" aria-label="Site" bind:this={navEl}>
	<a class="brand" href="#start" use:jump={{ id: 'start' }}>{brand}</a>

	<div class="links">
		<!-- wide screens: every part of the story as its own link -->
		{#each sections as s (s.id)}
			<a class="sec" href="#{s.id}" class:on={active === s.id} aria-current={active === s.id ? 'true' : undefined}
				use:jump={s}>{s.label}</a>
		{/each}

		<!-- narrow screens: the same links folded into one menu -->
		<div class="menu compact">
			<button aria-haspopup="true" aria-expanded={open === 'sections'} class:open={open === 'sections'}
				onclick={() => (open = open === 'sections' ? null : 'sections')}>
				Sections <span class="caret" aria-hidden="true">▾</span>
			</button>
			{#if open === 'sections'}
				<div class="drop">
					<ul>
						{#each sections as s (s.id)}
							<li><a href="#{s.id}" class:on={active === s.id} use:jump={s}>{s.label}</a></li>
						{/each}
					</ul>
				</div>
			{/if}
		</div>

		<div class="menu">
			<button class="primary" aria-haspopup="true" aria-expanded={open === 'charts'} class:open={open === 'charts'}
				onclick={() => (open = open === 'charts' ? null : 'charts')}>
				Visualizations <span class="caret" aria-hidden="true">▾</span>
			</button>
			{#if open === 'charts'}
				<div class="drop wide">
					<p class="head">Jump to a chart</p>
					{#each groups as g (g.name)}
						<p class="group">{g.name}</p>
						<ul>
							{#each g.items as c (c.id)}
								<li><a href="#{c.id}" use:jump={c}>{c.label}</a></li>
							{/each}
						</ul>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</nav>

<style>
	.top {
		position: sticky; top: 0; z-index: 30;
		display: flex; justify-content: space-between; align-items: center; gap: 20px;
		padding: 9px 20px; background: rgba(245, 245, 243, 0.94); backdrop-filter: blur(6px);
		border-bottom: 1px solid var(--rule); font-size: 13px; font-family: var(--ui);
	}
	.brand {
		font: 500 16px var(--serif); color: var(--ink); text-decoration: none;
		white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;
	}
	.brand:hover { color: var(--blue); }
	.links { display: flex; align-items: center; gap: 4px; flex: none; }

	.sec {
		padding: 6px 9px; border-radius: 6px; color: var(--ink-2); text-decoration: none; white-space: nowrap;
		border-bottom: 2px solid transparent; transition: color 150ms, background 150ms, border-color 150ms;
	}
	.sec:hover { color: var(--ink); background: rgba(27, 34, 51, 0.06); }
	.sec.on { color: var(--ink); font-weight: 500; border-bottom-color: var(--blue); border-radius: 6px 6px 0 0; }

	.menu { position: relative; }
	.menu.compact { display: none; }
	button {
		font: inherit; padding: 6px 11px; border: 1px solid var(--rule); border-radius: 999px;
		background: #fff; color: var(--ink); cursor: pointer; white-space: nowrap;
	}
	button.primary { margin-left: 8px; background: var(--ink); border-color: var(--ink); color: #fff; }
	.caret { display: inline-block; transition: transform 160ms; }
	button.open .caret { transform: rotate(180deg); }

	.drop {
		position: absolute; right: 0; top: calc(100% + 10px); z-index: 40;
		min-width: 230px; padding: 8px; background: #fff; border: 1px solid var(--rule); border-radius: 10px;
		box-shadow: 0 12px 32px rgba(27, 34, 51, 0.16);
		max-height: calc(100vh - 80px); overflow-y: auto;
		transform-origin: top right; animation: drop-in 150ms ease-out;
	}
	.drop.wide { min-width: 290px; }
	@keyframes drop-in {
		from { opacity: 0; transform: translateY(-4px); }
		to { opacity: 1; transform: none; }
	}
	.drop ul { list-style: none; margin: 0; padding: 0; }
	.drop a { display: block; padding: 7px 10px; border-radius: 6px; color: var(--ink); text-decoration: none; font-size: 14px; }
	.drop a:hover, .drop a:focus-visible { background: #efeefc; }
	.drop a.on { font-weight: 600; }
	.head { margin: 2px 10px 4px; font-size: 12px; color: var(--ink-3); }
	.group { margin: 8px 10px 2px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--blue); }

	/* Below this width the section links no longer fit beside the title. */
	@media (max-width: 1320px) {
		.sec { display: none; }
		.menu.compact { display: block; }
		button.primary { margin-left: 4px; }
	}
	@media (max-width: 560px) {
		.top { padding: 8px 12px; gap: 10px; }
		.brand { font-size: 14px; }
		button { padding: 5px 9px; }
	}
</style>
