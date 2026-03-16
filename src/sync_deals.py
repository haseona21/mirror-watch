"""
weekly_deals_sync.py
--------------------
1. Fetches all records from Airtable via REST API
2. Loads last week's snapshot from Google Drive
3. Diffs to find new records (by Airtable record ID — never changes)
4. Classifies each deal by parsing Other Notes (Seed vs Series A++)
5. Creates a new Notion subpage under the Mirror parent page
6. Writes deals grouped by section, skipping blank fields, hiding internal IDs
7. Saves this week's full snapshot to Google Drive as the new baseline
"""

import os
import io
import json
import requests
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# ── ENV VARS (set in GitHub Secrets) ────────────────────────────────────────
AIRTABLE_TOKEN     = os.environ["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID   = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_ID  = os.environ["AIRTABLE_TABLE_ID"]
NOTION_API_KEY     = os.environ["NOTION_API_KEY"]
NOTION_PARENT_PAGE = os.environ["NOTION_PARENT_PAGE_ID"]
GDRIVE_FILE_ID     = os.environ["GDRIVE_FILE_ID"]
GDRIVE_CREDS_JSON  = os.environ["GDRIVE_CREDS_JSON"]

# ── FIELD CONFIG ─────────────────────────────────────────────────────────────
FIELDS = [
    "Company Name",
    "Summary",
    "CEO LinkedIn",
    "Investor(s)",
    "Date Closed",
    "Round Size",
    "Post-money",
    "ARR",
    "Other Notes",
]
PRIMARY_KEY = "Company Name"

# Section order in Notion output
SECTIONS = ["Seed", "Series A++", "Uncategorized"]


# ── AIRTABLE API ──────────────────────────────────────────────────────────────
def fetch_airtable_records() -> list[dict]:
    """Fetch all records from Airtable via REST API, handling pagination."""
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
                "_id": record["id"],  # internal only, never shown in Notion
                **{f: str(fields.get(f, "")).strip() for f in FIELDS}
            })

        offset = data.get("offset")
        if not offset:
            break

    print(f"📥 Fetched {len(all_records)} records from Airtable")
    return all_records


# ── GOOGLE DRIVE ─────────────────────────────────────────────────────────────
def get_drive_service():
    creds_dict = json.loads(GDRIVE_CREDS_JSON)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def download_baseline(drive) -> list[dict]:
    """Download last week's snapshot JSON from Google Drive."""
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
        print(f"⚠️  No baseline found or error downloading: {e}")
        return []


def upload_baseline(drive, records: list[dict]):
    """Overwrite the baseline JSON on Google Drive with this week's snapshot."""
    data = json.dumps(records, indent=2).encode("utf-8")
    media = MediaIoBaseUpload(
        io.BytesIO(data),
        mimetype="application/json",
        resumable=False
    )
    drive.files().update(fileId=GDRIVE_FILE_ID, media_body=media).execute()
    print("✅ Baseline updated on Google Drive")


# ── DIFF ──────────────────────────────────────────────────────────────────────
def find_new_deals(current: list[dict], baseline: list[dict]) -> list[dict]:
    """Return records in current whose Airtable record ID is not in the baseline."""
    seen_ids = {r["_id"] for r in baseline}
    new_deals = [r for r in current if r["_id"] not in seen_ids]
    print(f"🆕 Found {len(new_deals)} new deal(s)")
    return new_deals


# ── CLASSIFICATION ────────────────────────────────────────────────────────────
def classify_deal(deal: dict) -> str:
    """
    Classify a deal by parsing Other Notes.
    - Contains "seed" (case-insensitive) → Seed
    - Non-empty but no "seed" → Series A++
    - Empty → Uncategorized
    """
    notes = deal.get("Other Notes", "").strip()
    if not notes:
        return "Uncategorized"
    if "seed" in notes.lower():
        return "Seed"
    return "Series A++"


