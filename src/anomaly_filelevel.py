import json, pandas as pd, joblib
from pathlib import Path
from src.utils import DATA_DIR, MODELS_DIR

MODEL_PATH = MODELS_DIR / "isolation_forest.pkl"
COLS_PATH  = MODELS_DIR / "model_columns.json"

def main():
    model = joblib.load(MODEL_PATH)
    cols = json.loads(COLS_PATH.read_text())

    for p in sorted(DATA_DIR.glob("*.json")):
        rows = json.loads(p.read_text())
        df = pd.DataFrame(rows)
        df["state"] = df["state"].str.lower().map({"active":1,"inactive":0}).fillna(0)
        latest = df.groupby("userName")["state"].last()
        x = pd.Series(0, index=cols, dtype=float)
        x.loc[latest.index.intersection(x.index)] = latest
        X = x.to_frame().T
        pred = model.predict(X)[0]
        score = model.decision_function(X)[0]
        label = "ANOMALY" if pred == -1 else "NORMAL"
        print(f"{p.name}: {label} (score={score:.4f})")

if __name__ == "__main__":
    main()
