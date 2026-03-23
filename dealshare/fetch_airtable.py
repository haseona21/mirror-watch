"""
fetch_airtable.py
-----------------
Fetches new deals from Airtable, diffs against Google Drive baseline.
Returns list of new deals grouped by Seed / Series A++ / Uncategorized.
"""

import os
import io
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

AIRTABLE_TOKEN    = os.environ["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID  = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_ID = os.environ["AIRTABLE_TABLE_ID"]
GDRIVE_FILE_ID    = os.environ["GDRIVE_FILE_ID"]
GDRIVE_CREDS_JSON = os.environ["GDRIVE_CREDS_JSON"]

FIELDS = [
    "Company Name", "Summary", "CEO LinkedIn", "Investor(s)",
    "Date Closed", "Round Size", "Post-money", "ARR", "Other Notes",
]
PRIMARY_KEY = "Company Name"
SECTIONS = ["Seed", "Series A++", "Uncategorized"]


def fetch_records() -> list[dict]:
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    params = {"fields[]": FIELDS, "pageSize": 100}
    all_records = []
    offset = None
    while True:
        if offset:
            params["offset"] = offset
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for record in data.get("records", []):
            fields = record.get("fields", {})
            all_records.append({
                "_id": record["id"],
                **{f: str(fields.get(f, "")).strip() for f in FIELDS}
            })
        offset = data.get("offset")
        if not offset:
            break
    return all_records


def get_drive_service():
    creds_dict = json.loads(GDRIVE_CREDS_JSON)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def download_baseline(drive) -> list[dict]:
    try:
        request = drive.files().get_media(fileId=GDRIVE_FILE_ID)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)
        return json.loads(buf.read().decode("utf-8"))
    except Exception as e:
        print(f"⚠️  No baseline found: {e}")
        return []


def upload_baseline(drive, records: list[dict]):
    data = json.dumps(records, indent=2).encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/json", resumable=False)
    drive.files().update(fileId=GDRIVE_FILE_ID, media_body=media).execute()


def find_new_deals(current, baseline):
    seen_ids = {r["_id"] for r in baseline}
    seen_names = {r["Company Name"].lower().strip() for r in baseline if r.get("Company Name")}
    return [
        r for r in current
        if r["_id"] not in seen_ids
        and r.get("Company Name", "").lower().strip() not in seen_names
    ]


def classify(deal):
    notes = deal.get("Other Notes", "").strip()
    if not notes:
        return "Uncategorized"
    if "seed" in notes.lower():
        return "Seed"
    return "Series A++"


def run() -> tuple[dict, list[dict], object]:
    """
    Returns:
      grouped_deals: dict of Seed/Series A++/Uncategorized → list of deals
      current_records: full snapshot (for baseline update)
      drive: drive service (for baseline update after email drafts confirmed)
    """
    print("📥 Fetching Airtable records...")
    drive = get_drive_service()
    current = fetch_records()
    baseline = download_baseline(drive)
    new_deals = find_new_deals(current, baseline)
    print(f"🆕 Found {len(new_deals)} new deal(s)")

    grouped = {s: [] for s in SECTIONS}
    for deal in new_deals:
        grouped[classify(deal)].append(deal)

    return grouped, current, drive
