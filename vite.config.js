import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			// The site is a single prerendered page, so it builds to plain files in
			// `build/` that any static host can serve (see src/routes/+layout.js).
			adapter: adapter({ fallback: '404.html' }),

			// GitHub Pages serves a project site from /<repository-name>/, not from the
			// domain root. The deploy workflow passes that name in BASE_PATH; locally
			// (`npm run dev`, or a build with no BASE_PATH) the site lives at the root.
			paths: {
				base: process.argv.includes('dev') ? '' : (process.env.BASE_PATH ?? '')
			}
		})
	]
});
