# Project Documentation

## Title
Product Line Profitability & Margin Performance Analysis for Nassau Candy Distributor

## Objective
The objective is to build a data-driven profitability intelligence system that helps the distributor understand which products, divisions, and factories create the strongest financial performance and which products create margin risk.

## Problem Statement
The organization lacks clear visibility into product-level profitability. High sales products may not always create strong profit. Without margin intelligence, pricing, promotions, sourcing, and product portfolio decisions remain reactive.

## Methodology

1. Data Cleaning and Validation
   - Standardize column names
   - Convert date fields
   - Validate Sales, Cost, Gross Profit, and Units
   - Remove invalid zero-sales records

2. Metric Engineering
   - Gross Margin %
   - Profit per Unit
   - Revenue Contribution %
   - Profit Contribution %
   - Cost Ratio %

3. Product-Level Analysis
   - Rank products by gross profit
   - Rank products by margin
   - Identify high-sales but low-margin products

4. Division-Level Analysis
   - Aggregate performance by product division
   - Compare revenue, cost, profit, and average margin

5. Pareto Analysis
   - Identify products contributing to 80% of profit
   - Detect over-dependency risk

6. Cost Diagnostics
   - Compare cost, sales, and margin behavior
   - Flag cost-heavy products

7. Factory Intelligence
   - Map products to factories
   - Analyze factory-level sales, cost, profit, and margin

8. Risk Engine
   - Classify products as Star Product, Volume Trap, Cost Heavy, Underperformer, or Review Product

## Tools and Technologies

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- OpenPyXL
- FPDF2

## Expected Outcome
The dashboard enables business stakeholders to make decisions on pricing, sourcing, product promotion, and discontinuation review based on actual profitability and margin data.

## Conclusion
This project establishes a complete profitability intelligence platform for Nassau Candy Distributor. By combining product profitability, division performance, cost diagnostics, Pareto analysis, and factory-level intelligence, the organization gains actionable insight into which products strengthen profitability and which products create margin risk.
