# Phase 39 - Risk Note Rendering + Smoothness Fix

Updates:
- Fixed Risk Command Center notes showing raw HTML fragments such as `<div class='kpi-note'>...`.
- Added a sanitization helper that strips accidental HTML from KPI titles, values, trend labels, and notes.
- Reinforced KPI note styling so notes render as clean neon-dashboard text.
- Updated version to v39.0.

Run:
```bash
pip install -r requirements.txt
streamlit run app.py
```
