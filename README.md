# Mirror – Weekly Dealflow Sync

Automated pipeline that tracks new venture deals from Airtable and publishes them weekly to Notion.

## How It Works

```
Every Monday @ 9am
  → Downloads current Airtable base (shared view CSV)
  → Compares against last week's snapshot (stored on Google Drive)
  → Identifies net-new deals only (ignores updates to existing records)
  → Creates a new "Dealflow – Week of [date]" subpage in Notion
  → Writes all new deals with structured formatting
  → Saves current snapshot as new baseline
```

## Stack

- **GitHub Actions** — weekly CRON scheduler (free tier)
- **Python** — diff logic + API calls
- **Google Drive** — stores the rolling CSV baseline between runs
- **Notion API** — writes formatted deal pages
- **Airtable** — source of truth (read-only via shared view CSV export)

## Notion Output Format

Each weekly subpage contains one section per deal:

```
## Company Name
Summary: ...
CEO LinkedIn: [link]
Investor(s): ...
Date Closed: ...
Round Size: ...
Post-money: ...
ARR: ...
Other Notes: ...
─────────────────
```

## Setup

### 1. Airtable — Get the CSV export URL
1. Open your Airtable base → switch to the view you want to export
2. Click **Share view** → enable **Allow CSV export** 
3. Copy the CSV download link — this is your `AIRTABLE_CSV_URL`

### 2. Google Drive — Create the baseline file
1. Create a blank `last_week.csv` file and upload it to Google Drive
2. Note the file ID from the URL: `drive.google.com/file/d/FILE_ID_HERE/...`
3. Create a [Google Service Account](https://console.cloud.google.com/iam-admin/serviceaccounts)
4. Download the service account JSON key
5. Share the CSV file with the service account email (Editor access)

### 3. Notion — Get your credentials
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → create a new integration
2. Copy the **Internal Integration Token** → this is your `NOTION_API_KEY`
3. Open your "Mirror" parent page in Notion → share it with your integration
4. Copy the page ID from the URL: `notion.so/PAGE_ID_HERE`

### 4. GitHub Secrets
In your repo → **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
|--------|-------|
| `AIRTABLE_CSV_URL` | Shared view CSV export URL |
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_PARENT_PAGE_ID` | ID of your "Mirror" page |
| `GDRIVE_FILE_ID` | ID of `last_week.csv` on Drive |
| `GDRIVE_CREDS_JSON` | Full contents of service account JSON key |

### 5. Adjust the schedule
Edit `.github/workflows/weekly_sync.yml` and change the cron expression if needed.
Current setting: **Every Monday at 9am Chicago time (CST)**.

## Running Manually
Go to **Actions → Weekly Deals Sync → Run workflow** to trigger a manual run at any time.
This is useful for testing before the first scheduled run.