def classify_deals(deals: list[dict]) -> dict[str, list[dict]]:
    """Group deals into sections based on Other Notes content."""
    grouped: dict[str, list[dict]] = {s: [] for s in SECTIONS}
    for deal in deals:
        section = classify_deal(deal)
        grouped[section].append(deal)

    for section, items in grouped.items():
        if items:
            print(f"  {section}: {len(items)} deal(s)")

    return grouped


# ── NOTION ────────────────────────────────────────────────────────────────────
NOTION_VERSION = "2022-06-28"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


def create_weekly_subpage(week_label: str) -> str:
    """Create a new subpage under Mirror and return its page ID."""
    payload = {
        "parent": {"page_id": NOTION_PARENT_PAGE},
        "properties": {
            "title": {
                "title": [{"text": {"content": f"Dealflow – Week of {week_label}"}}]
            }
        },
        "children": []
    }
    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=15
    )
    resp.raise_for_status()
    page_id = resp.json()["id"]
    print(f"📄 Created Notion subpage: Dealflow – Week of {week_label}")
    return page_id


def make_text_block(label: str, value: str) -> dict | None:
    """Build a Notion paragraph block. Returns None if value is blank."""
    if not value or not value.strip():
        return None

    is_url = value.startswith("http://") or value.startswith("https://")

    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"{label}: "},
                    "annotations": {"bold": True}
                },
                {
                    "type": "text",
                    "text": {"content": value, **({"link": {"url": value}} if is_url else {})}
                }
            ]
        }
    }


def deal_to_blocks(deal: dict) -> list[dict]:
    """Convert a deal into Notion blocks. Skips blank fields. Never shows _id."""
    blocks = []

    # Company name as H3 (section headers use H2)
    blocks.append({
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": deal.get("Company Name", "Unknown")}}]
        }
    })

    # All fields except Company Name — skip if blank, never show _id
    for field in FIELDS:
        if field == PRIMARY_KEY:
            continue
        value = deal.get(field, "").strip()
        block = make_text_block(field, value)
        if block:
            blocks.append(block)

    blocks.append({"object": "block", "type": "divider", "divider": {}})

    return blocks


def section_header_block(title: str) -> dict:
    """Create an H2 block for a section header."""
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": title}}]
        }
    }


def append_blocks(page_id: str, blocks: list[dict]):
    """Append blocks to a Notion page in batches of 100 (API limit)."""
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i + 100]
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=NOTION_HEADERS,
            json={"children": batch},
            timeout=15
        )
        resp.raise_for_status()
    print(f"✅ Written {len(blocks)} blocks to Notion")


def write_to_notion(page_id: str, grouped: dict[str, list[dict]], total: int):
    """Write deals grouped by section. Empty sections are omitted entirely."""
    all_blocks = []

    # Intro summary
    all_blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": f"{total} new deal(s) added this week."},
                "annotations": {"italic": True}
            }]
        }
    })

    for section in SECTIONS:
        deals = grouped.get(section, [])
        if not deals:
            continue  # omit empty sections entirely

        all_blocks.append(section_header_block(section))
        for deal in deals:
            all_blocks.extend(deal_to_blocks(deal))

    append_blocks(page_id, all_blocks)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    today = datetime.now(timezone.utc)
    week_label = today.strftime("%b %d, %Y")

    print(f"\n🚀 Weekly deal sync — {week_label}\n")

    drive = get_drive_service()

    # 1. Fetch current state from Airtable
    current_records = fetch_airtable_records()

    # 2. Load last week's baseline from Drive
    baseline_records = download_baseline(drive)

    # 3. Diff — find truly new records
    new_deals = find_new_deals(current_records, baseline_records)

    if not new_deals:
        print("ℹ️  No new deals this week. Skipping Notion write.")
    else:
        # 4. Classify deals by parsing Other Notes
        print("🗂️  Classifying deals...")
        grouped = classify_deals(new_deals)

        # 5. Create Notion subpage
        page_id = create_weekly_subpage(week_label)

        # 6. Write grouped deals to Notion
        write_to_notion(page_id, grouped, len(new_deals))

    # 7. Always update baseline with full current snapshot
    upload_baseline(drive, current_records)

    print("\n✅ Sync complete.\n")


if __name__ == "__main__":
    main()
