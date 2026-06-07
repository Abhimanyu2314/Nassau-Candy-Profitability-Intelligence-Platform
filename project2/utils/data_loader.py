import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID",
    "Country/Region", "City", "State/Province", "Postal Code", "Division", "Region",
    "Product ID", "Product Name", "Sales", "Units", "Gross Profit", "Cost"
]

def _parse_dates(series: pd.Series) -> pd.Series:
    # Dataset uses dd-mm-yyyy in many rows. dayfirst=True handles it safely.
    return pd.to_datetime(series, errors="coerce", dayfirst=True)

def load_data(path_or_file) -> pd.DataFrame:
    df = pd.read_csv(path_or_file)
    df.columns = df.columns.str.strip()

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df["Order Date"] = _parse_dates(df["Order Date"])
    df["Ship Date"] = _parse_dates(df["Ship Date"])

    for col in ["Sales", "Units", "Gross Profit", "Cost", "Postal Code"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = ["Order ID", "Ship Mode", "Country/Region", "City", "State/Province", "Division", "Region", "Product ID", "Product Name"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    df["Division"] = df["Division"].str.title()
    df["Region"] = df["Region"].str.title()

    # Keep only analytically valid records.
    df = df.dropna(subset=["Order Date", "Sales", "Units", "Gross Profit", "Cost", "Product Name", "Division"])
    df = df[(df["Sales"] > 0) & (df["Units"] > 0)]
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["Sales", "Units", "Gross Profit", "Cost"])
    return df.reset_index(drop=True)
