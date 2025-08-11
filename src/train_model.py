from pathlib import Path
import json, pandas as pd, joblib
from sklearn.ensemble import IsolationForest

from src.utils import DATA_DIR, SAMPLES_DIR, MODELS_DIR

MODEL_PATH = MODELS_DIR / "isolation_forest.pkl"
COLS_PATH  = MODELS_DIR / "model_columns.json"

def load_all_json_frames():
    rows = []
    for p in list(DATA_DIR.glob("*.json")) + list(SAMPLES_DIR.glob("*.json")):
        try:
            rows.extend(json.loads(p.read_text()))
        except Exception as e:
            print(f"Skipping {p.name}: {e}")
    if not rows:
        raise RuntimeError("No JSON files found in data/ or data_samples/")
    return pd.DataFrame(rows)

def prepare_matrix(df: pd.DataFrame):
    # map state -> {active:1, inactive:0}
    df = df.copy()
    df["state"] = df["state"].fillna("inactive").str.lower()
    df["state"] = df["state"].map({"active":1, "inactive":0}).fillna(0)
    # pivot by userName (sensor ID)
    pivot = df.pivot_table(
        index="timestamp", columns="userName", values="state", aggfunc="max"
    ).fillna(0).sort_index()
    # Persist final column order
    cols = list(pivot.columns)
    return pivot, cols

def main():
    df = load_all_json_frames()
    X, cols = prepare_matrix(df)

    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X)

    joblib.dump(model, MODEL_PATH)
    COLS_PATH.write_text(json.dumps(cols, indent=2))
    print(f"Saved model → {MODEL_PATH}")
    print(f"Saved model columns → {COLS_PATH}")

if __name__ == "__main__":
    main()
