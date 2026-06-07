import numpy as np
import pandas as pd


def safe_div(numerator, denominator, multiplier=1):
    """Safe division for pandas Series/scalars."""
    if hasattr(denominator, "replace"):
        denominator = denominator.replace(0, np.nan)
    elif denominator == 0:
        denominator = np.nan

    result = numerator / denominator * multiplier
    if hasattr(result, "replace"):
        return result.replace([np.inf, -np.inf], 0).fillna(0)
    if pd.isna(result) or np.isinf(result):
        return 0
    return result


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add profitability metrics to raw, product, division, factory, or monthly data.

    This function is intentionally flexible: aggregated tables do not contain
    Order Date, so Order Month is only created when Order Date exists.
    """
    df = df.copy()

    df["Gross Margin %"] = safe_div(df["Gross Profit"], df["Sales"], 100)
    df["Profit per Unit"] = safe_div(df["Gross Profit"], df["Units"])
    df["Cost Ratio %"] = safe_div(df["Cost"], df["Sales"], 100)

    total_sales = df["Sales"].sum()
    total_profit = df["Gross Profit"].sum()

    df["Revenue Contribution %"] = safe_div(df["Sales"], total_sales, 100) if total_sales else 0
    df["Profit Contribution %"] = safe_div(df["Gross Profit"], total_profit, 100) if total_profit else 0

    if "Order Date" in df.columns:
        df["Order Month"] = pd.to_datetime(df["Order Date"], errors="coerce").dt.to_period("M").astype(str)

    return df.replace([np.inf, -np.inf], 0).fillna(0)


def product_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouping = ["Product ID", "Product Name", "Division", "Factory"] if "Factory" in df.columns else ["Product ID", "Product Name", "Division"]
    out = df.groupby(grouping, as_index=False).agg(
        Sales=("Sales", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"),
        Orders=("Order ID", "nunique"),
        Regions=("Region", "nunique"),
    )
    out = out.rename(columns={"Gross_Profit": "Gross Profit"})
    out = add_metrics(out)

    # Margin volatility required by the project brief: standard deviation of monthly product margin.
    # Low values mean stable margin; high values indicate pricing/cost instability.
    if "Order Date" in df.columns:
        temp = df.copy()
        temp["Order Month"] = pd.to_datetime(temp["Order Date"], errors="coerce").dt.to_period("M").astype(str)
        monthly_product = temp.groupby(grouping + ["Order Month"], as_index=False).agg(
            Sales=("Sales", "sum"),
            Gross_Profit=("Gross Profit", "sum"),
        ).rename(columns={"Gross_Profit": "Gross Profit"})
        monthly_product["Monthly Margin %"] = safe_div(monthly_product["Gross Profit"], monthly_product["Sales"], 100)
        volatility = monthly_product.groupby(grouping, as_index=False)["Monthly Margin %"].std().rename(
            columns={"Monthly Margin %": "Margin Volatility"}
        )
        out = out.merge(volatility, on=grouping, how="left")
    else:
        out["Margin Volatility"] = 0

    out["Margin Volatility"] = out["Margin Volatility"].fillna(0).round(2)
    return out.sort_values("Gross Profit", ascending=False).reset_index(drop=True)


def division_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby("Division", as_index=False).agg(
        Sales=("Sales", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"),
        Products=("Product Name", "nunique"),
        Orders=("Order ID", "nunique"),
    ).rename(columns={"Gross_Profit": "Gross Profit"})
    out = add_metrics(out)
    return out.sort_values("Gross Profit", ascending=False).reset_index(drop=True)


def factory_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby("Factory", as_index=False).agg(
        Sales=("Sales", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"),
        Products=("Product Name", "nunique"),
        Latitude=("Factory Latitude", "first"),
        Longitude=("Factory Longitude", "first"),
    ).rename(columns={"Gross_Profit": "Gross Profit"})
    out = add_metrics(out)
    return out.sort_values("Gross Profit", ascending=False).reset_index(drop=True)


def monthly_margin(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    if "Order Month" not in work.columns:
        work["Order Month"] = pd.to_datetime(work["Order Date"], errors="coerce").dt.to_period("M").astype(str)

    out = work.groupby("Order Month", as_index=False).agg(
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"),
        Units=("Units", "sum"),
    ).rename(columns={"Gross_Profit": "Gross Profit"})
    return add_metrics(out)


def region_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate profitability by customer region/state for geographic margin diagnostics."""
    group_cols = ["Region"]
    if "State/Province" in df.columns:
        group_cols.append("State/Province")
    out = df.groupby(group_cols, as_index=False).agg(
        Sales=("Sales", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"),
        Products=("Product Name", "nunique"),
        Orders=("Order ID", "nunique"),
    ).rename(columns={"Gross_Profit": "Gross Profit"})
    out = add_metrics(out)
    return out.sort_values("Gross Profit", ascending=False).reset_index(drop=True)


def pareto_table(summary: pd.DataFrame, value_col: str) -> pd.DataFrame:
    out = summary.sort_values(value_col, ascending=False).copy()
    total = out[value_col].sum()
    out[f"Cumulative {value_col} %"] = safe_div(out[value_col].cumsum(), total, 100) if total else 0
    out["Product Rank"] = range(1, len(out) + 1)
    return out
