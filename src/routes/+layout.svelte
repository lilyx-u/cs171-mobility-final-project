<script>
	import favicon from '#lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;1,8..60,400&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

{@render children()}

<style>
	:global(:root) {
		--paper: #f5f5f3;
		--panel: #ffffff;
		--ink: #1b2233;
		--ink-2: #555b6b;
		--ink-3: #8a8f9c;
		--rule: #e1e1dc;
		--blue: #2a78d6;
		--red: #d6422a;
		--violet: #6250d6;
		--serif: 'Source Serif 4', Georgia, 'Times New Roman', serif;
		--ui: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
	}
	:global(body) {
		margin: 0;
		background: var(--paper);
		color: var(--ink);
		font-family: var(--ui);
		-webkit-font-smoothing: antialiased;
	}
	:global(*:focus-visible) { outline: 3px solid rgba(98, 80, 214, 0.45); outline-offset: 2px; }

	/* Anything the navigation bar can jump to stops clear of the sticky bar. */
	:global([id^='viz-']), :global(#your-county) { scroll-margin-top: 62px; border-radius: 8px; }

	/* The "arrival" animation SiteNav plays on the target of a navigation link.
	   A chart panel gets a ring that pulses outward; a block of text slides up into place. */
	:global(.nav-arrive) { animation: nav-arrive-ring 1.5s ease-out; }
	:global(.prose.nav-arrive), :global(h1.nav-arrive) { animation: nav-arrive-text 0.7s cubic-bezier(0.2, 0.7, 0.2, 1); }
	@keyframes -global-nav-arrive-ring {
		0% { box-shadow: 0 0 0 0 rgba(42, 120, 214, 0.6); }
		35% { box-shadow: 0 0 0 5px rgba(42, 120, 214, 0.45); }
		100% { box-shadow: 0 0 0 16px rgba(42, 120, 214, 0); }
	}
	@keyframes -global-nav-arrive-text {
		from { opacity: 0.15; transform: translateY(18px); }
		to { opacity: 1; transform: none; }
	}
	@media (prefers-reduced-motion: reduce) {
		:global(*) { transition: none !important; animation: none !important; scroll-behavior: auto !important; }
	}
</style>
