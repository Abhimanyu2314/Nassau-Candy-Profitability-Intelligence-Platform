# Phase 35 Navigation Click Deep Fix

Fixed sidebar icon selection by removing JavaScript preventDefault from floating rail links.

- Floating icon rail links now use native browser navigation with ?nav=.
- Loader is visual only and no longer blocks the actual click/navigation.
- Added stale-loader cleanup on every rerun.
- Increased floating rail z-index and pointer events.
- Version updated to v35.0.

After extracting, run a hard refresh once with Ctrl+F5 to clear old Streamlit browser cache.
