# Mirror – Weekly Dealflow Sync

Automated pipeline that pulls new venture deals from Airtable weekly and publishes them to Notion, grouped by funding stage.

## How It Works

```
Every Monday at 6:00 AM CT
  → Fetches all records from Airtable via REST API
  → Compares against last week's snapshot (stored on Google Drive)
  → Identifies net-new deals only (ignores updates to existing records)
  → Classifies each deal as Seed, Series A++, or Uncategorized
    based on the Other Notes field
  → Creates a new "Dealflow – Week of [date]" subpage in Notion
  → Writes new deals grouped by funding stage
  → Saves current snapshot as new baseline on Google Drive
```

## Stack

- **GitHub Actions** — weekly CRON scheduler (free tier)
- **Python** — diff logic + API calls
- **Airtable REST API** — source of truth (read-only)
- **Google Drive** — stores the rolling JSON baseline between runs
- **Notion API** — writes formatted deal pages

## Notion Output Format

Each weekly subpage contains deals grouped by funding stage:

```
## Seed
### Company Name
Summary: ...
CEO LinkedIn: [link]
Investor(s): ...
Date Closed: ...
Round Size: ...
Post-money: ...
ARR: ...
Other Notes: ...

## Series A++
### Company Name
...

## Uncategorized
### Company Name
...
```

Sections with no deals that week are omitted. Fields with no value are omitted.

## Classification Logic

Deals are classified by parsing the **Other Notes** field:
- Contains `"seed"` (case-insensitive) → **Seed**
- Has content but no `"seed"` → **Series A++**
- Empty → **Uncategorized**

## Setup

### 1. Airtable — Create a Personal Access Token
1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Create a token with scope: `data.records:read` only
3. Restrict access to your specific base
4. Copy the token → `AIRTABLE_TOKEN`
5. Get your Base ID and Table ID from the base URL:
   `https://airtable.com/{BASE_ID}/{TABLE_ID}/...`

### 2. Google Drive — Set up the baseline file
1. Create a file called `baseline.json` with content `[]`
2. Upload it to Google Drive, note the file ID from the URL
3. Go to [console.cloud.google.com](https://console.cloud.google.com)
4. Enable the **Google Drive API** on your project
5. Go to **IAM & Admin → Service Accounts → Create Service Account**
6. Under **Keys**, create a new JSON key and download it
7. Share `baseline.json` on Drive with the service account email (Editor access)

### 3. Notion — Create an integration
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration
2. Copy the integration token → `NOTION_API_KEY`
3. Open your parent page in Notion → **...** → **Connections** → connect your integration
4. Copy the page ID from the URL → `NOTION_PARENT_PAGE_ID`

### 4. GitHub Secrets
Go to repo **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `AIRTABLE_TOKEN` | Personal access token |
| `AIRTABLE_BASE_ID` | Base ID from Airtable URL |
| `AIRTABLE_TABLE_ID` | Table ID from Airtable URL |
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_PARENT_PAGE_ID` | ID of your parent page |
| `GDRIVE_FILE_ID` | ID of `baseline.json` on Drive |
| `GDRIVE_CREDS_JSON` | Full contents of service account JSON key |

## Running Manually
Go to **Actions → Weekly Deals Sync → Run workflow** to trigger a run at any time. Useful for testing.

## Notes
- The CRON runs at 11:00 UTC (6:00 AM CST). During CDT (summer), this will be 7:00 AM CT.
- Diffing is done by Airtable record ID — renaming a company won't cause it to appear as a new deal.
- The baseline JSON on Google Drive is overwritten every run with the full current snapshot.
