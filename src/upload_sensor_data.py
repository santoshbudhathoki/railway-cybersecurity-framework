from datetime import datetime
from pathlib import Path
import json, boto3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from src.utils import (
    DATA_DIR, AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, BUCKET_NAME, JMRI_URL, require_env
)

def fetch_sensor_data(url: str):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    try:
        driver.get(url)
        table = driver.find_element(By.ID, "jmri-data")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # skip header
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        data = []
        for r in rows:
            tds = r.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 6:
                state = (tds[5].text or "").strip() or "inactive"
                data.append({
                    "name": tds[0].text.strip(),
                    "userName": tds[1].text.strip(),
                    "inverted": (tds[4].text or "").strip(),
                    "state": state,
                    "timestamp": now
                })
        return data
    finally:
        driver.quit()

def save_locally(records):
    fname = f"sensor_data_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    p = DATA_DIR / fname
    p.write_text(json.dumps(records, indent=2))
    return p

def upload_to_s3(path: Path):
    require_env("BUCKET_NAME", BUCKET_NAME)
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
    s3.upload_file(str(path), BUCKET_NAME, path.name)

def main():
    rows = fetch_sensor_data(JMRI_URL)
    if not rows:
        print("No sensor rows found.")
        return
    p = save_locally(rows)
    upload_to_s3(p)
    print(f"Uploaded {p.name} to s3://{BUCKET_NAME}/{p.name}")

if __name__ == "__main__":
    main()
