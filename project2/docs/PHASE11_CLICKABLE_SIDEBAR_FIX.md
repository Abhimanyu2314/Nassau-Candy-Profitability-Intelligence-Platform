# Phase 11 - Clickable Sidebar Navigation Fix

This version fixes the floating sidebar functionality.

## What was fixed

- Floating neon sidebar icons are now clickable.
- Each icon uses URL-based Streamlit routing through `?nav=` query parameters.
- Active-page glow now follows the selected icon.
- Added dedicated rail icons for all major dashboard modules:
  - Executive Overview
  - Product Profitability
  - Division Performance
  - Cost Diagnostics
  - Pareto 80/20
  - Factory Intelligence
  - Risk Command Center
  - AI Insights
  - Advanced Analytics
  - Reports & Export
  - Requirement Coverage
- Sidebar spacing was made more compact to avoid overflow.
- Version updated to v11.0.

## How to use

Click the floating sidebar icons on the left. The app will navigate to the selected module automatically.

The standard Streamlit sidebar navigation is still available as a fallback.
