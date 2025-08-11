from datetime import datetime
from pathlib import Path
import json, boto3, joblib, pandas as pd, numpy as np

from src.utils import (
    DATA_DIR, MODELS_DIR, AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION,
    BUCKET_NAME, SNS_TOPIC_ARN, JMRI_URL, require_env
)
from src.upload_sensor_data import fetch_sensor_data, save_locally, upload_to_s3
from src.rules import run_rules

MODEL_PATH = MODELS_DIR / "isolation_forest.pkl"
COLS_PATH  = MODELS_DIR / "model_columns.json"

def load_model():
    require_env("SNS_TOPIC_ARN", SNS_TOPIC_ARN)
    if not MODEL_PATH.exists() or not COLS_PATH.exists():
        raise RuntimeError("Train the model first with src/train_model.py")
    model = joblib.load(MODEL_PATH)
    cols = json.loads(COLS_PATH.read_text())
    return model, cols

def to_feature_row(records, cols):
    # Build a single-row vector aligned to trang columns
    df = pd.DataFrame(records)
    df["state"] = df["state"].str.lower().map({"active":1,"inactive":0}).fillna(0)
    # last snapshot per sensor in this file
    latest = df.groupby("userName")["state"].last()
    x = pd.Series(0, index=cols, dtype=float)
    x.loc[latest.index.intersection(x.index)] = latest
    return x.to_frame().T  # shape (1, n_features)

def publish_sns(subject: str, message: str):
    client = boto3.client(
        "sns",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
    client.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)

def main():
    require_env("BUCKET_NAME", BUCKET_NAME)
    rows = fetch_sensor_data(JMRI_URL)
    if not rows:
        print("No sensor rows found.")
        return

    # rule-based alerts
    rule_alerts = run_rules(pd.DataFrame(rows))

    # ML-based anomaly
    model, cols = load_model()
    X = to_feature_row(rows, cols)
    pred = model.predict(X)         # 1=normal, -1=anomaly
    score = model.decision_function(X)[0]

    # Save & upload
    p = save_locally(rows)
    upload_to_s3(p)

    # Alerts (only if rule hit or anomaly)
    msgs = []
    if rule_alerts:
        msgs.append("Rule alerts: " + "; ".join(rule_alerts))
    if pred[0] == -1:
        msgs.append(f"ML anomaly detected (score={score:.4f})")

    if msgs:
        publish_sns(
            subject="🚨 Railway Sensor Alert",
            message=f"File: {p.name}\nTime(UTC): {datetime.utcnow()}\n" + "\n".join(msgs)
        )
        print("Alert sent:\n" + "\n".join(msgs))
    else:
        print(f"No alerts. Score={score:.4f}")

if __name__ == "__main__":
    main()
