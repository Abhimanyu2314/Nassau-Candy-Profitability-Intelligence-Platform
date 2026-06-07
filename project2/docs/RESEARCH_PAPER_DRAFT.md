# Product Line Profitability & Margin Performance Analysis for Nassau Candy Distributor

## Abstract
This project develops an industrial-level profitability intelligence system for Nassau Candy Distributor. The system analyzes product sales, units, cost, gross profit, margin percentage, margin volatility, product contribution, division performance, regional profitability, factory-level performance, and portfolio concentration. The dashboard converts raw transactional order data into executive-level insights for pricing, sourcing, promotion planning, product rationalization, and margin risk control.

## Problem Statement
Sales volume alone can mislead management because high-revenue products may produce weak margins, consume excessive manufacturing cost, or create dependency risk. Nassau Candy Distributor requires a data-driven decision system to identify high-value products, weak-margin products, underperforming divisions, and products requiring repricing, renegotiation, or discontinuation review.

## Objectives
1. Clean and validate order, cost, unit, sales, and product data.
2. Calculate profitability KPIs including gross margin, profit per unit, revenue contribution, profit contribution, cost ratio, and margin volatility.
3. Rank products by profit, margin, strategic value, and risk.
4. Compare product divisions by sales, gross profit, cost, average margin, and revenue-profit imbalance.
5. Conduct Pareto 80/20 analysis for revenue and profit dependency.
6. Diagnose cost-heavy and low-margin products using scatter plots and heatmaps.
7. Analyze profitability by factory using provided factory-product correlation and factory coordinates.
8. Generate executive recommendations and export CSV, Excel, and PDF reports.

## Methodology
The system follows an end-to-end analytics workflow: data loading, validation, cleaning, feature engineering, aggregation, risk scoring, visualization, and reporting. Invalid sales records are removed, missing numerical values are handled, labels are standardized, and dates are parsed. Product-level metrics are then calculated using the cleaned data.

## Key Metrics
- Gross Margin (%) = Gross Profit / Sales × 100
- Profit per Unit = Gross Profit / Units
- Revenue Contribution (%) = Product Sales / Total Sales × 100
- Profit Contribution (%) = Product Gross Profit / Total Gross Profit × 100
- Cost Ratio (%) = Cost / Sales × 100
- Margin Volatility = Standard deviation of monthly product margin
- Risk Score = weighted score combining margin weakness, cost ratio, and dependency index

## Dashboard Modules
The Streamlit application includes Executive Overview, Product Profitability, Division Performance, Cost Diagnostics, Pareto 80/20, Factory Intelligence, Risk Command Center, Recommendations, Advanced Analytics, Reports & Export, and Requirement Coverage.

## Insights and Decision Use
The system highlights star products, volume traps, cost-heavy products, underperformers, and products needing executive review. These insights help management decide where to increase promotion, where to review pricing, where to negotiate factory cost, and where to rationalize the product portfolio.

## Conclusion
This project establishes a data-driven profitability intelligence platform for Nassau Candy Distributor. By transforming transactional order data into margin, contribution, factory, and risk intelligence, the organization can make proactive business decisions on pricing, sourcing, product promotion, and product portfolio optimization.
