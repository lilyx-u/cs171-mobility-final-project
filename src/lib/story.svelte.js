// Shared story state. The "home" county is chosen once in the hook and then
// pinned in every later view, so the reader can follow their own place through
// the whole argument. Hover is kept here too so the map, scatter and fan can
// all echo the same county.
export const story = $state({
	home: null, // fips string, or null
	hovered: null // county object, or null
});
