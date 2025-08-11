##### How to Operate (Full Setup & Run Book)
This section explains exactly how to run the end-to-end pipeline: JMRI → Python → AWS S3 → Rules + Isolation Forest → SNS/CloudWatch Alerts, plus automation and testing. Keep your .env secret.

0) Prerequisites
- Windows 10/11, Python 3.11+, Google Chrome

- AWS account with S3, SNS, and EventBridge/CloudWatch access

- JMRI PanelPro running and reachable at:

- http://<JMRI-IP>:12080/table/sensor

- Repo structure (important files only)

        bashsrc/
        upload_sensor_data.py                # scrape → save → upload
        upload_sensor_data_with_anomaly.py   # scrape → rules + ML → upload + SNS
        train_model.py                       # build Isolation Forest model
        rules.py                             # rule-based detection logic
        attacks/data_tamper.py               # (optional) simulate tampering
        smoke/pra.py                         # Chrome/WebDriver sanity check
        models/
        isolation_forest.pkl                 # trained model (created by train_model.py)
        model_columns.json                   # trang feature columns
        data_samples/
        sensor_data_sample.json              # example input (sanitized)
        data/                                  # live JSON snapshots (auto-created)
        .env.example                           # template to copy → .env
        requirements.txt
1) Local environment
# from the repo root
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
Create your .env (copy the template then edit):

Copy-Item .env.example .env
.env contents to fill (no quotes):

    AWS_REGION=ap-southeast-2
    BUCKET_NAME=your-s3-bucket-name
    AWS_ACCESS_KEY=YOUR_AWS_ACCESS_KEY
    AWS_SECRET_KEY=YOUR_AWS_SECRET_KEY
    SNS_TOPIC_ARN=arn:aws:sns:ap-southeast-2:YOUR_ACCOUNT_ID:sensor-alerts
    JMRI_URL=http://<JMRI-IP>:12080/tables/sensor
         # Do not commit .env. It’s in .gitignore.

2) JMRI PanelPro setup (once)
    1. Open PanelPro → Preferences → Connections

            System: NCE PowerCab (or your system)

            Port: the COM port shown for your USB interface

    2. Tools → Tables → Sensors → Add your sensors

        Give clear User Names (e.g., sensor1, sensor2, …)

    3. Confirm live updates at:

        http://<JMRI-IP>:12080/table/sensor
3) Train the Isolation Forest model (one-time or when data drifts)
Uses data_samples/ (and any JSON in data/) to learn normal behavior.

    python .\src\train_model.py
Outputs:

    models/isolation_forest.pkl

    models/model_columns.json

4) Data ingestion & upload (baseline run)
Script: src/upload_sensor_data.py

What it does:

    Scrapes JMRI table (JMRI_URL)

    Normalizes empty/unknown states → "inactive"

    Writes JSON → data/sensor_data_YYYYMMDDHHMMSS.json

    Uploads file to S3 bucket BUCKET_NAME

Run it:

python .\src\upload_sensor_data.py
5) Full pipeline with detection & alerting
Script: src/upload_sensor_data_with_anomaly.py

What it does:

    Scrape JMRI → build one feature vector (latest state per sensor)

    Rules → evaluate simple security rules (see §6)

    ML → load models/isolation_forest.pkl, get predict() and decision_function()

    1 = normal, -1 = anomaly (more negative score = more abnormal)

    Save JSON to data/ and upload to S3

    If rules or ML trigger → send AWS SNS email

Run it:

    python .\src\upload_sensor_data_with_anomaly.py
Expected console output example:

    Uploaded sensor_data_20250101T120001.json to s3://your-bucket/...
    Alert sent:
    Rule alerts: Mass activation (>3)
    ML anomaly detected (score=-0.2149)
6) Detection rules (exact logic)
File: src/rules.py

R0 — Empty states present
    If any sensor has an empty/unknown state → flag data issue.

R1 — Mass activation
    If > 3 sensors are "active" in the same snapshot → flag suspicious mass trigger.

R2 — Inactive sensors present (continuity hint)
    Marks presence of "inactive" sensors; teams should verify continuity across files.

    Cross-file long-inactivity rules require history (you can extend later).

7) Windows Task Scheduler (automation)
Task Scheduler → Create Basic Task…

    Name: RailwaySensorUpload

