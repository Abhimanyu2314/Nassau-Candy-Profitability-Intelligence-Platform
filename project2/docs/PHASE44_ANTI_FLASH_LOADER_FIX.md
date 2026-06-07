# Phase 44 Anti-Flash Loader Fix

This update smooths the module navigation transition by keeping the loader visible while Streamlit completes its rerender.

## Changes
- Increased loader minimum visibility to approximately 1.25 seconds.
- Delayed stale-loader cleanup to avoid white/empty Streamlit flash during rerender.
- Added Streamlit dark theme configuration in `.streamlit/config.toml` so the app never falls back to a white page during reload.
- Removed old Python cache files.
- Updated project version to v44.0.
