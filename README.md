# Mirror – Weekly Dealflow Sync

Automated pipeline that tracks new venture deals from Airtable and publishes them weekly, plus a Claude Code skill for generating and sending dealshare emails.

---

## Part 1 — Weekly Sync (GitHub Actions)

Runs every Monday at 6:00 AM CT. Pulls new deals from Airtable, diffs against last week's snapshot, and writes a new subpage to Notion grouped by funding stage.

### How It Works

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

### Stack
- **GitHub Actions** — weekly CRON scheduler (free tier)
- **Python** — diff logic + API calls
- **Airtable REST API** — source of truth (read-only)
- **Google Drive** — stores the rolling JSON baseline between runs
- **Notion API** — writes formatted deal pages

### Notion Output Format

```
## Seed
Company Name
Summary: ...
CEO LinkedIn: [link]
Investor(s): ...
Date Closed: ...
Round Size: ...
Other Notes: ...

## Series A++
...

## Uncategorized
...
```

Sections with no deals are omitted. Fields with no value are omitted.

### Classification Logic
- Other Notes contains `"seed"` (case-insensitive) → **Seed**
- Has content but no `"seed"` → **Series A++**
- Empty → **Uncategorized**

### GitHub Secrets

| Secret | Value |
|--------|-------|
| `AIRTABLE_TOKEN` | Personal access token (scope: `data.records:read`) |
| `AIRTABLE_BASE_ID` | Base ID from Airtable URL |
| `AIRTABLE_TABLE_ID` | Table ID from Airtable URL |
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_PARENT_PAGE_ID` | ID of your parent page |
| `GDRIVE_FILE_ID` | ID of `baseline.json` on Drive |
| `GDRIVE_CREDS_JSON` | Full contents of service account JSON key |

### Schedule
Runs at 11:00 UTC (6:00 AM CST). During CDT (summer) this will be 7:00 AM CT.

### Running Manually
Go to **Actions → Weekly Deals Sync → Run workflow** to trigger at any time.

---

## Part 2 — Dealshare Skill (Claude Code)

A Claude Code skill that generates a weekly dealshare markdown file and sends it as Gmail drafts to your Dealshare list in Attio.

### How It Works

```
Run: claude dealshare (from the dealshare/ directory)
  → Fetches new Airtable deals (diff against Google Drive baseline)
  → Fetches calls logged this week from Attio via MCP
  → Generates a local markdown file and opens it for editing
  → After editing, updates the Google Drive baseline
  → Fetches Dealshare list from Attio (filtered to "Mae to Draft Email" = true)
  → Shows confirmation prompt with all recipients
  → Creates Gmail drafts for each recipient
```

### Markdown Output Format

```
# Dealshare – Week of [date]

**Folks we met:**
*Source*
Company Name
One-line description
LinkedIn URL
Raise details

**Deals we've heard about:**
Seed
  Company A - one liner

Series A++
  Company B - one liner
```

### Email Format

```
{First Name}, sharing folks we recently met and deals we recently heard about.

[optional: brief context from prior email thread]

[plain text content of the edited markdown]
```

### Skill Files

```
dealshare/
  CLAUDE.md                  ← Claude Code instructions
  dealshare.py               ← main entry point
  skills/
    fetch_airtable.py        ← pulls new deals + Google Drive baseline
    fetch_attio_calls.py     ← pulls this week's calls from Attio MCP
    generate_markdown.py     ← builds markdown file + opens for editing
    draft_emails.py          ← fetches Dealshare list + creates Gmail drafts
```

### MCP Tools Required
- **Attio MCP** — fetch calls and Dealshare people list
- **Gmail MCP** — search prior threads and create drafts

### Environment Variables

Set in your shell profile (`~/.zshrc`) or `.env`:

```bash
export AIRTABLE_TOKEN=
export AIRTABLE_BASE_ID=appoQFPWiFTtGuXPt
export AIRTABLE_TABLE_ID=tblnlIiRgC7duo2E4
export GDRIVE_FILE_ID=1rZXeTDqVmawaH9XRUa-ScnS6J9VtTdFp
export GDRIVE_CREDS_JSON='<full contents of service account JSON>'
```

### Setup (First Time)

```bash
# 1. Clone the repo
git clone https://github.com/haseona21/mirror-watch.git
cd mirror-watch/dealshare

# 2. Install dependencies
pip install -r ../requirements.txt

# 3. Set env vars (see above)

# 4. Run
claude dealshare
```