Trigger: Daily → Repeat task every 5 minutes (or as needed)

    Action: Start a program

Program/script:

    python
Add arguments:

    C:\full\path\to\repo\src\upload_sensor_data_with_anomaly.py
Start in:

    C:\full\path\to\repo
Finish, then Open task → Properties →

        Run whether user is logged on or not

        Start in is set to the repo root

        Optional: set .venv activation by using full interpreter path:

        C:\full\path\to\repo\.venv\Scripts\python.exe C:\full\path\to\repo\src\upload_sensor_data_with_anomaly.py
8) AWS configuration
A) S3 Bucket
    Create bucket your-s3-bucket-name in AWS_REGION

    Block public access (recommended)

    Optional: enable versioning

B) SNS Topic & Subscription
    Create topic: sensor-alerts

    Create subscription → Email → confirm from your inbox

    Keep the Topic ARN and set it in .env as SNS_TOPIC_ARN

C) EventBridge/CloudWatch (optional rule-based monitoring)
    Rule: Event pattern → S3 → Object Created → your bucket

    Target: SNS topic sensor-alerts (or a Lambda you control)

D) Mmal IAM permissions (attach to your user/role)
    Adjust bucket name and account id before using.

    json{
    "Version": "2012-10-17",
    "Statement": [
        { "Effect": "Allow", "Action": ["s3:PutObject","s3:GetObject","s3:ListBucket"], "Resource": [
        "arn:aws:s3:::your-s3-bucket-name",
        "arn:aws:s3:::your-s3-bucket-name/*"
        ]},
        { "Effect": "Allow", "Action": ["sns:Publish"], "Resource": "arn:aws:sns:ap-southeast-2:YOUR_ACCOUNT_ID:sensor-alerts" }
    ]
    }
9) Validation checklist
        JMRI page reachable: open http://<JMRI-IP>:12080/table/sensor

        Local JSON saved: files appear in data/ after each run

        S3 upload: file appears in your bucket with the same name

        Model present: models/isolation_forest.pkl exists

        Email alert: when rules/ML trigger, you receive an SNS email

        Task Scheduler: runs every 5 minutes and produces a new JSON in S3

10) Optional: attack simulations (lab only)
        Only in a controlled environment you own.

        Replay: Re-upload an old sensor_data_*.json with a new timestamp → should trigger anomaly.

        Data tampering:

        python .\src\attacks\data_tamper.py
        Produces a tampered JSON; upload and observe detection.

        DoS / MITM: Demonstrate safely on lab network to show why HTTPS & rate-limits matter (CloudWatch can also spot S3 upload spikes).

11) Troubleshooting
        Chrome/driver error: install Chrome; webdriver-manager auto-fetches the driver.

        AccessDenied on S3/SNS: wrong region, wrong ARN, or missing IAM permissions.

        Empty states: scraper defaults blanks → "inactive" to stabilize features.

        No emails: subscription not confirmed, or SNS topic/region mismatch.

        Scheduler runs wrong Python: point “Program/script” to

        php-template<repo>\.venv\Scripts\python.exe
12) What each Python file does
        src/upload_sensor_data.py
        Scrapes JMRI → saves JSON → uploads to S3. Use for baseline ingestion.

        src/upload_sensor_data_with_anomaly.py
        Full pipeline: scrape → rules + Isolation Forest → upload → SNS alert.

        src/train_model.py
        Builds Isolation Forest from data_samples/ (+ any data/) and saves:

        models/isolation_forest.pkl

        models/model_columns.json

        src/rules.py
        Implements R0 Empty states, R1 Mass activation (>3), R2 Inactive continuity hint.

        src/attacks/data_tamper.py
        Flips sensor states randomly (for demo/testing).

        src/smoke/pra.py
        Checks that Chrome/WebDriver is working.

13) Screenshots to include (for README/docs/LinkedIn)
      

        graphqlsystem_architecture.png         # high-level pipeline diagram
        jmri_sensor_table.png           # live JMRI table
        aws_s3_upload.png               # S3 bucket with JSON files
        sns_email_alert.png             # alert email screenshot
        anomaly_detection.png           # console output showing anomaly & rules
        attack_simulation.png           # (optional) table of simulated attacks