# Phase 40 Risk Note Hard Fix

Removed the remaining path that allowed raw HTML fragments such as `<div class='kpi-note'>` to appear in the Risk Command Center cards. KPI notes are now forced to plain text and risk-level notes are mapped directly.
