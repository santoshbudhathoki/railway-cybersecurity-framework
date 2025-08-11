import pandas as pd
from typing import List

def normalize_state(s: str) -> str:
    return (s or "").strip().lower()

def run_rules(df: pd.DataFrame) -> List[str]:
    alerts = []
    if "state" not in df.columns:
        return ["No 'state' column in data"]

    # Normalize
    df = df.copy()
    df["state"] = df["state"].apply(normalize_state)

    # Rule 0: empty/unknown states present
    if (df["state"] == "").any():
        alerts.append("Empty sensor states present")

    # Rule 1: mass activation in a snapshot (>3 active)
    if (df["state"] == "active").sum() > 3:
        alerts.append("Mass activation (>3 active in file)")

    # Note: cross-file rules (e.g., inactivity > N minutes) need historical state.
    # Here we just flag that there are inactive sensors for follow-up.
    if (df["state"] == "inactive").any():
        alerts.append("Inactive sensors present (check continuity across files)")

    return alerts
    return value    
