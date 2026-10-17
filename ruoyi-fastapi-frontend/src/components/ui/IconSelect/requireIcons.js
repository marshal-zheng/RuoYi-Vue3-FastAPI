import symbolIds from 'virtual:svg-icons-names';

// Reuse the same sprite catalog as SvgIcon without emitting per-file loaders.
export default symbolIds.map((id) => id.replace(/^icon-/, '')).sort();
