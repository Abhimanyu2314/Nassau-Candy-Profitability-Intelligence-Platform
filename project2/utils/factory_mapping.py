import pandas as pd

FACTORY_COORDINATES = {
    "Lot's O' Nuts": {"Latitude": 32.881893, "Longitude": -111.768036},
    "Wicked Choccy's": {"Latitude": 32.076176, "Longitude": -81.088371},
    "Sugar Shack": {"Latitude": 48.119140, "Longitude": -96.181150},
    "Secret Factory": {"Latitude": 41.446333, "Longitude": -90.565487},
    "The Other Factory": {"Latitude": 35.117500, "Longitude": -89.971107},
}

PRODUCT_FACTORY = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory",
}

def attach_factory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY).fillna("Unmapped Factory")
    df["Factory Latitude"] = df["Factory"].map(lambda x: FACTORY_COORDINATES.get(x, {}).get("Latitude"))
    df["Factory Longitude"] = df["Factory"].map(lambda x: FACTORY_COORDINATES.get(x, {}).get("Longitude"))
    return df
