from pathlib import Path
from dotenv import load_dotenv
import os

# Project roots/paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SAMPLES_DIR = ROOT / "data_samples"
MODELS_DIR = ROOT / "models"
DOCS_DIR = ROOT / "docs"

for d in (DATA_DIR, SAMPLES_DIR, MODELS_DIR, DOCS_DIR):
    d.mkdir(exist_ok=True)

# Load secrets
load_dotenv(ROOT / ".env", override=True)

AWS_REGION   = os.getenv("AWS_REGION", "ap-southeast-2")
BUCKET_NAME  = os.getenv("BUCKET_NAME", "")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "")
SNS_TOPIC_ARN  = os.getenv("SNS_TOPIC_ARN", "")
JMRI_URL       = os.getenv("JMRI_URL", "http://localhost:12080/tables/sensor")

def require_env(varname: str, value: str):
    if not value:
        raise RuntimeError(f"Missing required env var: {varname}")
    return value