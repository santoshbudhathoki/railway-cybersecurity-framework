# User Guide — Railway Cybersecurity Framework

## 1) Overview
A practical guide to replicate the full pipeline: **JMRI → Python → AWS S3 → Detection (Rules + Isolation Forest) → SNS/CloudWatch Alerts**.

## 2) Prerequisites
- Windows 10/11, Python 3.11+
- Google Chrome
- AWS account (S3, SNS, CloudWatch/EventBridge permissions)
- JMRI (PanelPro) with sensors visible at `http://<jmri-ip>:12080/tables/sensor`

## 3) Setup
```
# venv & deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt



## 4) Data Ingestion & Upload
Script: src/upload_sensor_data.py

What it does: Scrapes JMRI sensor table → normalizes states → saves JSON under data/ with timestamp → uploads to S3.

Run:

python .\src\upload_sensor_data.py
 ## 5) Detection
a. Rule-Based (src/rules.py)
Flags:

    i. >3 sensors active in a snapshot

    ii. Empty state values

    iii. Inactivity hints (cross-file continuity recommended)

b. ML-Based (src/train_model.py + src/upload_sensor_data_with_anomaly.py)
    i.Train model (uses data_samples/ and any data/ JSONs):
        
        python .\src\train_model.py
    ii. Run full pipeline:
        
        python .\src\upload_sensor_data_with_anomaly.py
c. Output:
    i. Saves JSON to data/
    ii. Uploads to S3
    iii. Sends SNS alert when rules/ML trigger

6) Alerts (AWS)
- SNS: Create topic sensor-alerts, subscribe Email/SMS (confirm email).

- CloudWatch/EventBridge: Optional — trigger on S3 “Object Created” to fan out workflows.

- Expected email: subject like “🚨 Railway Sensor Alert”.

7) Automation
- Windows Task Scheduler:

- Create Basic Task → Action: python <repo>\src\upload_sensor_data.py

- Trigger: Every 5 minutes (or as needed)

8) Attack Simulations (Lab/Demo)
- Replay: Re-upload old JSON with new timestamp → should trigger detection.

- Data Tampering: src/attacks/data_tamper.py flips states randomly.

- DoS/MITM: Demonstration-only; use safe lab network.

9) Troubleshooting
- Chrome/driver errors → install Chrome; webdriver-manager fetches the driver automatically.

- AccessDenied (S3/SNS) → fix IAM policy, region, and ARNs.

- Empty states → scraper defaults to "inactive" to stabilize data.

10) Security Notes
- No secrets in code; use .env.

- Rotate IAM keys; enable MFA.

- Use least-privilege policies.