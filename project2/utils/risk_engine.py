import pandas as pd
import numpy as np


def classify_products(products: pd.DataFrame, margin_threshold: float = 25.0) -> pd.DataFrame:
    """Classify products into business risk/action segments and generate recommendation text."""
    df = products.copy()
    if df.empty:
        return df

    sales_q75 = df["Sales"].quantile(0.75)
    sales_med = df["Sales"].median()
    profit_med = df["Gross Profit"].median()
    cost_ratio_q75 = df["Cost Ratio %"].quantile(0.75)

    # dependency intensity: high profit contribution means the portfolio depends on this SKU.
    max_contrib = df["Profit Contribution %"].max() or 1
    df["Dependency Index"] = (df["Profit Contribution %"] / max_contrib * 100).fillna(0).round(2)

    def label(row):
        if row["Gross Profit"] <= 0 or row["Gross Margin %"] < margin_threshold / 2:
            return "Critical Margin Risk"
        if row["Sales"] >= sales_q75 and row["Gross Margin %"] < margin_threshold:
            return "Volume Trap"
        if row["Cost Ratio %"] >= cost_ratio_q75 and row["Gross Margin %"] < margin_threshold:
            return "Cost Heavy"
        if row["Sales"] >= sales_med and row["Gross Margin %"] >= margin_threshold and row["Gross Profit"] >= profit_med:
            return "Star Product"
        if row["Sales"] < sales_med and row["Gross Profit"] < profit_med:
            return "Underperformer"
        return "Review Product"

    df["Risk Segment"] = df.apply(label, axis=1)
    df["Risk Score"] = (
        (100 - df["Gross Margin %"].clip(0, 100)) * 0.50
        + df["Cost Ratio %"].clip(0, 100) * 0.30
        + df["Dependency Index"].clip(0, 100) * 0.20
    ).round(2)

    def level(score):
        if score >= 75:
            return "Critical"
        if score >= 55:
            return "High"
        if score >= 35:
            return "Medium"
        return "Low"

    df["Risk Level"] = df["Risk Score"].apply(level)

    def recommendation(row):
        if row["Risk Segment"] == "Star Product":
            return "Scale promotion, protect inventory availability, and maintain supplier/factory continuity."
        if row["Risk Segment"] == "Volume Trap":
            return "Review pricing, discounts, and pack-size strategy because revenue is not converting into margin."
        if row["Risk Segment"] == "Cost Heavy":
            return "Renegotiate manufacturing/sourcing cost or redesign cost structure."
        if row["Risk Segment"] == "Critical Margin Risk":
            return "Immediate repricing or discontinuation review required."
        if row["Risk Segment"] == "Underperformer":
            return "Test bundling, targeted campaigns, or rationalization if demand remains weak."
        return "Monitor against division benchmark and reassess after next reporting cycle."

    df["AI Recommendation"] = df.apply(recommendation, axis=1)
    return df.sort_values(["Risk Score", "Gross Profit"], ascending=[False, False]).reset_index(drop=True)


def executive_recommendations(products: pd.DataFrame, divisions: pd.DataFrame, factories: pd.DataFrame):
    recs = []
    if not products.empty:
        best = products.sort_values("Gross Profit", ascending=False).iloc[0]
        highest_margin = products.sort_values("Gross Margin %", ascending=False).iloc[0]
        riskiest = products.sort_values("Risk Score", ascending=False).iloc[0] if "Risk Score" in products.columns else products.sort_values("Gross Margin %").iloc[0]
        concentration = products.sort_values("Profit Contribution %", ascending=False).head(3)["Profit Contribution %"].sum()

        recs.append(f"Protect and scale '{best['Product Name']}' because it contributes the highest gross profit.")
        recs.append(f"Use '{highest_margin['Product Name']}' as a margin benchmark for pricing and cost discipline.")
        recs.append(f"Immediately review '{riskiest['Product Name']}' because it has the highest combined risk score.")
        if concentration > 50:
            recs.append(f"Portfolio dependency is high: the top three products contribute {concentration:.1f}% of profit. Build backup growth SKUs.")
        else:
            recs.append(f"Profit concentration is manageable: top three products contribute {concentration:.1f}% of profit.")

    if not divisions.empty:
        top_div = divisions.sort_values("Gross Profit", ascending=False).iloc[0]
        low_div = divisions.sort_values("Gross Margin %").iloc[0]
        recs.append(f"'{top_div['Division']}' is the strongest profit division and should receive priority in promotion planning.")
        recs.append(f"Start margin improvement with '{low_div['Division']}', the lowest-margin division.")

    if not factories.empty and "Factory" in factories.columns:
        top_factory = factories.sort_values("Gross Profit", ascending=False).iloc[0]
        low_factory = factories.sort_values("Gross Margin %").iloc[0]
        recs.append(f"Factory profitability is strongest at '{top_factory['Factory']}', making it a priority production node.")
        recs.append(f"Review cost efficiency at '{low_factory['Factory']}' because it has the weakest factory margin.")

    recs.append("Use Pareto concentration results to reduce over-dependence on a small number of products.")
    return recs


def add_portfolio_actions(products: pd.DataFrame) -> pd.DataFrame:
    """Add a CFO-style strategic score and final action label.

    Score logic rewards profit, margin and sales strength while penalizing excessive cost ratio.
    Output categories are designed for executive decision-making.
    """
    df = products.copy()
    if df.empty:
        return df

    def pct_rank(col, ascending=True):
        return df[col].rank(pct=True, ascending=ascending).fillna(0) * 100

    margin_score = pct_rank("Gross Margin %", ascending=True)
    profit_score = pct_rank("Gross Profit", ascending=True)
    sales_score = pct_rank("Sales", ascending=True)
    cost_penalty = pct_rank("Cost Ratio %", ascending=True)

    df["Strategic Score"] = (
        0.35 * margin_score +
        0.30 * profit_score +
        0.20 * sales_score +
        0.15 * (100 - cost_penalty)
    ).round(2)

    def action(row):
        if row.get("Risk Level", "") in ["Critical", "High"] and row["Gross Margin %"] < 25:
            return "Discontinue / Reprice Review"
        if row["Strategic Score"] >= 80 and row["Gross Margin %"] >= 25:
            return "Invest & Scale"
        if row["Strategic Score"] >= 65:
            return "Grow Selectively"
        if row["Strategic Score"] >= 45:
            return "Monitor"
        return "Review / Rationalize"

    df["Executive Action"] = df.apply(action, axis=1)
    return df
