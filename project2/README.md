# Nassau Candy Profitability Intelligence Platform

An industrial-level Streamlit analytics application for **Product Line Profitability & Margin Performance Analysis for Nassau Candy Distributor**.

This project turns raw sales, cost, product, division, region, and factory data into an executive decision-support platform. It helps identify high-profit products, margin-risk products, division imbalance, product concentration risk, and factory-level profitability.

## Main Features

- Executive KPI command center
- Product profitability leaderboard
- Gross margin percentage analysis
- Profit-per-unit analysis
- Division-level revenue, cost, and profit comparison
- Cost vs margin diagnostic scatter plots
- Pareto 80/20 revenue and profit concentration analysis
- Factory-level profitability mapping
- Margin risk classification engine
- AI-style business recommendation panel
- Product search, division filter, region filter, factory filter, date filter, and margin threshold slider
- CSV export
- Excel report export
- Executive PDF report export

## Business Problem

Sales volume alone does not prove business success. A product may sell heavily but still weaken profitability if its cost is too high or its margin is too low. This platform helps Nassau Candy answer:

- Which products truly drive gross profit?
- Which high-sales products have weak margins?
- Which divisions are financially efficient or inefficient?
- Which factories contribute the best profit performance?
- Which products need repricing, cost renegotiation, or discontinuation review?

## Key Metrics Used

| Metric | Formula |
|---|---|
| Gross Margin % | Gross Profit / Sales × 100 |
| Profit per Unit | Gross Profit / Units |
| Revenue Contribution % | Product Sales / Total Sales × 100 |
| Profit Contribution % | Product Gross Profit / Total Gross Profit × 100 |
| Cost Ratio % | Cost / Sales × 100 |
| Risk Score | Rule-based score using margin, cost ratio, profit, and sales behavior |

## Project Structure

```text
nassau_profitability_enterprise/
│
├── app.py
├── requirements.txt
├── RUN_THIS_FIRST.txt
├── README.md
│
├── data/
│   └── nassau_orders.csv
│
├── utils/
│   ├── data_loader.py
│   ├── metrics.py
│   ├── risk_engine.py
│   ├── factory_mapping.py
│   └── report_generator.py
│
├── assets/
└── reports/
```

## Installation

Open CMD or terminal inside the project folder and run:

```bash
python -m pip install -r requirements.txt
```

Then start the dashboard:

```bash
streamlit run app.py
```

## Required Python Packages

- streamlit
- pandas
- numpy
- plotly
- openpyxl
- fpdf2
- scikit-learn

## Dashboard Modules

### 1. Executive Dashboard
Shows total sales, gross profit, average margin, number of products, and risk product count. It also includes monthly sales/profit/cost trend and product contribution treemap.

### 2. Product Profitability
Ranks products by sales, gross profit, margin, profit per unit, revenue contribution, and profit contribution.

### 3. Division Performance
Compares Chocolate, Sugar, and Other divisions using sales, cost, profit, product count, and margin distribution.

### 4. Cost Diagnostics
Uses scatter plots to identify cost-heavy and margin-poor products.

### 5. Pareto 80/20
Identifies product dependency by showing how many products contribute to 80% of total profit or sales.

### 6. Factory Intelligence
Maps products to factories and analyzes factory-wise sales, cost, profit, and average margin.

### 7. Recommendations
Generates business-friendly recommendations for pricing, sourcing, promotion, and portfolio review.

### 8. Data Export
Exports filtered product analytics as CSV, Excel, and executive PDF report.

## Submission Value

This project is suitable for analytics, data science, business intelligence, and industrial decision-support use cases. It goes beyond basic EDA by adding profitability metrics, risk scoring, factory intelligence, and report exports.

## Phase 4 Industrial Intelligence Upgrade

Latest additions include:

- Interactive factory profitability map
- Profit waterfall chart
- Margin risk heatmap
- Strategic product score
- Executive action classification
- Advanced analytics decision matrix
- Professional sidebar navigation

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Phase 8: Requirement-Complete Upgrade

This version completes the full project brief:

- Margin Volatility KPI added.
- Region / State profitability diagnostics added.
- Revenue and profit Pareto analysis included.
- High-sales / low-margin product table added.
- Low-sales / low-profit product table added.
- Revenue-profit imbalance by division added.
- Factory command map and factory intelligence included.
- Requirement Coverage page added inside the Streamlit app.
- Research paper draft, government executive summary, and checklist added in `docs/`.

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Phase 9 Final Requirement Completion

Final fixes include portfolio monthly margin volatility, a cost diagnostics management action queue, an interactive factory profitability map using the supplied factory coordinates, and updated requirement traceability.


## Phase 23 Update
Visible loading screen now appears immediately after sidebar navigation clicks.


## Phase 33 Fix
Sidebar navigation options now select correctly with the loading screen enabled.


## Phase 46 Enterprise Polish

Final video-review improvements: hidden Plotly toolbars, smoother page transitions, chart reveal animation, refined chart colors, and v46.0 version update.
