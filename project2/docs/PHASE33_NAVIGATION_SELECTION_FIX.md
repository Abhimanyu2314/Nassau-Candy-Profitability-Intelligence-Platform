# Phase 33 Navigation Selection Fix

Fixed the issue where sidebar navigation options were not being selected after adding the loading overlay.

## Root Cause
The JavaScript loading overlay was being inserted during the click capture phase. This could block Streamlit radio/sidebar controls before the click reached the actual widget.

## Fix Applied
- Floating rail links still show the loader and navigate using query parameters.
- Streamlit sidebar radio clicks now receive the click first.
- Loader is delayed by 90ms for actual Streamlit navigation controls.
- Settings option remains removed.
- Loader keeps blur overlay, darkened background, and page-freeze behavior.

Version: v33.0
