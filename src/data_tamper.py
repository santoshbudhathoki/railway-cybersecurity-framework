import json, random
from pathlib import Path

def tamper_file(src: Path, dst: Path, flip_prob: float = 0.3):
    data = json.loads(src.read_text())
    for row in data:
        state = (row.get("state") or "inactive").lower()
        if random.random() < flip_prob:
            row["state"] = "inactive" if state == "active" else "active"
    dst.write_text(json.dumps(data, indent=2))
    print(f"Tampered -> {dst}")

if __name__ == "__main__":
    # Example:
    # python src/attacks/data_tamper.py
    s = Path("data_samples/sensor_data_sample.json")
    d = Path("data_samples/sensor_data_sample_tampered.json")
    tamper_file(s, d)
    print(f"Tampered file saved to {d}")
    print("Run anomaly detection on the tampered file to see effects.")